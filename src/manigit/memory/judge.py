"""
Semantic Memory Judge for evaluating conversation items against active memory.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from manigit.core.models import MemoryTier
from manigit.models.base import ModelAdapter


@dataclass(frozen=True)
class JudgmentResult:
    """Structured result returned by the MemoryJudge."""
    tier: str
    confidence: float
    reason: str
    importance: str  # "high", "medium", "low"
    needs_summary: bool
    source_message_ids: List[str] = field(default_factory=list)
    extracted_fact: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tier": self.tier,
            "confidence": self.confidence,
            "reason": self.reason,
            "importance": self.importance,
            "needs_summary": self.needs_summary,
            "source_message_ids": list(self.source_message_ids),
            "extracted_fact": self.extracted_fact,
        }


class MemoryJudge:
    """
    Evaluates conversation turns using a model adapter to produce structured memory judgments.
    """

    def __init__(self, model_adapter: ModelAdapter):
        self.model_adapter = model_adapter

    def judge(
        self,
        message_content: str,
        source_message_ids: List[str],
        active_memories: Optional[List[Dict[str, Any]]] = None,
    ) -> JudgmentResult:
        """
        Produce a structured judgment evaluating tier, confidence, importance, and summary need.
        """
        raw_judgment = self.model_adapter.judge_memory(
            message_content=message_content,
            active_memories=active_memories,
        )

        tier_raw = str(raw_judgment.get("tier", "VERBATIM")).upper()
        if tier_raw not in (MemoryTier.VERBATIM.value, MemoryTier.SUMMARY.value, MemoryTier.ARCHIVED.value):
            tier_raw = MemoryTier.VERBATIM.value

        try:
            confidence = float(raw_judgment.get("confidence", 0.65))
            confidence = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            confidence = 0.65

        reason = str(raw_judgment.get("reason", "Evaluated by semantic memory judge."))
        importance = str(raw_judgment.get("importance", "medium")).lower()
        if importance not in ("high", "medium", "low"):
            importance = "medium"

        needs_summary = bool(raw_judgment.get("needs_summary", tier_raw == MemoryTier.SUMMARY.value))
        extracted_fact = raw_judgment.get("extracted_fact")
        if extracted_fact is not None:
            extracted_fact = str(extracted_fact).strip()

        return JudgmentResult(
            tier=tier_raw,
            confidence=confidence,
            reason=reason,
            importance=importance,
            needs_summary=needs_summary,
            source_message_ids=list(source_message_ids),
            extracted_fact=extracted_fact,
        )
