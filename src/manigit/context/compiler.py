"""
Context Compiler orchestrating deterministic query-specific memory selection under strict token budgets.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from manigit.context.budget import ContextBudget
from manigit.context.models import ContextResult, SelectedMemory
from manigit.context.retrieval import MemoryRetriever
from manigit.context.scoring import ScoringEngine
from manigit.core.exceptions import CommitNotFoundError
from manigit.core.repository import ManiGitRepository


class ContextCompiler:
    """
    Assembles query-specific, budgeted prompt context from versioned memory state.
    
    Guarantees:
    - Strictly READ-ONLY (never modifies messages, commits, branches, or memories).
    - Fully deterministic: identical query + state + budget = identical ContextResult.
    - Token budget is strictly respected (never exceeded).
    - Historical commit compilation without current HEAD state leakage.
    - Branch-aware context isolation.
    """

    def __init__(
        self,
        repo: ManiGitRepository,
        scoring_engine: Optional[ScoringEngine] = None,
        retriever: Optional[MemoryRetriever] = None,
    ):
        self.repo = repo
        self.scoring_engine = scoring_engine or ScoringEngine()
        self.retriever = retriever or MemoryRetriever(repo, self.scoring_engine)

    def compile(
        self,
        query: str,
        token_budget: int,
        branch: Optional[str] = None,
        commit_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> ContextResult:
        """
        Compile context for a user request under a token budget.
        """
        opts = options or {}
        target_branch: Optional[str] = None
        target_commit_id: Optional[str] = None

        # 1. Resolve target commit ID
        if commit_id is not None:
            # Historical commit mode
            # Validate commit exists
            self.repo.get_commit(commit_id)
            target_commit_id = commit_id
            target_branch = branch
        else:
            # Branch HEAD mode
            target_branch = branch or self.repo.active_branch
            branch_obj = self.repo.get_branch(target_branch)
            target_commit_id = branch_obj.head_commit_id

        if not target_commit_id:
            # Empty repository / branch
            return ContextResult(
                query=query,
                selected_memories=[],
                excluded_memories=[],
                total_tokens=0,
                token_budget=max(0, token_budget),
                remaining_tokens=max(0, token_budget),
                commit_id="",
                branch=target_branch,
                selection_metadata=opts,
            )

        # 2. Retrieve candidates and filter inactive/tombstone/duplicate records
        eligible, pre_excluded = self.retriever.retrieve_candidates(target_commit_id, query)

        # 3. Score and prioritize candidates
        query_has_terms = bool(self.scoring_engine.tokenize(query))
        ranked_candidates: List[SelectedMemory] = []

        for memory, relevance in eligible:
            priority, dominant_reason = self.scoring_engine.compute_priority(
                memory=memory,
                relevance_score=relevance,
                query_has_terms=query_has_terms,
            )

            ranked_candidates.append(
                SelectedMemory(
                    memory_id=memory.id,
                    content=memory.content,
                    tier=memory.tier,
                    confidence=memory.confidence,
                    token_count=memory.token_count,
                    relevance_score=relevance,
                    priority_score=priority,
                    selection_reason=dominant_reason,
                    source_message_ids=list(memory.source_message_ids),
                    created_at=memory.created_at,
                )
            )

        # Deterministic sorting: priority DESC, relevance DESC, confidence DESC, recency DESC, token_count ASC, id ASC
        def sort_key(item: SelectedMemory):
            timestamp_val = 0.0
            if item.created_at:
                try:
                    timestamp_val = datetime.fromisoformat(item.created_at).timestamp()
                except (ValueError, TypeError):
                    timestamp_val = 0.0
            return (
                -item.priority_score,
                -item.relevance_score,
                -item.confidence,
                -timestamp_val,
                item.token_count,
                item.memory_id,
            )

        ranked_candidates.sort(key=sort_key)

        # 4. Enforce Token Budget
        budget = ContextBudget(max_tokens=token_budget)

        # Register pre-excluded memories first (archived, tombstone, duplicate)
        for excl in pre_excluded:
            budget.excluded.append(excl)

        # Pack candidates greedily
        for candidate in ranked_candidates:
            budget.allocate(candidate)

        return ContextResult(
            query=query,
            selected_memories=budget.selected,
            excluded_memories=budget.excluded,
            total_tokens=budget.used_tokens,
            token_budget=budget.max_tokens,
            remaining_tokens=budget.remaining_tokens,
            commit_id=target_commit_id,
            branch=target_branch,
            selection_metadata={
                **opts,
                "candidate_count": len(ranked_candidates),
                "selected_count": len(budget.selected),
                "excluded_count": len(budget.excluded),
            },
        )
