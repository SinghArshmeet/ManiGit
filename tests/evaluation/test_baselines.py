"""
Unit tests for evaluation baseline implementations and ablation modes.
"""

import pytest

from manigit.core.tokens import estimate_tokens
from manigit.evaluation.baselines import (
    FullHistoryBaseline,
    ManiGitEvaluationMethod,
    RAGStyleBaseline,
    SlidingWindowBaseline,
    SummaryBaseline,
)
from manigit.evaluation.models import AblationMode, BenchmarkQuery
from manigit.evaluation.scenarios import (
    create_exact_constraints_scenario,
    create_stable_facts_scenario,
    create_superseding_facts_scenario,
)
from manigit.models.mock import MockModelAdapter


def test_full_history_baseline():
    sc = create_stable_facts_scenario()
    model = MockModelAdapter()
    baseline = FullHistoryBaseline()
    baseline.setup(sc, model)

    query = sc.queries[0]
    # Very small budget: only first turns fit
    ctx_small, indices_small = baseline.compile_context(query, budget=30)
    assert len(indices_small) < len(sc.turns)
    assert estimate_tokens(ctx_small) <= 30

    # Large budget: all turns fit
    ctx_large, indices_large = baseline.compile_context(query, budget=2048)
    assert len(indices_large) == len(sc.turns)
    assert "PostgreSQL" in ctx_large


def test_sliding_window_baseline():
    sc = create_stable_facts_scenario()
    model = MockModelAdapter()
    # Window of 2 messages (only turns 6 and 7)
    baseline = SlidingWindowBaseline(window_size=2)
    baseline.setup(sc, model)

    query = sc.queries[0]
    ctx, indices = baseline.compile_context(query, budget=500)
    # The early fact in turn 0 should be lost from sliding window
    assert 0 not in indices
    assert "PostgreSQL" not in ctx
    assert 6 in indices or 7 in indices


def test_summary_baseline():
    sc = create_exact_constraints_scenario()
    model = MockModelAdapter()
    baseline = SummaryBaseline()
    baseline.setup(sc, model)

    query = sc.queries[0]
    ctx, indices = baseline.compile_context(query, budget=500)
    assert "500 ms" in ctx
    assert estimate_tokens(ctx) <= 500


def test_rag_style_baseline():
    sc = create_stable_facts_scenario()
    model = MockModelAdapter()
    baseline = RAGStyleBaseline()
    baseline.setup(sc, model)

    # Query specifically matches PostgreSQL database turn
    query = sc.queries[0]  # "What database are we using?"
    ctx, indices = baseline.compile_context(query, budget=100)
    assert "PostgreSQL" in ctx
    assert 0 in indices or 1 in indices


def test_manigit_evaluation_method_stable():
    sc = create_stable_facts_scenario()
    model = MockModelAdapter()
    baseline = ManiGitEvaluationMethod()
    baseline.setup(sc, model)

    query = sc.queries[0]
    ctx, indices = baseline.compile_context(query, budget=512)
    assert "PostgreSQL" in ctx
    assert estimate_tokens(ctx) <= 512


def test_manigit_evaluation_method_superseding():
    sc = create_superseding_facts_scenario()
    model = MockModelAdapter()
    baseline = ManiGitEvaluationMethod()
    baseline.setup(sc, model)

    # Current query
    curr_q = next(q for q in sc.queries if not q.is_historical)
    ctx_curr, _ = baseline.compile_context(curr_q, budget=512)
    assert "MongoDB" in ctx_curr
    assert "PostgreSQL" not in ctx_curr

    # Historical query (queries commit before migration)
    hist_q = next(q for q in sc.queries if q.is_historical)
    ctx_hist, _ = baseline.compile_context(hist_q, budget=512)
    assert "PostgreSQL" in ctx_hist
    assert "MongoDB" not in ctx_hist


def test_manigit_ablation_modes():
    sc = create_stable_facts_scenario()
    model = MockModelAdapter()

    # Test all ablation modes instantiate and compile cleanly
    for mode in [
        AblationMode.FULL,
        AblationMode.RETRIEVAL_ONLY,
        AblationMode.RETRIEVAL_TIERING,
        AblationMode.RETRIEVAL_TIERING_CONFIDENCE,
    ]:
        method = ManiGitEvaluationMethod(ablation_mode=mode)
        method.setup(sc, model)
        ctx, _ = method.compile_context(sc.queries[0], budget=512)
        assert len(ctx) > 0
