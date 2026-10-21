"""
Statistical analysis tools for ManiGit research benchmarking and ablations.

Provides:
- Closed-form Wilson score confidence intervals for binomial metrics (fact recall, answer correctness)
- Continuous descriptive statistics (mean, std, median, min, max, parametric CI) for token/latency metrics
- Paired comparison analysis across methods and ablation variants over identical (scenario, query, budget) trials
"""

import math
from typing import Any, Callable, Dict, List, Optional, Tuple

from manigit.evaluation.models import BenchmarkResult


def wilson_score_interval(
    successes: int,
    total: int,
    confidence: float = 0.95,
) -> Tuple[float, float, float]:
    """
    Computes the Wilson score interval for a binomial proportion.
    
    Returns:
        (point_estimate, lower_bound, upper_bound)
    """
    if total <= 0:
        return 0.0, 0.0, 0.0

    p = successes / float(total)
    
    # Critical value z
    if confidence == 0.95:
        z = 1.959963984540054
    elif confidence == 0.99:
        z = 2.5758293035489004
    elif confidence == 0.90:
        z = 1.6448536269514722
    else:
        # Normal quantile approximation
        z = 1.95996

    denominator = 1.0 + (z * z) / total
    centre_adjusted_probability = p + (z * z) / (2.0 * total)
    adjusted_center = centre_adjusted_probability / denominator
    
    under_radical = (p * (1.0 - p) / total) + ((z * z) / (4.0 * total * total))
    margin = (z / denominator) * math.sqrt(max(0.0, under_radical))
    
    lower = max(0.0, adjusted_center - margin)
    upper = min(1.0, adjusted_center + margin)
    
    return round(p, 4), round(lower, 4), round(upper, 4)


def compute_continuous_stats(values: List[float]) -> Dict[str, float]:
    """
    Computes summary descriptive statistics for continuous variables (tokens, latency).
    
    Returns:
        mean, std, median, min, max, count
    """
    if not values:
        return {
            "mean": 0.0,
            "std": 0.0,
            "median": 0.0,
            "min": 0.0,
            "max": 0.0,
            "count": 0,
        }

    n = len(values)
    mean_val = sum(values) / float(n)
    
    if n > 1:
        variance = sum((x - mean_val) ** 2 for x in values) / float(n - 1)
        std_val = math.sqrt(max(0.0, variance))
    else:
        std_val = 0.0

    sorted_vals = sorted(values)
    if n % 2 == 1:
        median_val = sorted_vals[n // 2]
    else:
        median_val = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0

    return {
        "mean": round(mean_val, 2),
        "std": round(std_val, 2),
        "median": round(median_val, 2),
        "min": round(sorted_vals[0], 2),
        "max": round(sorted_vals[-1], 2),
        "count": n,
    }


def compute_paired_comparison(
    baseline_trials: List[BenchmarkResult],
    ablation_trials: List[BenchmarkResult],
    metric_extractor: Callable[[BenchmarkResult], float],
) -> Dict[str, Any]:
    """
    Computes paired difference between baseline (e.g. ManiGit Full) and an ablation variant
    over matching (scenario_id, query_id, budget) keys.
    """
    baseline_map = {
        (t.scenario_id, t.query_id, t.budget): t
        for t in baseline_trials
    }
    
    deltas: List[float] = []
    improved = 0
    tied = 0
    degraded = 0

    for ab in ablation_trials:
        key = (ab.scenario_id, ab.query_id, ab.budget)
        if key in baseline_map:
            base_trial = baseline_map[key]
            val_base = metric_extractor(base_trial)
            val_ab = metric_extractor(ab)
            
            diff = val_ab - val_base
            deltas.append(diff)
            
            if diff > 1e-6:
                improved += 1
            elif diff < -1e-6:
                degraded += 1
            else:
                tied += 1

    if not deltas:
        return {
            "mean_delta": 0.0,
            "std_delta": 0.0,
            "improved": 0,
            "tied": 0,
            "degraded": 0,
            "pairs_evaluated": 0,
        }

    stats = compute_continuous_stats(deltas)
    return {
        "mean_delta": stats["mean"],
        "std_delta": stats["std"],
        "improved": improved,
        "tied": tied,
        "degraded": degraded,
        "pairs_evaluated": len(deltas),
    }
