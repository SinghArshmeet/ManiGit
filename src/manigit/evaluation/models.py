"""
Evaluation data models and schema definitions.

Defines:
- Baseline types and ablation modes
- Scenario categories, turns, and benchmark queries
- Evaluation metrics and experiment result records
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from manigit.core.models import utc_now_iso


class BaselineType(str, Enum):
    """Evaluation baseline methods."""
    FULL_HISTORY = "full_history"
    SLIDING_WINDOW = "sliding_window"
    SUMMARY = "summary"
    RAG_STYLE = "rag_style"
    MANIGIT = "manigit"


class AblationMode(str, Enum):
    """Ablation configurations for ManiGit components."""
    FULL = "full"
    NO_CONTRADICTION = "no_contradiction"
    NO_CONFIDENCE = "no_confidence"
    NO_TIER = "no_tier"
    # Legacy modes preserved for backwards compatibility
    RETRIEVAL_ONLY = "retrieval_only"
    RETRIEVAL_TIERING = "retrieval_tiering"
    RETRIEVAL_TIERING_CONFIDENCE = "retrieval_tiering_confidence"


class ScenarioCategory(str, Enum):
    """Categories of synthetic benchmark scenarios."""
    STABLE_FACTS = "stable_facts"
    SUPERSEDING_FACTS = "superseding_facts"
    EXACT_CONSTRAINTS = "exact_constraints"
    DECISIONS = "decisions"
    TECHNICAL_FACTS = "technical_facts"
    DISTRACTORS = "distractors"
    DUPLICATES = "duplicates"
    LONG_CONVERSATION = "long_conversation"
    AMBIGUOUS_CONFIDENCE = "ambiguous_confidence"
    TIER_COMPETITION = "tier_competition"


@dataclass
class ScenarioTurn:
    """A single dialogue turn within a benchmark scenario."""
    turn_index: int
    role: str  # "user" or "assistant"
    content: str
    is_distractor: bool = False
    contains_fact: Optional[str] = None
    fact_key: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScenarioTurn":
        return cls(**data)


@dataclass
class BenchmarkQuery:
    """
    An evaluation query probing retention or historical recovery of facts.
    """
    query_id: str
    query: str
    expected_answer: str
    acceptable_alternatives: List[str] = field(default_factory=list)
    is_historical: bool = False
    target_commit_ref: Optional[str] = None  # Reference to earlier commit if historical
    target_fact_key: Optional[str] = None
    relevant_turn_indices: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkQuery":
        return cls(**data)


@dataclass
class BenchmarkScenario:
    """
    A complete evaluation scenario consisting of sequential dialogue turns and queries.
    """
    scenario_id: str
    name: str
    category: ScenarioCategory
    description: str
    turns: List[ScenarioTurn] = field(default_factory=list)
    queries: List[BenchmarkQuery] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "category": self.category.value if isinstance(self.category, ScenarioCategory) else self.category,
            "description": self.description,
            "turns": [t.to_dict() for t in self.turns],
            "queries": [q.to_dict() for q in self.queries],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkScenario":
        category = ScenarioCategory(data["category"]) if isinstance(data["category"], str) else data["category"]
        turns = [ScenarioTurn.from_dict(t) for t in data.get("turns", [])]
        queries = [BenchmarkQuery.from_dict(q) for q in data.get("queries", [])]
        return cls(
            scenario_id=data["scenario_id"],
            name=data["name"],
            category=category,
            description=data.get("description", ""),
            turns=turns,
            queries=queries,
            metadata=data.get("metadata", {}),
        )


@dataclass
class EvaluationMetrics:
    """Quantitative evaluation metrics collected per experiment trial."""
    context_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    context_utilization: float = 0.0  # used_context_tokens / budget
    fact_recall: bool = False  # Expected fact retrieved/present in context
    answer_correctness: bool = False  # Model answer matches expected answer
    historical_recall: Optional[bool] = None  # Superseded fact recovered
    contradiction_accuracy: Optional[bool] = None  # Distinguishes current vs superseded
    retrieval_precision: float = 0.0
    retrieval_recall: float = 0.0
    latency_context_ms: float = 0.0
    latency_generation_ms: float = 0.0
    latency_total_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvaluationMetrics":
        return cls(**data)


@dataclass
class BenchmarkResult:
    """The structured record of a single benchmark trial."""
    experiment_id: str
    scenario_id: str
    method: str
    conversation_length: int
    budget: int
    query_id: str
    query: str
    expected_answer: str
    actual_answer: str
    compiled_context: str
    metrics: EvaluationMetrics
    success: bool
    config_metadata: Dict[str, Any] = field(default_factory=dict)
    ablation_mode: Optional[str] = None
    retrieved_indices: List[int] = field(default_factory=list)
    timestamp: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "scenario_id": self.scenario_id,
            "method": self.method,
            "ablation_mode": self.ablation_mode,
            "conversation_length": self.conversation_length,
            "budget": self.budget,
            "query_id": self.query_id,
            "query": self.query,
            "expected_answer": self.expected_answer,
            "actual_answer": self.actual_answer,
            "compiled_context": self.compiled_context,
            "metrics": self.metrics.to_dict(),
            "success": self.success,
            "config_metadata": self.config_metadata,
            "retrieved_indices": self.retrieved_indices,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkResult":
        metrics_data = data.get("metrics", {})
        metrics = EvaluationMetrics.from_dict(metrics_data) if isinstance(metrics_data, dict) else metrics_data
        return cls(
            experiment_id=data["experiment_id"],
            scenario_id=data["scenario_id"],
            method=data["method"],
            ablation_mode=data.get("ablation_mode"),
            conversation_length=data["conversation_length"],
            budget=data["budget"],
            query_id=data["query_id"],
            query=data["query"],
            expected_answer=data["expected_answer"],
            actual_answer=data["actual_answer"],
            compiled_context=data.get("compiled_context", ""),
            metrics=metrics,
            success=data.get("success", False),
            config_metadata=data.get("config_metadata", {}),
            retrieved_indices=data.get("retrieved_indices", []),
            timestamp=data.get("timestamp", utc_now_iso()),
        )
