"""
Unit tests for benchmark runner and experiment execution.
"""

from pathlib import Path
import tempfile
import pytest

from manigit.evaluation.models import BaselineType
from manigit.evaluation.runner import BenchmarkConfig, BenchmarkRunner
from manigit.evaluation.scenarios import (
    create_exact_constraints_scenario,
    create_stable_facts_scenario,
)
from manigit.evaluation.storage import BenchmarkResultStorage


def test_runner_mini_matrix():
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = BenchmarkResultStorage(base_dir=tmp_dir)
        config = BenchmarkConfig(
            experiment_id="test_exp_mini",
            methods=[BaselineType.FULL_HISTORY, BaselineType.MANIGIT],
            budgets=[256, 512],
            scenarios=["stable_facts"],
            storage_dir=tmp_dir,
            random_seed=42,
        )

        runner = BenchmarkRunner(config=config, storage=storage)
        mini_suite = {"stable_facts": create_stable_facts_scenario()}
        results = runner.run_benchmark(suite=mini_suite, save_results=True)

        # 2 methods * 2 budgets * 2 queries = 8 trials
        assert len(results) == 8

        for r in results:
            assert r.experiment_id == "test_exp_mini"
            assert r.scenario_id == "scenario_a_stable_facts"
            assert r.budget in [256, 512]
            assert r.metrics.context_tokens > 0
            assert r.metrics.latency_total_ms >= 0.0

        # Verify disk persistence
        loaded = storage.load_run("test_exp_mini")
        assert len(loaded) == 8


def test_runner_reproducibility():
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = BenchmarkResultStorage(base_dir=tmp_dir)
        config1 = BenchmarkConfig(
            experiment_id="test_rep_1",
            methods=[BaselineType.MANIGIT],
            budgets=[256],
            scenarios=["exact_constraints"],
            storage_dir=tmp_dir,
            random_seed=123,
        )
        runner1 = BenchmarkRunner(config=config1, storage=storage)
        suite = {"exact_constraints": create_exact_constraints_scenario()}
        res1 = runner1.run_benchmark(suite=suite, save_results=False)

        config2 = BenchmarkConfig(
            experiment_id="test_rep_2",
            methods=[BaselineType.MANIGIT],
            budgets=[256],
            scenarios=["exact_constraints"],
            storage_dir=tmp_dir,
            random_seed=123,
        )
        runner2 = BenchmarkRunner(config=config2, storage=storage)
        res2 = runner2.run_benchmark(suite=suite, save_results=False)

        assert len(res1) == len(res2)
        for r1, r2 in zip(res1, res2):
            assert r1.metrics.fact_recall == r2.metrics.fact_recall
            assert r1.metrics.context_tokens == r2.metrics.context_tokens
            assert r1.actual_answer == r2.actual_answer


def test_canonical_matrix_cardinality():
    """
    Verifies that the canonical benchmark suite matrix cardinality strictly equals:
    20 queries across 9 scenario instances * 5 methods * 5 budgets = 500 trials.
    """
    from manigit.evaluation.scenarios import get_standard_benchmark_suite
    suite = get_standard_benchmark_suite()
    
    # 9 scenario instances covering the 8 categories
    assert len(suite) == 9
    
    total_queries = sum(len(s.queries) for s in suite.values())
    assert total_queries == 20

    config = BenchmarkConfig()
    num_methods = len(config.methods)
    num_budgets = len(config.budgets)
    assert num_methods == 5
    assert num_budgets == 5

    expected_total_trials = total_queries * num_methods * num_budgets
    assert expected_total_trials == 500


def test_benchmark_database_isolation():
    """
    Verifies that benchmark execution does NOT mutate data/database/manigit.db.
    """
    import os
    db_file = Path("data/database/manigit.db")
    mtime_before = os.path.getmtime(db_file) if db_file.exists() else None

    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = BenchmarkResultStorage(base_dir=tmp_dir)
        config = BenchmarkConfig(
            experiment_id="test_db_isolation",
            methods=[BaselineType.MANIGIT],
            budgets=[256],
            scenarios=["stable_facts"],
            storage_dir=tmp_dir,
        )
        runner = BenchmarkRunner(config=config, storage=storage)
        mini_suite = {"stable_facts": create_stable_facts_scenario()}
        results = runner.run_benchmark(suite=mini_suite, save_results=True)
        assert len(results) > 0

    # Ensure repository db file was never created or modified by benchmark run
    if mtime_before is not None:
        assert os.path.getmtime(db_file) == mtime_before
    else:
        # If it didn't exist before, it still must not exist
        assert not db_file.exists()


