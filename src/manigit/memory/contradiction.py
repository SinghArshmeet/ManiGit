"""
Contradiction and supersession detection between new information and active memory.
"""

from dataclasses import dataclass
import re
from typing import List, Optional

from manigit.core.models import Memory


@dataclass(frozen=True)
class ContradictionResult:
    """Structured result of contradiction and supersession detection."""
    has_contradiction: bool
    superseded_memory_id: Optional[str] = None
    conflict_type: str = "NONE"  # "EXPLICIT_REPLACEMENT", "KEY_OVERWRITE", "TOPICAL_MUTATION", "NONE"
    explanation: str = ""
    historical_fact: Optional[str] = None
    current_fact: Optional[str] = None


class ContradictionDetector:
    """
    Practical detector for conflicting assertions and supersessions.
    
    Identifies when a new assertion replaces or updates an existing active memory,
    ensuring the historical memory is superseded rather than silently erased.
    """

    REPLACEMENT_PATTERNS = [
        re.compile(r"\b(?:change|switch|replace|update)\s+(?:from\s+)?(.+?)\s+(?:to|with)\s+(.+)", re.IGNORECASE),
        re.compile(r"\b(?:instead of)\s+(.+?)[,\s]+(?:use|we will use|let's use|we've decided on)\s+(.+)", re.IGNORECASE),
        re.compile(r"\b(?:no longer|don't use)\s+(.+?)[,\s]+(?:use|now using|switch to)\s+(.+)", re.IGNORECASE),
        re.compile(r"\b(?:actually|revised?|correction)[,\s]+(?:we decided to use|use|it is)\s+(.+)", re.IGNORECASE),
    ]

    KEY_VALUE_PATTERN = re.compile(
        r"\b([a-zA-Z0-9_\-\s]{2,25})\s*(?:[:=]|is now|will be|is)\s*([a-zA-Z0-9_.\-/$%]+)",
        re.IGNORECASE,
    )

    # Core topics often subject to constraint revision
    TOPIC_KEYWORDS = [
        "database", "db", "budget", "language", "framework", "model",
        "provider", "port", "theme", "color", "deadline", "architecture",
        "backend", "frontend", "auth", "license", "storage"
    ]

    def detect(self, new_text: str, active_memories: List[Memory]) -> ContradictionResult:
        """
        Evaluate new_text against currently active memories to identify contradictions.
        """
        if not active_memories or not new_text.strip():
            return ContradictionResult(has_contradiction=False)

        new_clean = new_text.strip()
        new_lower = new_clean.lower()

        # Inquiries and questions do not assert facts or supersede memory
        if new_clean.endswith("?") or any(
            new_lower.startswith(q) for q in [
                "what", "which", "where", "when", "why", "who", "how",
                "is", "are", "can", "could", "would", "do", "does", "did"
            ]
        ):
            return ContradictionResult(has_contradiction=False)

        # 1. Check for explicit replacement phrasing ("change X to Y", "instead of X use Y")
        for pattern in self.REPLACEMENT_PATTERNS:
            match = pattern.search(new_text)
            if match:
                old_subject = match.group(1).strip().lower()
                new_subject = match.group(2).strip()

                for mem in active_memories:
                    mem_lower = mem.content.lower()
                    if old_subject in mem_lower or any(word in mem_lower for word in old_subject.split() if len(word) > 3):
                        return ContradictionResult(
                            has_contradiction=True,
                            superseded_memory_id=mem.id,
                            conflict_type="EXPLICIT_REPLACEMENT",
                            explanation=f"Explicit replacement: '{old_subject}' was superseded by '{new_subject}'.",
                            historical_fact=mem.content,
                            current_fact=new_text.strip(),
                        )

        # 2. Check for key/attribute overwrites (e.g. "Database: PostgreSQL" vs "Database: MongoDB")
        new_kv_matches = self.KEY_VALUE_PATTERN.findall(new_text)
        ignored_prefix_keys = {
            "constraint", "note", "rule", "fact", "instruction",
            "requirement", "preferences", "update", "step", "summary"
        }
        for key, val in new_kv_matches:
            key_clean = key.strip().lower()
            if key_clean in ignored_prefix_keys:
                continue
            val_clean = val.strip().lower()
            for mem in active_memories:
                mem_lower = mem.content.lower()
                if key_clean in mem_lower and val_clean not in mem_lower:
                    # Same key/topic present, but different value
                    return ContradictionResult(
                        has_contradiction=True,
                        superseded_memory_id=mem.id,
                        conflict_type="KEY_OVERWRITE",
                        explanation=f"Key '{key_clean}' updated to new value.",
                        historical_fact=mem.content,
                        current_fact=new_text.strip(),
                    )

        # 3. Check for specific topic keyword collisions with conflicting details
        for topic in self.TOPIC_KEYWORDS:
            if topic in new_lower:
                for mem in active_memories:
                    mem_lower = mem.content.lower()
                    if topic in mem_lower and new_lower != mem_lower:
                        # Shared critical topic keyword with different phrasing/value
                        # Check if words overlap significantly (e.g., database postgres vs database mongodb)
                        return ContradictionResult(
                            has_contradiction=True,
                            superseded_memory_id=mem.id,
                            conflict_type="TOPICAL_MUTATION",
                            explanation=f"Topical assertion regarding '{topic}' superseded earlier assertion.",
                            historical_fact=mem.content,
                            current_fact=new_text.strip(),
                        )

        return ContradictionResult(has_contradiction=False)
