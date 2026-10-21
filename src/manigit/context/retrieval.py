"""
Deterministic local memory retrieval from reconstructed active repository state.
"""

from typing import List, Optional, Set, Tuple

from manigit.context.models import ExcludedMemory
from manigit.context.scoring import ScoringEngine
from manigit.core.models import Memory, MemoryStatus, MemoryTier
from manigit.core.repository import ManiGitRepository


class MemoryRetriever:
    """
    Retrieves and filters candidate memories from the active repository state.
    
    Guarantees:
    - Strictly READ-ONLY.
    - Operates on the authoritative reconstructed state via reconstruct_memory_state().
    - Excludes ARCHIVED and TOMBSTONE records from active context.
    - Filters duplicates.
    """

    def __init__(self, repo: ManiGitRepository, scoring_engine: Optional[ScoringEngine] = None):
        self.repo = repo
        self.scoring_engine = scoring_engine or ScoringEngine()

    def retrieve_candidates(
        self,
        commit_id: str,
        query: str,
    ) -> Tuple[List[Tuple[Memory, float]], List[ExcludedMemory]]:
        """
        Reconstruct active state at commit_id, filter active memories, and compute relevance.
        
        Returns:
            (eligible_candidates, pre_excluded_memories)
        """
        raw_state: List[Memory] = self.repo.reconstruct_memory_state(commit_id)

        eligible: List[Tuple[Memory, float]] = []
        excluded: List[ExcludedMemory] = []
        seen_contents: Set[str] = set()

        for mem in raw_state:
            # 1. Check status
            if mem.status == MemoryStatus.TOMBSTONE.value:
                excluded.append(
                    ExcludedMemory(
                        memory_id=mem.id,
                        content=mem.content,
                        exclusion_reason="tombstone",
                        relevance_score=0.0,
                        token_count=mem.token_count,
                    )
                )
                continue

            # 2. Check tier
            if mem.tier in (MemoryTier.ARCHIVED.value, MemoryTier.TOMBSTONE.value):
                excluded.append(
                    ExcludedMemory(
                        memory_id=mem.id,
                        content=mem.content,
                        exclusion_reason="archived",
                        relevance_score=0.0,
                        token_count=mem.token_count,
                    )
                )
                continue

            # 3. Check for duplicates in active set
            norm_content = mem.content.strip().lower()
            if norm_content in seen_contents:
                excluded.append(
                    ExcludedMemory(
                        memory_id=mem.id,
                        content=mem.content,
                        exclusion_reason="duplicate",
                        relevance_score=0.0,
                        token_count=mem.token_count,
                    )
                )
                continue

            seen_contents.add(norm_content)

            # 4. Compute relevance
            relevance = self.scoring_engine.compute_relevance(query, mem.content)
            eligible.append((mem, relevance))

        return eligible, excluded
