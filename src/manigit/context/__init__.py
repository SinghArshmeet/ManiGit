"""
Context Compiler Subsystem.

Responsible for deterministic, query-specific memory selection under strict token budgets:
- Retrieval: local deterministic filtering of reconstructed active memory state
- Scoring: relevance-first priority scoring, constraint/decision boosts, deterministic tie-breaking
- Token Budget: strict budget enforcement, greedy token-budget selection, boundary handling
- Compiler: assembling ContextResult with full selection/exclusion auditing and prompt formatting
"""

from manigit.context.budget import ContextBudget
from manigit.context.compiler import ContextCompiler
from manigit.context.models import (
    ContextResult,
    ExcludedMemory,
    ScoringWeights,
    SelectedMemory,
)
from manigit.context.retrieval import MemoryRetriever
from manigit.context.scoring import ScoringEngine

__all__ = [
    "ContextBudget",
    "ContextCompiler",
    "ContextResult",
    "SelectedMemory",
    "ExcludedMemory",
    "ScoringWeights",
    "MemoryRetriever",
    "ScoringEngine",
]
