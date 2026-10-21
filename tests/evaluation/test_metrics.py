"""
Unit tests for evaluation metrics calculations and edge cases.
"""

import pytest

from manigit.evaluation.metrics import (
    calculate_answer_correctness,
    calculate_contradiction_accuracy,
    calculate_fact_recall,
    calculate_historical_recovery,
    calculate_retrieval_precision_recall,
    calculate_token_metrics,
    compute_metrics,
)


def test_calculate_token_metrics():
    ctx = "The backend database is PostgreSQL."
    query = "What database are we using?"
    answer = "The database is PostgreSQL."
    budget = 100

    ctx_tok, in_tok, out_tok, total_tok, util = calculate_token_metrics(
        context_str=ctx,
        query_str=query,
        answer_str=answer,
        budget=budget,
    )

    assert ctx_tok > 0
    assert in_tok > ctx_tok
    assert out_tok > 0
    assert total_tok == in_tok + out_tok
    assert 0.0 < util <= 1.0

    # Zero budget edge case
    _, _, _, _, util_zero = calculate_token_metrics(ctx, query, answer, budget=0)
    assert util_zero == 0.0


def test_calculate_fact_recall():
    ctx = "Our API timeout constraint is 500 ms for all endpoints."
    
    # Exact match
    assert calculate_fact_recall(ctx, "500 ms") is True
    # Case insensitivity
    assert calculate_fact_recall(ctx, "500 MS") is True
    # Alternative match
    assert calculate_fact_recall(ctx, "1000 ms", acceptable_alternatives=["500 ms"]) is True
    # Missing fact
    assert calculate_fact_recall(ctx, "MongoDB") is False
    # Empty inputs
    assert calculate_fact_recall("", "500 ms") is False
    assert calculate_fact_recall(ctx, "") is False


def test_calculate_answer_correctness():
    # Direct inclusion
    assert calculate_answer_correctness("The answer is PostgreSQL.", "PostgreSQL") is True
    # Alternative
    assert calculate_answer_correctness("Configured with postgres.", "PostgreSQL", acceptable_alternatives=["postgres"]) is True
    # Missing
    assert calculate_answer_correctness("I do not know.", "PostgreSQL") is False
    # Empty
    assert calculate_answer_correctness("", "PostgreSQL") is False


def test_calculate_historical_recovery():
    ctx_historical = "Historical configuration: Database was PostgreSQL prior to migration."
    ctx_current_only = "Active database is MongoDB."

    assert calculate_historical_recovery(ctx_historical, "PostgreSQL") is True
    assert calculate_historical_recovery(ctx_current_only, "PostgreSQL") is False


def test_calculate_contradiction_accuracy():
    # Scenario: current query for MongoDB
    ctx_correct = "Active database: MongoDB. Note: PostgreSQL was superseded."
    assert calculate_contradiction_accuracy(
        context_str=ctx_correct,
        expected_fact="MongoDB",
        superseded_fact="PostgreSQL",
        is_historical_query=False,
    ) is True

    # Scenario: historical query for PostgreSQL
    assert calculate_contradiction_accuracy(
        context_str=ctx_correct,
        expected_fact="PostgreSQL",
        superseded_fact="MongoDB",
        is_historical_query=True,
    ) is True

    # Scenario: current query missing expected fact
    assert calculate_contradiction_accuracy(
        context_str="Only distractor context here.",
        expected_fact="MongoDB",
        superseded_fact="PostgreSQL",
        is_historical_query=False,
    ) is False


def test_calculate_retrieval_precision_recall_edge_cases():
    # Perfect precision & recall
    prec, rec = calculate_retrieval_precision_recall([0, 1], [0, 1])
    assert prec == 1.0
    assert rec == 1.0

    # Zero recall (disjoint sets)
    prec, rec = calculate_retrieval_precision_recall([2, 3], [0, 1])
    assert prec == 0.0
    assert rec == 0.0

    # Partial overlap
    # Retrieved 0, 1, 2; Relevant 1, 3
    # TP = {1} -> precision = 1/3, recall = 1/2
    prec, rec = calculate_retrieval_precision_recall([0, 1, 2], [1, 3])
    assert pytest.approx(prec, 0.01) == 1 / 3
    assert pytest.approx(rec, 0.01) == 1 / 2

    # Zero retrieved items
    prec, rec = calculate_retrieval_precision_recall([], [0, 1])
    assert prec == 0.0
    assert rec == 0.0

    # Zero relevant items
    prec, rec = calculate_retrieval_precision_recall([], [])
    assert prec == 1.0
    assert rec == 1.0

    prec, rec = calculate_retrieval_precision_recall([1, 2], [])
    assert prec == 0.0
    assert rec == 1.0


def test_compute_metrics_integration():
    metrics = compute_metrics(
        context_str="The backend database is PostgreSQL.",
        query_str="What database?",
        actual_answer="PostgreSQL",
        expected_answer="PostgreSQL",
        acceptable_alternatives=["postgres"],
        retrieved_indices=[0, 1],
        relevant_indices=[0, 1],
        budget=256,
        latency_context_ms=1.5,
        latency_generation_ms=10.0,
    )

    assert metrics.fact_recall is True
    assert metrics.answer_correctness is True
    assert metrics.retrieval_precision == 1.0
    assert metrics.retrieval_recall == 1.0
    assert metrics.latency_total_ms == 11.5
    assert metrics.context_tokens > 0
