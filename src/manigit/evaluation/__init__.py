"""
ManiGit Research Evaluation and Benchmarking Framework.

Provides reproducible testing and measurement harnesses:
- Deterministic synthetic long-running agent scenarios (A through H)
- Uniform comparative baselines (Full History, Sliding Window, Summary, RAG-Style, ManiGit)
- Comprehensive quantitative metrics (Tokens, utilization, recall, precision, latency)
- Storage of trial records in isolated JSON/JSONL format
- Markdown report generator for empirical paper figures and tables
"""

from manigit.evaluation.baselines import (
    BaseEvaluationMethod,
    FullHistoryBaseline,
    ManiGitEvaluationMethod,
    RAGStyleBaseline,
    SlidingWindowBaseline,
    SummaryBaseline,
)
from manigit.evaluation.metrics import (
    calculate_answer_correctness,
    calculate_contradiction_accuracy,
    calculate_fact_recall,
    calculate_historical_recovery,
    calculate_retrieval_precision_recall,
    calculate_token_metrics,
    compute_metrics,
)
from manigit.evaluation.models import (
    AblationMode,
    BaselineType,
    BenchmarkQuery,
    BenchmarkResult,
    BenchmarkScenario,
    EvaluationMetrics,
    ScenarioCategory,
    ScenarioTurn,
)
from manigit.evaluation.reporting import BenchmarkReportGenerator
from manigit.evaluation.runner import BenchmarkConfig, BenchmarkRunner
from manigit.evaluation.scenarios import (
    create_decisions_scenario,
    create_distractor_scenario,
    create_duplicate_scenario,
    create_exact_constraints_scenario,
    create_long_conversation_scenario,
    create_stable_facts_scenario,
    create_superseding_facts_scenario,
    create_technical_facts_scenario,
    get_standard_benchmark_suite,
    load_scenario_from_disk,
    save_scenario_to_disk,
)
from manigit.evaluation.storage import BenchmarkResultStorage

__all__ = [
    # Models
    "BaselineType",
    "AblationMode",
    "ScenarioCategory",
    "ScenarioTurn",
    "BenchmarkQuery",
    "BenchmarkScenario",
    "EvaluationMetrics",
    "BenchmarkResult",
    # Scenarios
    "create_stable_facts_scenario",
    "create_superseding_facts_scenario",
    "create_exact_constraints_scenario",
    "create_decisions_scenario",
    "create_technical_facts_scenario",
    "create_distractor_scenario",
    "create_duplicate_scenario",
    "create_long_conversation_scenario",
    "get_standard_benchmark_suite",
    "save_scenario_to_disk",
    "load_scenario_from_disk",
    # Baselines
    "BaseEvaluationMethod",
    "FullHistoryBaseline",
    "SlidingWindowBaseline",
    "SummaryBaseline",
    "RAGStyleBaseline",
    "ManiGitEvaluationMethod",
    # Metrics
    "calculate_token_metrics",
    "calculate_fact_recall",
    "calculate_answer_correctness",
    "calculate_historical_recovery",
    "calculate_contradiction_accuracy",
    "calculate_retrieval_precision_recall",
    "compute_metrics",
    # Storage
    "BenchmarkResultStorage",
    # Runner
    "BenchmarkConfig",
    "BenchmarkRunner",
    # Reporting
    "BenchmarkReportGenerator",
]
