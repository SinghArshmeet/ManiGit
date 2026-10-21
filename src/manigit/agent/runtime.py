"""
Agent Runtime implementation for ManiGit.

Coordinates the multi-turn agent execution loop:
User Message -> Raw Storage -> Context Compilation -> Model Adapter -> Assistant Storage -> Memory Intelligence -> Commit.
"""

from typing import Any, Dict, List, Optional
import uuid

from manigit.agent.exceptions import (
    ContextCompilationError,
    EmptyMessageError,
    InvalidBranchError,
    ModelAdapterError,
)
from manigit.agent.models import AgentConfig, AgentResponse, AgentTurn, TokenUsage
from manigit.context.compiler import ContextCompiler
from manigit.context.models import ContextResult
from manigit.core.exceptions import BranchNotFoundError
from manigit.core.models import Memory, Message, MessageRole, utc_now_iso
from manigit.core.repository import ManiGitRepository
from manigit.memory.service import MemoryProcessingResult, MemoryService
from manigit.models.base import ModelAdapter


class AgentRuntime:
    """
    Orchestrates long-running multi-turn AI agent execution across versioned memory.
    
    Guarantees:
    - Raw messages are permanently archived and immutable.
    - Context is dynamically compiled within a strict token budget using Phase 3 ContextCompiler.
    - Model interactions are provider-agnostic via ModelAdapter.
    - Meaningful memory transitions are recorded as versioned commits with Why Reports.
    - Historical states remain 100% reconstructable without head leakage.
    - The active repository branch is never switched silently.
    """

    def __init__(
        self,
        repository: ManiGitRepository,
        model: ModelAdapter,
        memory_service: Optional[MemoryService] = None,
        context_compiler: Optional[ContextCompiler] = None,
        config: Optional[AgentConfig] = None,
    ):
        self.repository = repository
        self.model = model
        self.memory_service = memory_service or MemoryService(repository, model)
        self.context_compiler = context_compiler or ContextCompiler(repository)
        self.config = config or AgentConfig()

    def run(
        self,
        user_message: str,
        session_id: Optional[str] = None,
        branch: Optional[str] = None,
        token_budget: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> AgentResponse:
        """
        Execute a complete agent interaction turn.
        
        Args:
            user_message: The raw textual prompt from the user.
            session_id: Optional session identifier (defaults to configured session).
            branch: Optional target branch (defaults to repository's active branch).
            token_budget: Optional token ceiling for context compilation.
            system_prompt: Optional override for system instructions.
            
        Returns:
            AgentResponse: Auditable response including text, turn metadata, context, and why report.
        """
        # Step 1: Input validation
        if not user_message or not user_message.strip():
            raise EmptyMessageError("User message cannot be empty or whitespace.")

        target_session = session_id or self.config.default_session_id
        target_branch = branch or self.repository.active_branch

        # Step 2: Validate branch existence without mutating active branch
        try:
            branch_obj = self.repository.get_branch(target_branch)
        except BranchNotFoundError as e:
            raise InvalidBranchError(f"Branch '{target_branch}' does not exist.") from e

        turn_id = f"turn_{uuid.uuid4().hex[:12]}"
        now_iso = utc_now_iso()

        # Step 3: Persist raw user message (immutable archive)
        user_msg = self.repository.append_message(
            session_id=target_session,
            role=MessageRole.USER,
            content=user_message,
            metadata={"turn_id": turn_id},
        )

        # Step 4: Compile context via ContextCompiler (strictly read-only)
        budget = token_budget if token_budget is not None else self.config.default_token_budget
        try:
            context_result = self.context_compiler.compile(
                query=user_message,
                token_budget=budget,
                branch=target_branch,
            )
        except Exception as e:
            raise ContextCompilationError(f"Failed to compile context: {e}") from e

        # Step 5: Construct model input distinguishing instructions, context, and prompt
        sys_instructions = system_prompt if system_prompt is not None else self.config.system_prompt
        prompt_sections: List[str] = []
        if sys_instructions and sys_instructions.strip():
            prompt_sections.append(f"[System Instructions]\n{sys_instructions.strip()}")

        active_context = context_result.to_prompt_context()
        if active_context:
            prompt_sections.append(active_context)

        prompt_sections.append(f"[User Message]\n{user_message.strip()}")
        model_input = "\n\n".join(prompt_sections)

        # Step 6: Invoke ModelAdapter
        try:
            raw_response = self.model.generate(model_input)
        except Exception as e:
            # Model failed after raw user message was preserved.
            # Do NOT create a false assistant response or misleading memory commit.
            raise ModelAdapterError(f"Model generation failed: {e}") from e

        # Step 7: Persist raw assistant message
        assistant_msg = self.repository.append_message(
            session_id=target_session,
            role=MessageRole.ASSISTANT,
            content=raw_response,
            metadata={"turn_id": turn_id, "user_message_id": user_msg.id},
        )

        # Step 8: Run Memory Intelligence pipeline
        mem_result: Optional[MemoryProcessingResult] = None
        active_commit_id = branch_obj.head_commit_id

        if self.config.process_user_memory:
            mem_result = self.memory_service.process_message(
                message=user_msg,
                branch_name=target_branch,
            )

            # Step 9: Commit memory state update if a meaningful mutation occurred
            state_changed = (
                mem_result.new_memory is not None
                or mem_result.superseded_memory_id is not None
            )

            if state_changed:
                if mem_result.contradiction.has_contradiction:
                    commit_msg = f"Superseded memory: {mem_result.why_report.reason}"
                elif mem_result.new_memory:
                    commit_msg = f"Learned ({mem_result.classification.tier}): {mem_result.why_report.reason}"
                else:
                    commit_msg = f"Memory update: {mem_result.why_report.reason}"

                new_commit = self.memory_service.commit_memory_update(
                    result=mem_result,
                    commit_message=commit_msg,
                    branch_name=target_branch,
                    author=self.config.author,
                )
                active_commit_id = new_commit.id

        # Step 10: Token accounting & assemble AgentResponse
        user_tokens = user_msg.token_count
        context_tokens = context_result.total_tokens
        estimated_input = self.model.count_tokens(model_input)
        output_tokens = assistant_msg.token_count
        total_tokens = estimated_input + output_tokens

        token_usage = TokenUsage(
            context_tokens=context_tokens,
            user_message_tokens=user_tokens,
            estimated_input_tokens=estimated_input,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )

        turn = AgentTurn(
            turn_id=turn_id,
            session_id=target_session,
            user_message_id=user_msg.id,
            assistant_message_id=assistant_msg.id,
            commit_id=active_commit_id,
            branch=target_branch,
            user_message=user_message,
            assistant_response=raw_response,
            context_result=context_result,
            token_usage=token_usage,
            memory_result=mem_result,
            created_at=now_iso,
        )

        return AgentResponse(content=raw_response, turn=turn)

    def compile_context(
        self,
        query: str,
        token_budget: Optional[int] = None,
        branch: Optional[str] = None,
        commit_id: Optional[str] = None,
    ) -> ContextResult:
        """Direct context compilation helper for inspection or tool access."""
        budget = token_budget if token_budget is not None else self.config.default_token_budget
        return self.context_compiler.compile(
            query=query,
            token_budget=budget,
            branch=branch or self.repository.active_branch,
            commit_id=commit_id,
        )

    def reconstruct_state(
        self,
        commit_id: Optional[str] = None,
        branch: Optional[str] = None,
    ) -> List[Memory]:
        """Reconstruct active memory state at a branch HEAD or historical commit."""
        if commit_id:
            return self.repository.reconstruct_memory_state(commit_id)
        target_branch = branch or self.repository.active_branch
        head = self.repository.get_current_head(target_branch)
        if not head:
            return []
        return self.repository.reconstruct_memory_state(head.id)

    def get_history(self, session_id: Optional[str] = None) -> List[Message]:
        """Retrieve raw conversation history from the immutable archive."""
        target_session = session_id or self.config.default_session_id
        return self.repository.get_messages(session_id=target_session)
