"""
Backend service layer for the ManiGit research web interface.

Wraps existing Phase 1–5 services without bypassing repository abstractions:
- ManiGitRepository
- AgentRuntime
- ContextCompiler
- MemoryService
- BenchmarkResultStorage / BenchmarkReportGenerator
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from manigit.agent.runtime import AgentRuntime
from manigit.context.compiler import ContextCompiler
from manigit.context.models import ContextResult
from manigit.core.exceptions import BranchNotFoundError, CommitNotFoundError
from manigit.core.models import MemoryStatus, utc_now_iso
from manigit.core.repository import ManiGitRepository
from manigit.evaluation.reporting import BenchmarkReportGenerator
from manigit.evaluation.storage import BenchmarkResultStorage
from manigit.memory.service import MemoryService
from manigit.models.mock import MockModelAdapter
from web.backend.models import (
    BenchmarkSummary,
    BranchSummary,
    ChatRequest,
    ChatResponse,
    CommitDetail,
    CommitSummary,
    ContextPreviewRequest,
    ContextPreviewResponse,
    ExcludedMemoryItem,
    MemoryDetail,
    MemorySummary,
    SelectedMemoryItem,
    WhyReportResponse,
)


class ManiGitWebService:
    """
    Coordinates web API operations across ManiGit's versioned memory services.
    Enforces that the web layer NEVER directly manipulates SQLite tables.
    """

    def __init__(
        self,
        repository: Optional[ManiGitRepository] = None,
        runtime: Optional[AgentRuntime] = None,
        benchmark_storage: Optional[BenchmarkResultStorage] = None,
    ):
        if repository is None:
            self.repository = ManiGitRepository("data/database/manigit.db")
            self.repository.initialize_repository()
        else:
            self.repository = repository

        self.model = MockModelAdapter()
        self.compiler = ContextCompiler(self.repository)
        self.memory_service = MemoryService(self.repository, self.model)
        self.runtime = runtime or AgentRuntime(
            repository=self.repository,
            model=self.model,
            memory_service=self.memory_service,
            context_compiler=self.compiler,
        )
        self.benchmark_storage = benchmark_storage or BenchmarkResultStorage()

    def get_health(self) -> Dict[str, Any]:
        """System health and active repository status."""
        active_branch = self.repository.active_branch
        head = self.repository.get_current_head(active_branch)
        return {
            "status": "healthy",
            "active_branch": active_branch,
            "head_commit_id": head.id if head else None,
            "timestamp": utc_now_iso(),
        }

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Processes a user prompt through AgentRuntime and returns the response."""
        response = self.runtime.run(
            user_message=request.message,
            session_id=request.session_id or "web_session",
            branch=request.branch or self.repository.active_branch,
            token_budget=request.token_budget or 1024,
        )

        turn = response.turn
        why_reason = None
        if turn.memory_result and turn.memory_result.why_report:
            why_reason = turn.memory_result.why_report.reason

        return ChatResponse(
            content=response.content,
            turn_id=turn.turn_id,
            session_id=turn.session_id,
            branch=turn.branch,
            commit_id=turn.commit_id,
            user_message_id=turn.user_message_id,
            assistant_message_id=turn.assistant_message_id,
            context_tokens=turn.token_usage.context_tokens,
            total_tokens=turn.token_usage.total_tokens,
            why_reason=why_reason,
            created_at=turn.created_at,
        )

    def list_commits(self, branch: Optional[str] = None, limit: int = 50) -> List[CommitSummary]:
        """Retrieves commit DAG timeline for a branch or all branches."""
        target_branch = branch or self.repository.active_branch
        history = self.repository.get_commit_history(target_branch)
        
        summaries: List[CommitSummary] = []
        for c in history[:limit]:
            # Count memories associated with commit
            commit_mems = self.repository.reconstruct_memory_state(c.id)
            total_tokens = sum(m.token_count for m in commit_mems)
            summaries.append(
                CommitSummary(
                    id=c.id,
                    short_id=c.id[:7],
                    message=c.message,
                    author=c.author,
                    parent_commit_id=c.parent_commit_id,
                    branch_name=c.branch,
                    memory_count=len(commit_mems),
                    total_tokens=total_tokens,
                    created_at=c.timestamp,
                )
            )
        return summaries

    def get_commit(self, commit_id: str) -> Optional[CommitDetail]:
        """Retrieves complete details for a specific commit."""
        try:
            c = self.repository.get_commit(commit_id)
        except CommitNotFoundError:
            return None

        commit_mems = self.repository.reconstruct_memory_state(c.id)
        total_tokens = sum(m.token_count for m in commit_mems)
        return CommitDetail(
            id=c.id,
            short_id=c.id[:7],
            message=c.message,
            author=c.author,
            parent_commit_id=c.parent_commit_id,
            branch_name=c.branch,
            memory_ids=[m.id for m in commit_mems],
            memory_count=len(commit_mems),
            total_tokens=total_tokens,
            created_at=c.timestamp,
            metadata=c.metadata,
        )

    def list_branches(self) -> List[BranchSummary]:
        """Returns all branches in the repository."""
        branches = self.repository.list_branches()
        active = self.repository.active_branch
        return [
            BranchSummary(
                name=b.name,
                head_commit_id=b.head_commit_id,
                is_active=(b.name == active),
                created_at=b.created_at,
                updated_at=b.updated_at,
            )
            for b in branches
        ]

    def create_branch(self, name: str, from_commit_id: Optional[str] = None) -> BranchSummary:
        """Creates a new branch pointer from a commit or active HEAD."""
        b = self.repository.create_branch(name, source_commit_id=from_commit_id)
        return BranchSummary(
            name=b.name,
            head_commit_id=b.head_commit_id,
            is_active=(b.name == self.repository.active_branch),
            created_at=b.created_at,
            updated_at=b.updated_at,
        )

    def switch_branch(self, branch_name: str) -> BranchSummary:
        """Switches the active branch pointer."""
        b = self.repository.switch_branch(branch_name)
        return BranchSummary(
            name=b.name,
            head_commit_id=b.head_commit_id,
            is_active=True,
            created_at=b.created_at,
            updated_at=b.updated_at,
        )

    def get_active_memories(self, branch: Optional[str] = None) -> List[MemorySummary]:
        """Returns active memories at HEAD of a branch."""
        target_branch = branch or self.repository.active_branch
        head = self.repository.get_current_head(target_branch)
        if not head:
            return []
        mems = self.repository.reconstruct_memory_state(head.id)
        return [
            MemorySummary(
                id=m.id,
                tier=m.tier.value if hasattr(m.tier, "value") else str(m.tier),
                status=m.status.value if hasattr(m.status, "value") else str(m.status),
                content=m.content,
                confidence=m.confidence,
                token_count=m.token_count,
                source_message_ids=m.source_message_ids,
                metadata=m.metadata,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in mems
        ]

    def get_commit_memories(self, commit_id: str) -> List[MemorySummary]:
        """
        Reconstructs memory state at an older commit in the DAG.
        GUARANTEED READ-ONLY: Never switches branches or mutates active HEAD.
        """
        mems = self.repository.reconstruct_memory_state(commit_id)
        return [
            MemorySummary(
                id=m.id,
                tier=m.tier.value if hasattr(m.tier, "value") else str(m.tier),
                status=m.status.value if hasattr(m.status, "value") else str(m.status),
                content=m.content,
                confidence=m.confidence,
                token_count=m.token_count,
                source_message_ids=m.source_message_ids,
                metadata=m.metadata,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in mems
        ]

    def get_commit_why_report(self, commit_id: str) -> Optional[WhyReportResponse]:
        """Retrieves recorded why report for a commit from commit metadata."""
        try:
            commit = self.repository.get_commit(commit_id)
        except CommitNotFoundError:
            return None

        report_dict = commit.metadata.get("why_report")
        if not report_dict:
            return None

        contra_info = report_dict.get("contradiction_info")
        contra_detected = (contra_info is not None) or (report_dict.get("decision") == "SUPERSEDE")
        superseded_id = report_dict.get("predecessor_memory_id")

        tokens_before = report_dict.get("tokens_before", 0)
        tokens_after = report_dict.get("tokens_after", 0)
        tokens_saved = max(0, tokens_before - tokens_after)

        return WhyReportResponse(
            commit_id=commit.id,
            operation=report_dict.get("decision", "RECORD"),
            tier=str(report_dict.get("tier", "VERBATIM")),
            confidence=float(report_dict.get("confidence", 1.0)),
            reason=report_dict.get("reason", commit.reason),
            matched_rules=report_dict.get("matched_rules", []),
            source_message_ids=report_dict.get("source_message_ids", []),
            predecessor_memory_id=report_dict.get("predecessor_memory_id"),
            contradiction_detected=contra_detected,
            superseded_memory_id=superseded_id,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            tokens_saved=tokens_saved,
        )

    def get_memory_detail(self, memory_id: str) -> Optional[MemoryDetail]:
        """Retrieves full memory detail including provenance source messages."""
        mem = self.repository.get_memory(memory_id)
        if not mem:
            return None
        
        # Load source messages for full provenance audit
        sources: List[Dict[str, Any]] = []
        for msg_id in mem.source_message_ids:
            try:
                msg = self.repository.get_message(msg_id)
                if msg:
                    sources.append({
                        "id": msg.id,
                        "session_id": msg.session_id,
                        "role": msg.role.value if hasattr(msg.role, "value") else str(msg.role),
                        "content": msg.content,
                        "created_at": msg.created_at,
                    })
            except Exception:
                pass

        return MemoryDetail(
            id=mem.id,
            tier=mem.tier.value if hasattr(mem.tier, "value") else str(mem.tier),
            status=mem.status.value if hasattr(mem.status, "value") else str(mem.status),
            content=mem.content,
            confidence=mem.confidence,
            token_count=mem.token_count,
            source_message_ids=mem.source_message_ids,
            source_messages=sources,
            metadata=mem.metadata,
            created_at=mem.created_at,
            updated_at=mem.updated_at,
        )

    def preview_context(self, request: ContextPreviewRequest) -> ContextPreviewResponse:
        """Compiles budgeted prompt context and exposes full diagnostics."""
        result: ContextResult = self.compiler.compile(
            query=request.query,
            token_budget=request.token_budget or 1024,
            branch=request.branch or self.repository.active_branch,
            commit_id=request.commit_id,
        )

        selected = [
            SelectedMemoryItem(
                memory_id=m.memory_id,
                content=m.content,
                tier=m.tier,
                confidence=m.confidence,
                token_count=m.token_count,
                relevance_score=m.relevance_score,
                priority_score=m.priority_score,
                selection_reason=m.selection_reason,
                source_message_ids=m.source_message_ids,
            )
            for m in result.selected_memories
        ]

        excluded = [
            ExcludedMemoryItem(
                memory_id=m.memory_id,
                content=m.content,
                token_count=m.token_count,
                relevance_score=m.relevance_score,
                exclusion_reason=m.exclusion_reason,
            )
            for m in result.excluded_memories
        ]

        return ContextPreviewResponse(
            query=result.query,
            token_budget=result.token_budget,
            total_tokens=result.total_tokens,
            remaining_tokens=result.remaining_tokens,
            commit_id=result.commit_id,
            branch=result.branch,
            selected_memories=selected,
            excluded_memories=excluded,
            formatted_context=result.to_prompt_context(),
        )

    def get_benchmark_summary(self, run_id: Optional[str] = "exp_canonical_run_001") -> Optional[BenchmarkSummary]:
        """Provides high-level empirical benchmark results for the dashboard."""
        target_run = run_id or "exp_canonical_run_001"
        results = self.benchmark_storage.load_run(target_run)
        if not results:
            return None

        generator = BenchmarkReportGenerator(results)
        method_metrics = generator.generate_method_aggregates()

        # Build budget-specific metrics and budget vs recall table
        budgets = sorted(list(set(r.budget for r in results)))
        methods = sorted(list(set(r.method for r in results)))

        budget_metrics: Dict[str, Dict[str, Dict[str, Any]]] = {}
        budget_vs_recall: Dict[str, Dict[str, float]] = {}
        for b in budgets:
            budget_metrics[str(b)] = generator.generate_method_aggregates(budget=b)
            budget_vs_recall[str(b)] = {}
            for m in methods:
                sub = [r for r in results if r.budget == b and r.method == m]
                rec = (sum(1 for r in sub if r.metrics.fact_recall) / len(sub)) if sub else 0.0
                budget_vs_recall[str(b)][m] = round(rec, 4)

        return BenchmarkSummary(
            run_id=target_run,
            total_trials=len(results),
            scenarios_evaluated=len(set(r.scenario_id for r in results)),
            methods=methods,
            budgets=budgets,
            method_metrics=method_metrics,
            budget_metrics=budget_metrics,
            budget_vs_recall=budget_vs_recall,
            timestamp=results[0].timestamp if results else utc_now_iso(),
        )