def test_context_tokens_strictly_bounded_by_budget():
    """
    Regression test enforcing Research Integrity:
    1. For EVERY single benchmark trial in the canonical suite (N=500), context_tokens <= budget.
    2. Zero trials may violate the hard token budget constraint.
    3. Specifically verifies the exact B=128 empirical metrics for every evaluated method.
    """
    import json
    raw_path = Path("data/processed/benchmarks/results/exp_canonical_run_001.json")
    assert raw_path.exists(), "Canonical benchmark results file must exist"
    trials = json.loads(raw_path.read_text())
    assert len(trials) == 500

    # 1. Enforce hard budget on every trial
    violations = []
    for t in trials:
        ctx_tok = t["metrics"]["context_tokens"]
        budget = t["budget"]
        if ctx_tok > budget:
            violations.append((t["method"], budget, t["query_id"], ctx_tok))
    assert violations == [], f"Detected budget violations: {violations}"

    # 2. Specifically verify B=128 metrics for all 5 methods
    b128_trials = [t for t in trials if t["budget"] == 128]
    assert len(b128_trials) == 100

    methods = [
        "ManiGit (full)",
        "Full History",
        "Sliding Window (N=10)",
        "RAG-Style (Raw Messages)",
        "Running Summary",
    ]

    expected_b128 = {
        "ManiGit (full)": {"avg_ctx": 79.2, "recall": 0.85, "max_ctx": 124},
        "Full History": {"avg_ctx": 109.9, "recall": 0.75, "max_ctx": 128},
        "Sliding Window (N=10)": {"avg_ctx": 116.9, "recall": 0.70, "max_ctx": 128},
        "RAG-Style (Raw Messages)": {"avg_ctx": 90.7, "recall": 0.95, "max_ctx": 127},
        "Running Summary": {"avg_ctx": 35.5, "recall": 0.95, "max_ctx": 52},
    }

    for m in methods:
        m_trials = [t for t in b128_trials if t["method"] == m]
        assert len(m_trials) == 20
        avg_ctx = sum(t["metrics"]["context_tokens"] for t in m_trials) / 20.0
        max_ctx = max(t["metrics"]["context_tokens"] for t in m_trials)
        recall = sum(1 for t in m_trials if t["metrics"]["fact_recall"]) / 20.0

        assert avg_ctx <= 128.0, f"{m} exceeded B=128 average: {avg_ctx}"
        assert max_ctx <= 128, f"{m} exceeded B=128 max: {max_ctx}"
        assert round(avg_ctx, 1) == expected_b128[m]["avg_ctx"]
        assert round(recall, 2) == expected_b128[m]["recall"]
        assert max_ctx == expected_b128[m]["max_ctx"]


def test_budget_specific_metrics_distinct_from_aggregate():
    """
    Regression test preventing budget-specific reporting from accidentally using
    aggregate metrics across all budgets.
    """
    import json
    from manigit.evaluation.reporting import BenchmarkReportGenerator
    from manigit.evaluation.storage import BenchmarkResultStorage

    storage = BenchmarkResultStorage(base_dir="data/processed/benchmarks/results")
    results = storage.load_run("exp_canonical_run_001")
    assert len(results) == 500

    generator = BenchmarkReportGenerator(results)
    aggs_overall = generator.generate_method_aggregates()
    aggs_b128 = generator.generate_method_aggregates(budget=128)

    # ManiGit: B=128 average context is 79.2, aggregate is 179.5
    manigit_b128_ctx = aggs_b128["ManiGit (full)"]["avg_context_tokens"]
    manigit_all_ctx = aggs_overall["ManiGit (full)"]["avg_context_tokens"]
    assert manigit_b128_ctx == 79.2
    assert manigit_all_ctx == 179.5
    assert manigit_b128_ctx <= 128.0
    assert manigit_b128_ctx != manigit_all_ctx

    # Full History: B=128 average context is 109.9, aggregate is 317.3
    fh_b128_ctx = aggs_b128["Full History"]["avg_context_tokens"]
    fh_all_ctx = aggs_overall["Full History"]["avg_context_tokens"]
    assert fh_b128_ctx == 109.9
    assert fh_all_ctx == 317.3
    assert fh_b128_ctx <= 128.0
    assert fh_b128_ctx != fh_all_ctx

    # Ensure format_budget_breakdown_section() includes distinct sections
    breakdown_text = generator.format_budget_breakdown_section()
    assert "### Results at B=128" in breakdown_text
    assert "### Results at B=256" in breakdown_text
    assert "### Results at B=512" in breakdown_text
    assert "### Results at B=1024" in breakdown_text
    assert "### Results at B=2048" in breakdown_text


def test_historical_reconstruction_mutual_exclusion():
    """
    Verifies that in superseding fact scenarios:
    - Current state contains MongoDB and NEVER PostgreSQL.
    - Historical state contains PostgreSQL and NEVER MongoDB.
    - Historical state consumes exactly 18.0 context tokens for ManiGit.
    """
    import json
    raw_path = Path("data/processed/benchmarks/results/exp_canonical_run_001.json")
    trials = json.loads(raw_path.read_text())
    superseding_trials = [
        t for t in trials if "superseding" in t["scenario_id"] and t["method"] == "ManiGit (full)"
    ]
    assert len(superseding_trials) == 10

    for t in superseding_trials:
        ctx_lower = t["compiled_context"].lower()
        if t["config_metadata"].get("is_historical"):
            # Historical query: PostgreSQL must be present, MongoDB must be absent
            assert "postgresql" in ctx_lower, "Historical state must contain PostgreSQL"
            assert "mongodb" not in ctx_lower, "Historical state must not leak MongoDB"
            assert t["metrics"]["context_tokens"] == 18
            assert t["metrics"]["fact_recall"] is True
            assert t["metrics"]["contradiction_accuracy"] is True
        else:
            # Current query: MongoDB must be present, PostgreSQL must be absent
            assert "mongodb" in ctx_lower, "Current state must contain MongoDB"
            assert "postgresql" not in ctx_lower, "Current state must not leak PostgreSQL"
            assert t["metrics"]["context_tokens"] == 51
            assert t["metrics"]["fact_recall"] is True
            assert t["metrics"]["contradiction_accuracy"] is True


