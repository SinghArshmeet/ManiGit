"""
Hybrid Memory Classifier combining deterministic rule signals with semantic LLM judging.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from manigit.core.models import Memory, MemoryTier
from manigit.memory.judge import JudgmentResult, MemoryJudge
from manigit.memory.rules import RuleEngine, RuleSignal


@dataclass(frozen=True)
class ClassificationResult:
    """Final decision output of the hybrid classification pipeline."""
    tier: str                              # "VERBATIM", "SUMMARY", "ARCHIVED"
    confidence: float                      # 0.0 to 1.0
    decision: str                          # "KEEP_VERBATIM", "SUMMARIZE", "ARCHIVE"
    reason: str
    matched_rules: List[str] = field(default_factory=list)
    source_message_ids: List[str] = field(default_factory=list)
    content_to_store: str = ""
    used_llm_judge: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tier": self.tier,
            "confidence": self.confidence,
            "decision": self.decision,
            "reason": self.reason,
            "matched_rules": list(self.matched_rules),
            "source_message_ids": list(self.source_message_ids),
            "content_to_store": self.content_to_store,
            "used_llm_judge": self.used_llm_judge,
        }


class MemoryClassifier:
    """
    Coordinates the hybrid decision pipeline:
    Rule Engine (fast, deterministic) -> LLM Judge (semantic, ambiguous fallback).
    """

    # Conservative threshold: Archiving requires at least 0.75 confidence.
    ARCHIVE_CONFIDENCE_THRESHOLD = 0.75

    def __init__(self, rule_engine: RuleEngine, judge: MemoryJudge):
        self.rule_engine = rule_engine
        self.judge = judge

    def classify(
        self,
        content: str,
        source_message_ids: List[str],
        active_memories: Optional[List[Memory]] = None,
    ) -> ClassificationResult:
        """
        Classify a conversational item into VERBATIM, SUMMARY, or ARCHIVED.
        """
        existing_texts = [m.content for m in active_memories] if active_memories else []
        rule_signal: RuleSignal = self.rule_engine.evaluate(content, existing_memories=existing_texts)

        # Fast path: Obvious high-confidence rule match bypasses LLM call
        if rule_signal.is_definitive and rule_signal.suggested_tier is not None:
            tier = rule_signal.suggested_tier
            decision = self._map_tier_to_decision(tier)
            return ClassificationResult(
                tier=tier,
                confidence=rule_signal.confidence,
                decision=decision,
                reason=rule_signal.reason,
                matched_rules=rule_signal.matched_rules,
                source_message_ids=list(source_message_ids),
                content_to_store=content.strip(),
                used_llm_judge=False,
            )

        # Ambiguous path: Invoke semantic LLM judge
        active_dicts = [m.to_dict() for m in active_memories] if active_memories else []
        judgment: JudgmentResult = self.judge.judge(
            message_content=content,
            source_message_ids=source_message_ids,
            active_memories=active_dicts,
        )

        tier = judgment.tier
        confidence = judgment.confidence
        reason = judgment.reason

        # Conservative preservation policy:
        # Never archive low-confidence items; escalate to VERBATIM preservation
        if tier == MemoryTier.ARCHIVED.value and confidence < self.ARCHIVE_CONFIDENCE_THRESHOLD:
            tier = MemoryTier.VERBATIM.value
            reason = (
                f"Candidate marked as low-confidence archive ({confidence:.2f}); "
                "escalated to VERBATIM to prevent silent loss of potentially important information."
            )

        # If rule engine identified verbatim signals even if not fully definitive, respect them
        if rule_signal.suggested_tier == MemoryTier.VERBATIM.value and tier == MemoryTier.ARCHIVED.value:
            tier = MemoryTier.VERBATIM.value
            reason = (
                f"Deterministic rules detected factual indicators ({', '.join(rule_signal.matched_rules)}); "
                "overriding judge archive recommendation."
            )

        decision = self._map_tier_to_decision(tier)
        content_to_store = judgment.extracted_fact or content.strip()

        return ClassificationResult(
            tier=tier,
            confidence=confidence,
            decision=decision,
            reason=reason,
            matched_rules=rule_signal.matched_rules,
            source_message_ids=list(source_message_ids),
            content_to_store=content_to_store,
            used_llm_judge=True,
        )

    @staticmethod
    def _map_tier_to_decision(tier: str) -> str:
        if tier == MemoryTier.VERBATIM.value:
            return "KEEP_VERBATIM"
        elif tier == MemoryTier.SUMMARY.value:
            return "SUMMARIZE"
        elif tier == MemoryTier.ARCHIVED.value:
            return "ARCHIVE"
        return "KEEP_VERBATIM"
