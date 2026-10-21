"""
Targeted test suite for Phase 8: Research Validation, Ablation & Paper-Ready Evidence.

Verifies:
1. Ablation matrix cardinality (880 trials) and schema validation
2. No-contradiction ablation mechanism & detector behavior
3. No-confidence ablation mechanism & classifier escalation behavior
4. No-tier ablation mechanism & budget ranking competition
5. Production ManiGit integrity (production classes and defaults remain intact)
6. Canonical experiment protection (exp_canonical_run_001 cannot be overwritten)
7. Raw result schema validation & trial uniqueness
8. Aggregate vs raw result consistency (zero synthetic fabrication)
9. Budget compliance (context_tokens <= budget for all 880 trials)
10. Reproducibility under deterministic seed 42
11. Statistical calculation correctness (Wilson score CI & continuous stats)
12. Paper-ready figure data generation and file integrity
"""

import json
from pathlib import Path
import pytest

from manigit.context.models import ScoringWeights
from manigit.core.models import MemoryStatus, MemoryTier
from manigit.core.repository import ManiGitRepository
from manigit.evaluation.baselines import (
    DisabledContradictionDetector,
    ManiGitEvaluationMethod,
    NoConfidenceMemoryClassifier,
)
from manigit.evaluation.figures import FigureDataGenerator
from manigit.evaluation.models import AblationMode, BaselineType, BenchmarkResult
from manigit.evaluation.reporting import BenchmarkReportGenerator
from manigit.evaluation.runner import BenchmarkConfig, BenchmarkRunner
from manigit.evaluation.scenarios import (
    create_ambiguous_confidence_scenario,
    create_superseding_facts_scenario,
    create_tier_competition_scenario,
    get_ablation_benchmark_suite,
    get_standard_benchmark_suite,
)
from manigit.evaluation.statistics import (
    compute_continuous_stats,
    compute_paired_comparison,
    wilson_score_interval,
)
from manigit.evaluation.storage import BenchmarkResultStorage
from manigit.memory.classifier import MemoryClassifier
from manigit.memory.contradiction import ContradictionDetector
from manigit.models.mock import MockModelAdapter


