"""
Evaluation metrics calculation engine for ManiGit benchmarks.

Implements:
- Token accounting (context, input, output, total, utilization)
- Important-fact recall & answer correctness
- Historical recovery & contradiction handling accuracy
- Retrieval precision & recall
- Execution latency accounting
"""

from typing import List, Optional, Set, Tuple

from manigit.core.tokens import estimate_tokens
from manigit.evaluation.models import EvaluationMetrics


def calculate_token_metrics(
    context_str: str,
    query_str: str,
    answer_str: str,
    budget: int,
) -> Tuple[int, int, int, int, float]:
    """
    Computes token counts and utilization.
    Returns:
        (context_tokens, input_tokens, output_tokens, total_tokens, context_utilization)
    """
    ctx_tokens = estimate_tokens(context_str) if context_str else 0
    query_tokens = estimate_tokens(query_str) if query_str else 0
    input_tokens = ctx_tokens + query_tokens
    out_tokens = estimate_tokens(answer_str) if answer_str else 0
    total_tokens = input_tokens + out_tokens
    
    utilization = (ctx_tokens / budget) if budget > 0 else 0.0
    return ctx_tokens, input_tokens, out_tokens, total_tokens, min(utilization, 1.0)


def calculate_fact_recall(
    context_str: str,
    expected_answer: str,
    acceptable_alternatives: Optional[List[str]] = None,
) -> bool:
    """
    Evaluates whether the expected fact or any acceptable alternative
    is present in the compiled context.
    """
    if not context_str or not expected_answer:
        return False

    ctx_lower = context_str.lower()
    if expected_answer.lower() in ctx_lower:
        return True

    if acceptable_alternatives:
        for alt in acceptable_alternatives:
            if alt.lower() in ctx_lower:
                return True

    return False


def calculate_answer_correctness(
    actual_answer: str,
    expected_answer: str,
    acceptable_alternatives: Optional[List[str]] = None,
) -> bool:
    """
    Determines whether the generated answer contains the expected answer
    or acceptable alternatives.
    """
    if not actual_answer or not expected_answer:
        return False

    ans_lower = actual_answer.lower()
    if expected_answer.lower() in ans_lower:
        return True

    if acceptable_alternatives:
        for alt in acceptable_alternatives:
            if alt.lower() in ans_lower:
                return True

    return False


def calculate_historical_recovery(
    context_str: str,
    expected_historical_fact: str,
    acceptable_alternatives: Optional[List[str]] = None,
) -> bool:
    """
    Evaluates whether an earlier version of a fact was preserved and recovered
    when historical state was requested.
    """
    return calculate_fact_recall(context_str, expected_historical_fact, acceptable_alternatives)


def calculate_contradiction_accuracy(
    context_str: str,
    expected_fact: str,
    superseded_fact: Optional[str] = None,
    is_historical_query: bool = False,
) -> bool:
    """
    Evaluates whether the context correctly distinguishes active vs superseded facts:
    - If querying current state: expected active fact must be present; superseded fact
      should not be presented as active state.
    - If querying historical state: historical fact must be present.
    """
    if not context_str:
        return False

    ctx_lower = context_str.lower()
    fact_present = expected_fact.lower() in ctx_lower

    if is_historical_query:
        return fact_present

    # Querying current state
    if not fact_present:
        return False

    # If a superseded fact exists, check that it's either omitted or marked superseded/tombstone
    if superseded_fact and superseded_fact.lower() in ctx_lower:
        # If both are present, ensure markers of supersession or tiering exist
        supersession_markers = ["superseded", "tombstone", "migrated", "now", "archived", "v2"]
        has_marker = any(m in ctx_lower for m in supersession_markers)
        return has_marker

    return True


def calculate_retrieval_precision_recall(
    retrieved_indices: List[int],
    relevant_indices: List[int],
) -> Tuple[float, float]:
    """
    Calculates standard retrieval precision and recall over dialogue turn indices.
    Returns:
        (precision, recall)
    """
    retrieved_set: Set[int] = set(retrieved_indices)
    relevant_set: Set[int] = set(relevant_indices)

    if not relevant_set:
        # No relevant items expected
        precision = 1.0 if not retrieved_set else 0.0
        recall = 1.0
        return precision, recall

    if not retrieved_set:
        return 0.0, 0.0

    true_positives = len(retrieved_set.intersection(relevant_set))
    precision = true_positives / len(retrieved_set)
    recall = true_positives / len(relevant_set)

    return precision, recall


def compute_metrics(
    context_str: str,
    query_str: str,
    actual_answer: str,
    expected_answer: str,
    acceptable_alternatives: Optional[List[str]],
    retrieved_indices: List[int],
    relevant_indices: List[int],
    budget: int,
    latency_context_ms: float,
    latency_generation_ms: float,
    is_historical: bool = False,
    superseded_fact: Optional[str] = None,
) -> EvaluationMetrics:
    """
    Aggregates all individual metric calculations into an EvaluationMetrics record.
    """
    ctx_tok, in_tok, out_tok, total_tok, util = calculate_token_metrics(
        context_str=context_str,
        query_str=query_str,
        answer_str=actual_answer,
        budget=budget,
    )

    fact_rec = calculate_fact_recall(
        context_str=context_str,
        expected_answer=expected_answer,
        acceptable_alternatives=acceptable_alternatives,
    )

    ans_corr = calculate_answer_correctness(
        actual_answer=actual_answer,
        expected_answer=expected_answer,
        acceptable_alternatives=acceptable_alternatives,
    )

    prec, rec = calculate_retrieval_precision_recall(
        retrieved_indices=retrieved_indices,
        relevant_indices=relevant_indices,
    )

    hist_rec = None
    if is_historical:
        hist_rec = calculate_historical_recovery(
            context_str=context_str,
            expected_historical_fact=expected_answer,
            acceptable_alternatives=acceptable_alternatives,
        )

    contra_acc = calculate_contradiction_accuracy(
        context_str=context_str,
        expected_fact=expected_answer,
        superseded_fact=superseded_fact,
        is_historical_query=is_historical,
    )

    return EvaluationMetrics(
        context_tokens=ctx_tok,
        input_tokens=in_tok,
        output_tokens=out_tok,
        total_tokens=total_tok,
        context_utilization=round(util, 4),
        fact_recall=fact_rec,
        answer_correctness=ans_corr,
        historical_recall=hist_rec,
        contradiction_accuracy=contra_acc,
        retrieval_precision=round(prec, 4),
        retrieval_recall=round(rec, 4),
        latency_context_ms=round(latency_context_ms, 2),
        latency_generation_ms=round(latency_generation_ms, 2),
        latency_total_ms=round(latency_context_ms + latency_generation_ms, 2),
    )
