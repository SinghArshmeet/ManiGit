"""
Dedicated Token Budget component for strict context window management.
"""

from typing import List, Set

from manigit.context.models import ExcludedMemory, SelectedMemory


class ContextBudget:
    """
    Manages and enforces token budgets during context compilation.
    
    Guarantees:
    - Total tokens of selected memories NEVER exceed max_tokens.
    - Handles exact boundaries, zero budget, and greedy token-budget selection.
    """

    def __init__(self, max_tokens: int):
        self.max_tokens = max(0, int(max_tokens))
        self.used_tokens = 0
        self.selected: List[SelectedMemory] = []
        self.excluded: List[ExcludedMemory] = []
        self._selected_ids: Set[str] = set()

    @property
    def remaining_tokens(self) -> int:
        return max(0, self.max_tokens - self.used_tokens)

    def can_fit(self, token_count: int) -> bool:
        """Check if a memory of token_count fits within remaining budget."""
        return token_count <= self.remaining_tokens

    def allocate(self, memory: SelectedMemory) -> bool:
        """
        Attempt to allocate budget for a candidate memory.
        
        Returns True if allocated, False if rejected.
        """
        if memory.memory_id in self._selected_ids:
            self.excluded.append(
                ExcludedMemory(
                    memory_id=memory.memory_id,
                    content=memory.content,
                    exclusion_reason="duplicate",
                    relevance_score=memory.relevance_score,
                    token_count=memory.token_count,
                )
            )
            return False

        if self.can_fit(memory.token_count):
            self.selected.append(memory)
            self._selected_ids.add(memory.memory_id)
            self.used_tokens += memory.token_count
            return True
        else:
            self.excluded.append(
                ExcludedMemory(
                    memory_id=memory.memory_id,
                    content=memory.content,
                    exclusion_reason=f"outside budget (requires {memory.token_count} tokens, remaining: {self.remaining_tokens})",
                    relevance_score=memory.relevance_score,
                    token_count=memory.token_count,
                )
            )
            return False

    def reject(
        self,
        memory_id: str,
        reason: str,
        relevance_score: float = 0.0,
        token_count: int = 0,
        content: str = "",
    ) -> None:
        """Record an explicit exclusion."""
        self.excluded.append(
            ExcludedMemory(
                memory_id=memory_id,
                content=content,
                exclusion_reason=reason,
                relevance_score=relevance_score,
                token_count=token_count,
            )
        )
