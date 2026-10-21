"""
Domain models for the Context Compiler subsystem.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ScoringWeights:
    """Configurable scoring weights for memory prioritization."""
    relevance_weight: float = 0.50
    constraint_boost: float = 0.15
    decision_boost: float = 0.10
    verbatim_boost: float = 0.10
    summary_boost: float = 0.05
    confidence_weight: float = 0.05
    recency_weight: float = 0.05


@dataclass(frozen=True)
class SelectedMemory:
    """Represents a memory unit selected for prompt context under budget."""
    memory_id: str
    content: str
    tier: str
    confidence: float
    token_count: int
    relevance_score: float
    priority_score: float
    selection_reason: str
    source_message_ids: List[str] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "tier": self.tier,
            "confidence": self.confidence,
            "token_count": self.token_count,
            "relevance_score": self.relevance_score,
            "priority_score": self.priority_score,
            "selection_reason": self.selection_reason,
            "source_message_ids": list(self.source_message_ids),
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class ExcludedMemory:
    """Represents a candidate memory excluded from context."""
    memory_id: str
    exclusion_reason: str
    relevance_score: float
    token_count: int
    content: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "exclusion_reason": self.exclusion_reason,
            "relevance_score": self.relevance_score,
            "token_count": self.token_count,
            "content": self.content,
        }


from manigit.core.tokens import estimate_tokens


@dataclass(frozen=True)
class ContextResult:
    """
    Final result of the deterministic context compilation process.
    """
    query: str
    selected_memories: List[SelectedMemory]
    excluded_memories: List[ExcludedMemory]
    total_tokens: int
    token_budget: int
    remaining_tokens: int
    commit_id: str
    branch: Optional[str] = None
    selection_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_prompt_context(self) -> str:
        """Format selected memories into clean, structured prompt context strictly obeying token_budget."""
        if not self.selected_memories:
            return ""
        lines = ["[Active Memory Context]"]
        for mem in self.selected_memories:
            prefix = f"[{mem.tier}]"
            candidate_line = f"{prefix} {mem.content}"
            if self.token_budget > 0:
                candidate_text = "\n".join(lines + [candidate_line])
                if estimate_tokens(candidate_text) > self.token_budget:
                    break
            lines.append(candidate_line)
        if len(lines) == 1:
            return ""
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "selected_memories": [m.to_dict() for m in self.selected_memories],
            "excluded_memories": [m.to_dict() for m in self.excluded_memories],
            "total_tokens": self.total_tokens,
            "token_budget": self.token_budget,
            "remaining_tokens": self.remaining_tokens,
            "commit_id": self.commit_id,
            "branch": self.branch,
            "selection_metadata": self.selection_metadata,
        }
