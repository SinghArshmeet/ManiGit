"""
Data models for the ManiGit Agent Runtime subsystem.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from manigit.context.models import ContextResult
from manigit.memory.service import MemoryProcessingResult
from manigit.memory.why import WhyReport


@dataclass(frozen=True)
class AgentConfig:
    """Configuration options for the AgentRuntime."""
    default_token_budget: int = 2048
    system_prompt: Optional[str] = "You are an intelligent AI assistant equipped with ManiGit versioned memory."
    default_session_id: str = "default_session"
    author: str = "agent:auto"
    process_user_memory: bool = True


@dataclass(frozen=True)
class TokenUsage:
    """Token statistics for an agent turn."""
    context_tokens: int
    user_message_tokens: int
    estimated_input_tokens: int
    output_tokens: int
    total_tokens: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_tokens": self.context_tokens,
            "user_message_tokens": self.user_message_tokens,
            "estimated_input_tokens": self.estimated_input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass(frozen=True)
class AgentTurn:
    """
    Structured, auditable record of a completed agent interaction turn.
    """
    turn_id: str
    session_id: str
    user_message_id: str
    assistant_message_id: str
    commit_id: Optional[str]
    branch: str
    user_message: str
    assistant_response: str
    context_result: ContextResult
    token_usage: TokenUsage
    memory_result: Optional[MemoryProcessingResult] = None
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "session_id": self.session_id,
            "user_message_id": self.user_message_id,
            "assistant_message_id": self.assistant_message_id,
            "commit_id": self.commit_id,
            "branch": self.branch,
            "user_message": self.user_message,
            "assistant_response": self.assistant_response,
            "context_result": self.context_result.to_dict(),
            "token_usage": self.token_usage.to_dict(),
            "memory_result": {
                "decision": self.memory_result.why_report.decision,
                "tier": self.memory_result.classification.tier,
                "reason": self.memory_result.why_report.reason,
                "new_memory_id": self.memory_result.new_memory.id if self.memory_result.new_memory else None,
                "superseded_memory_id": self.memory_result.superseded_memory_id,
                "has_contradiction": self.memory_result.contradiction.has_contradiction,
            } if self.memory_result else None,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class AgentResponse:
    """
    Top-level response returned to the caller of agent.run().
    
    Provides direct access to generated content while retaining full
    underlying turn auditability (commit ID, token usage, context, why report).
    """
    content: str
    turn: AgentTurn

    @property
    def turn_id(self) -> str:
        return self.turn.turn_id

    @property
    def session_id(self) -> str:
        return self.turn.session_id

    @property
    def user_message_id(self) -> str:
        return self.turn.user_message_id

    @property
    def assistant_message_id(self) -> str:
        return self.turn.assistant_message_id

    @property
    def commit_id(self) -> Optional[str]:
        return self.turn.commit_id

    @property
    def branch(self) -> str:
        return self.turn.branch

    @property
    def token_usage(self) -> TokenUsage:
        return self.turn.token_usage

    @property
    def context_result(self) -> ContextResult:
        return self.turn.context_result

    @property
    def memory_result(self) -> Optional[MemoryProcessingResult]:
        return self.turn.memory_result

    @property
    def why_report(self) -> Optional[WhyReport]:
        return self.turn.memory_result.why_report if self.turn.memory_result else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "turn": self.turn.to_dict(),
        }