def test_ablation_matrix_cardinality_and_uniqueness():
    """Verify raw ablation results file contains exactly 880 trials and unique keys."""
    results_path = Path("data/processed/benchmarks/results/exp_ablation_run_001.json")
    assert results_path.exists(), "Ablation results file does not exist!"

    with open(results_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # 11 scenarios (22 queries) * 8 methods * 5 budgets = 880 trials
    assert len(raw_data) == 880, f"Expected 880 trials, found {len(raw_data)}"

    # Verify trial uniqueness: (method, budget, scenario_id, query_id)
    seen_keys = set()
    valid_budgets = {128, 256, 512, 1024, 2048}
    valid_methods = {
        "Full History",
        "Sliding Window (N=10)",
        "Running Summary",
        "RAG-Style (Raw Messages)",
        "ManiGit (full)",
        "ManiGit (no_contradiction)",
        "ManiGit (no_confidence)",
        "ManiGit (no_tier)",
    }

    for trial in raw_data:
        key = (trial["method"], trial["budget"], trial["scenario_id"], trial["query_id"])
        assert key not in seen_keys, f"Duplicate trial detected: {key}"
        seen_keys.add(key)

        assert trial["method"] in valid_methods, f"Invalid method: {trial['method']}"
        assert trial["budget"] in valid_budgets, f"Invalid budget: {trial['budget']}"
        assert trial["experiment_id"] == "exp_ablation_run_001"
        assert "metrics" in trial


def test_budget_compliance_all_trials():
    """Verify context_tokens <= budget across all 880 trials (no budget violations)."""
    results_path = Path("data/processed/benchmarks/results/exp_ablation_run_001.json")
    with open(results_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    for trial in raw_data:
        ctx_tokens = trial["metrics"]["context_tokens"]
        budget = trial["budget"]
        assert ctx_tokens <= budget, (
            f"Budget violation: {trial['method']} consumed {ctx_tokens} > budget {budget} "
            f"on query {trial['query_id']}"
        )


def test_canonical_benchmark_file_protection():
    """Verify that canonical benchmark results cannot be overwritten and remain intact."""
    canonical_path = Path("data/processed/benchmarks/results/exp_canonical_run_001.json")
    assert canonical_path.exists(), "Canonical run file missing!"

    with open(canonical_path, "r", encoding="utf-8") as f:
        canonical_trials = json.load(f)
    assert len(canonical_trials) == 500, "Canonical run must contain exactly 500 trials!"

    # Verify storage safeguard raises PermissionError
    storage = BenchmarkResultStorage()
    with pytest.raises(PermissionError, match="exp_canonical_run_001"):
        storage.save_run("exp_canonical_run_001", [])


def test_production_manigit_remains_unchanged():
    """Verify that production ManiGit classes and defaults are completely unmodified."""
    # Production contradiction detector
    detector = ContradictionDetector()
    assert detector is not None
    assert type(detector) is ContradictionDetector

    # Production memory classifier threshold
    assert MemoryClassifier.ARCHIVE_CONFIDENCE_THRESHOLD == 0.75

    # Production context scoring weights
    weights = ScoringWeights()
    assert weights.verbatim_boost == 0.10
    assert weights.summary_boost == 0.05
    assert weights.confidence_weight == 0.05
    assert weights.constraint_boost == 0.15
    assert weights.decision_boost == 0.10
    assert weights.relevance_weight == 0.5


def test_no_contradiction_ablation_mechanism():
    """Verify DisabledContradictionDetector disables contradiction detection without breaking immutability."""
    disabled_detector = DisabledContradictionDetector()
    res = disabled_detector.detect("Switch from PostgreSQL to MongoDB", [])
    assert not res.has_contradiction
    assert res.conflict_type == "NONE"
    assert "disabled" in res.explanation.lower()

    # Verify in ManiGitEvaluationMethod
    method = ManiGitEvaluationMethod(AblationMode.NO_CONTRADICTION)
    assert method.ablation_mode == AblationMode.NO_CONTRADICTION
    assert method.name == "ManiGit (no_contradiction)"


def test_no_confidence_ablation_mechanism():
    """Verify NoConfidenceMemoryClassifier neutralizes confidence escalation."""
    assert NoConfidenceMemoryClassifier.ARCHIVE_CONFIDENCE_THRESHOLD == 0.0

    # In production classifier, a low-confidence archive (0.55) is escalated to VERBATIM
    model = MockModelAdapter()
    repo = ManiGitRepository(db_path=":memory:")
    repo.initialize_repository()

    # In no_confidence method, classifier uses threshold 0.0
    method = ManiGitEvaluationMethod(AblationMode.NO_CONFIDENCE)
    sc = create_ambiguous_confidence_scenario()
    method.setup(sc, model)
    assert isinstance(method.runtime.memory_service.classifier, NoConfidenceMemoryClassifier)


def test_no_tier_ablation_mechanism():
    """Verify NoTier ablation sets verbatim_boost and summary_boost to 0.0."""
    method = ManiGitEvaluationMethod(AblationMode.NO_TIER)
    sc = create_tier_competition_scenario()
    model = MockModelAdapter()
    method.setup(sc, model)

    scoring_weights = method.compiler.scoring_engine.weights
    assert scoring_weights.verbatim_boost == 0.0
    assert scoring_weights.summary_boost == 0.0
    # Other weights intact
    assert scoring_weights.confidence_weight == 0.05
    assert scoring_weights.relevance_weight == 0.5


def test_wilson_score_interval_mathematical_properties():
    """Verify Wilson score confidence interval computation and boundary properties."""
    # 0 successes out of 10
    p, low, high = wilson_score_interval(0, 10, confidence=0.95)
    assert p == 0.0
    assert low == 0.0
    assert high > 0.0 and high < 0.35

    # 10 successes out of 10
    p, low, high = wilson_score_interval(10, 10, confidence=0.95)
    assert p == 1.0
    assert low > 0.65
    assert high == 1.0

    # 50 out of 100 (symmetric)
    p, low, high = wilson_score_interval(50, 100, confidence=0.95)
    assert p == 0.5
    assert round(0.5 - low, 2) == round(high - 0.5, 2)
    assert low > 0.39 and high < 0.61

    # Empty sample
    assert wilson_score_interval(0, 0) == (0.0, 0.0, 0.0)


def test_continuous_statistics_computation():
    """Verify continuous descriptive statistics computation."""
    vals = [10.0, 20.0, 30.0, 40.0, 50.0]
    stats = compute_continuous_stats(vals)
    assert stats["mean"] == 30.0
    assert stats["median"] == 30.0
    assert stats["min"] == 10.0
    assert stats["max"] == 50.0
    assert stats["count"] == 5
    assert stats["std"] > 15.0 and stats["std"] < 16.0

    # Empty list
    empty_stats = compute_continuous_stats([])
    assert empty_stats["mean"] == 0.0
    assert empty_stats["count"] == 0


def test_aggregate_vs_raw_consistency():
    """Verify report aggregates match calculations derived directly from raw results."""
    results_path = Path("data/processed/benchmarks/results/exp_ablation_run_001.json")
    with open(results_path, "r", encoding="utf-8") as f:
        raw_data = [BenchmarkResult.from_dict(d) for d in json.load(f)]

    report_gen = BenchmarkReportGenerator(raw_data)
    aggs = report_gen.generate_method_aggregates()

    for method, d in aggs.items():
        m_trials = [r for r in raw_data if r.method == method]
        n = len(m_trials)
        raw_recall = round(sum(1 for r in m_trials if r.metrics.fact_recall) / n, 4)
        raw_correctness = round(sum(1 for r in m_trials if r.metrics.answer_correctness) / n, 4)
        raw_avg_ctx = round(sum(r.metrics.context_tokens for r in m_trials) / n, 1)

        assert d["trials"] == n
        assert d["fact_recall_rate"] == raw_recall
        assert d["answer_correctness_rate"] == raw_correctness
        assert d["avg_context_tokens"] == raw_avg_ctx


def test_figure_data_generation_integrity():
    """Verify that all 7 figure datasets exist and can be loaded cleanly."""
    figures_dir = Path("data/processed/benchmarks/figures")
    assert figures_dir.exists()

    expected_figures = [
        "fig1_context_vs_budget",
        "fig2_fact_recall_vs_budget",
        "fig3_correctness_vs_budget",
        "fig4_historical_recovery",
        "fig5_contradiction_handling",
        "fig6_ablation_degradation",
        "fig7_efficiency_tradeoff",
    ]

    for fig in expected_figures:
        json_file = figures_dir / f"{fig}.json"
        csv_file = figures_dir / f"{fig}.csv"
        assert json_file.exists(), f"Missing {json_file}"
        assert csv_file.exists(), f"Missing {csv_file}"

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert len(data) > 0, f"Empty figure data in {json_file}"


def test_deterministic_reproducibility_seed_42():
    """Verify that running the ablation runner twice with seed 42 produces bit-for-bit identical results."""
    config = BenchmarkConfig(
        experiment_id="exp_repro_test",
        methods=[BaselineType.MANIGIT],
        ablation_modes=[AblationMode.FULL, AblationMode.NO_CONTRADICTION],
        budgets=[128, 256],
        scenarios=["superseding_facts"],
        random_seed=42,
    )

    runner1 = BenchmarkRunner(config=config)
    suite = get_ablation_benchmark_suite()
    res1 = runner1.run_benchmark(suite=suite, save_results=False)

    runner2 = BenchmarkRunner(config=config)
    res2 = runner2.run_benchmark(suite=suite, save_results=False)

    assert len(res1) == len(res2)
    for t1, t2 in zip(res1, res2):
        assert t1.method == t2.method
        assert t1.budget == t2.budget
        assert t1.compiled_context == t2.compiled_context
        assert t1.actual_answer == t2.actual_answer
        assert t1.metrics.fact_recall == t2.metrics.fact_recall
        assert t1.metrics.answer_correctness == t2.metrics.answer_correctness
