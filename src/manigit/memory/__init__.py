"""
Memory Intelligence Subsystem.

Responsible for automated 3-tier classification, confidence scoring,
semantic judging, summarization, contradiction detection, and Why Reports:
- Tier 1: VERBATIM (uncompressed, strict constraints, code, errors, exact numbers)
- Tier 2: SUMMARY (condensed multi-turn discussions with provenance)
- Tier 3: ARCHIVED (conversational filler, preserved in raw history with provenance)
"""

from manigit.memory.classifier import ClassificationResult, MemoryClassifier
from manigit.memory.contradiction import ContradictionDetector, ContradictionResult
from manigit.memory.judge import JudgmentResult, MemoryJudge
from manigit.memory.rules import RuleEngine, RuleSignal
from manigit.memory.service import MemoryProcessingResult, MemoryService
from manigit.memory.summarizer import MemorySummarizer, SummaryResult
from manigit.memory.why import WhyReport

__all__ = [
    "RuleEngine",
    "RuleSignal",
    "MemoryJudge",
    "JudgmentResult",
    "MemoryClassifier",
    "ClassificationResult",
    "ContradictionDetector",
    "ContradictionResult",
    "MemorySummarizer",
    "SummaryResult",
    "WhyReport",
    "MemoryService",
    "MemoryProcessingResult",
]
