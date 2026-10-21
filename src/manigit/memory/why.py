"""
Why Report domain model for auditability and explainability of memory decisions.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from manigit.core.models import utc_now_iso


@dataclass(frozen=True)
class WhyReport:
    """
    Structured explanation recording why information was retained, summarized, or archived.
    
    Powers transparent user auditing, explainability, and future commit inspections.
    """
    decision: str                          # e.g., "KEEP_VERBATIM", "SUMMARIZE", "ARCHIVE", "SUPERSEDE"
    tier: str                              # "VERBATIM", "SUMMARY", "ARCHIVED"
    confidence: float                      # 0.0 to 1.0
    reason: str                            # Human-readable justification
    source_message_ids: List[str]          # Provenance links
    matched_rules: List[str] = field(default_factory=list)
    predecessor_memory_id: Optional[str] = None
    contradiction_info: Optional[Dict[str, Any]] = None
    tokens_before: int = 0
    tokens_after: int = 0
    timestamp: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "tier": self.tier,
            "confidence": self.confidence,
            "reason": self.reason,
            "source_message_ids": list(self.source_message_ids),
            "matched_rules": list(self.matched_rules),
            "predecessor_memory_id": self.predecessor_memory_id,
            "contradiction_info": self.contradiction_info,
            "tokens_before": self.tokens_before,
            "tokens_after": self.tokens_after,
            "timestamp": self.timestamp,
        }
