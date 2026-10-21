"""
Figure generation and extraction engine for ManiGit paper-ready figures.

Generates machine-readable figure data (JSON and CSV) strictly from raw trial records:
- Figure 1: Average context tokens vs token budget
- Figure 2: Fact recall vs token budget
- Figure 3: Answer correctness vs token budget
- Figure 4: Historical recovery comparison across methods
- Figure 5: Contradiction handling accuracy comparison across methods
- Figure 6: Ablation degradation deltas relative to ManiGit Full
- Figure 7: Context efficiency vs answer correctness Pareto trade-off
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from manigit.evaluation.models import BenchmarkResult
from manigit.evaluation.statistics import (
    compute_continuous_stats,
    compute_paired_comparison,
    wilson_score_interval,
)


class FigureDataGenerator:
    """
    Extracts and serializes paper-ready figure datasets from raw experiment results.
    """

    def __init__(self, output_dir: str = "data/processed/benchmarks/figures"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_all_figures(
        self,
        results: List[BenchmarkResult],
    ) -> Dict[str, Any]:
        """
        Generates and saves all 7 paper figures in JSON and CSV formats.
        """
        fig1 = self.generate_fig1_context_vs_budget(results)
        fig2 = self.generate_fig2_fact_recall_vs_budget(results)
        fig3 = self.generate_fig3_correctness_vs_budget(results)
        fig4 = self.generate_fig4_historical_recovery(results)
        fig5 = self.generate_fig5_contradiction_handling(results)
        fig6 = self.generate_fig6_ablation_degradation(results)
        fig7 = self.generate_fig7_efficiency_tradeoff(results)

        figures = {
            "fig1_context_vs_budget": fig1,
            "fig2_fact_recall_vs_budget": fig2,
            "fig3_correctness_vs_budget": fig3,
            "fig4_historical_recovery": fig4,
            "fig5_contradiction_handling": fig5,
            "fig6_ablation_degradation": fig6,
            "fig7_efficiency_tradeoff": fig7,
        }

        # Save index file
        index_path = self.output_dir / "figures_index.json"
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump({k: len(v) if isinstance(v, list) else v for k, v in figures.items()}, f, indent=2)

        return figures

    def _save_json_and_csv(self, filename_base: str, data: List[Dict[str, Any]]) -> None:
        """Helper to save a dataset as both JSON and CSV."""
        json_path = self.output_dir / f"{filename_base}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        if data:
            csv_path = self.output_dir / f"{filename_base}.csv"
            keys = list(data[0].keys())
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(data)

    def generate_fig1_context_vs_budget(self, results: List[BenchmarkResult]) -> List[Dict[str, Any]]:
        """Figure 1: Average context tokens vs token budget across all methods/ablations."""
        methods = sorted(list(set(r.method for r in results)))
        budgets = sorted(list(set(r.budget for r in results)))

        data = []
        for budget in budgets:
            row: Dict[str, Any] = {"budget": budget}
            for m in methods:
                m_trials = [r for r in results if r.method == m and r.budget == budget]
                if m_trials:
                    ctx_stats = compute_continuous_stats([r.metrics.context_tokens for r in m_trials])
                    row[f"{m}_mean"] = ctx_stats["mean"]
                    row[f"{m}_std"] = ctx_stats["std"]
                else:
                    row[f"{m}_mean"] = 0.0
                    row[f"{m}_std"] = 0.0
            data.append(row)

        self._save_json_and_csv("fig1_context_vs_budget", data)
        return data

    def generate_fig2_fact_recall_vs_budget(self, results: List[BenchmarkResult]) -> List[Dict[str, Any]]:
        """Figure 2: Fact recall vs budget with Wilson 95% CI."""
        methods = sorted(list(set(r.method for r in results)))
        budgets = sorted(list(set(r.budget for r in results)))

        data = []
        for budget in budgets:
            row: Dict[str, Any] = {"budget": budget}
            for m in methods:
                m_trials = [r for r in results if r.method == m and r.budget == budget]
                if m_trials:
                    successes = sum(1 for r in m_trials if r.metrics.fact_recall)
                    p, lower, upper = wilson_score_interval(successes, len(m_trials))
                    row[f"{m}_recall"] = p
                    row[f"{m}_ci_lower"] = lower
                    row[f"{m}_ci_upper"] = upper
                else:
                    row[f"{m}_recall"] = 0.0
                    row[f"{m}_ci_lower"] = 0.0
                    row[f"{m}_ci_upper"] = 0.0
            data.append(row)

        self._save_json_and_csv("fig2_fact_recall_vs_budget", data)
        return data

    def generate_fig3_correctness_vs_budget(self, results: List[BenchmarkResult]) -> List[Dict[str, Any]]:
        """Figure 3: Answer correctness vs budget with Wilson 95% CI."""
        methods = sorted(list(set(r.method for r in results)))
        budgets = sorted(list(set(r.budget for r in results)))

        data = []
        for budget in budgets:
            row: Dict[str, Any] = {"budget": budget}
            for m in methods:
                m_trials = [r for r in results if r.method == m and r.budget == budget]
                if m_trials:
                    successes = sum(1 for r in m_trials if r.metrics.answer_correctness)
                    p, lower, upper = wilson_score_interval(successes, len(m_trials))
                    row[f"{m}_correctness"] = p
                    row[f"{m}_ci_lower"] = lower
                    row[f"{m}_ci_upper"] = upper
                else:
                    row[f"{m}_correctness"] = 0.0
                    row[f"{m}_ci_lower"] = 0.0
                    row[f"{m}_ci_upper"] = 0.0
            data.append(row)

        self._save_json_and_csv("fig3_correctness_vs_budget", data)
        return data

    def generate_fig4_historical_recovery(self, results: List[BenchmarkResult]) -> List[Dict[str, Any]]:
        """Figure 4: Historical recovery accuracy across methods."""
        methods = sorted(list(set(r.method for r in results)))
        data = []
        for m in methods:
            hist_trials = [r for r in results if r.method == m and r.metrics.historical_recall is not None]
            if hist_trials:
                successes = sum(1 for r in hist_trials if r.metrics.historical_recall)
                p, lower, upper = wilson_score_interval(successes, len(hist_trials))
                data.append({
                    "method": m,
                    "historical_recovery_rate": p,
                    "ci_lower": lower,
                    "ci_upper": upper,
                    "total_trials": len(hist_trials),
                })
        self._save_json_and_csv("fig4_historical_recovery", data)
        return data

    def generate_fig5_contradiction_handling(self, results: List[BenchmarkResult]) -> List[Dict[str, Any]]:
        """Figure 5: Contradiction handling accuracy across methods."""
        methods = sorted(list(set(r.method for r in results)))
        data = []
        for m in methods:
            contra_trials = [r for r in results if r.method == m and r.metrics.contradiction_accuracy is not None]
            if contra_trials:
                successes = sum(1 for r in contra_trials if r.metrics.contradiction_accuracy)
                p, lower, upper = wilson_score_interval(successes, len(contra_trials))
                data.append({
                    "method": m,
                    "contradiction_accuracy": p,
                    "ci_lower": lower,
                    "ci_upper": upper,
                    "total_trials": len(contra_trials),
                })
        self._save_json_and_csv("fig5_contradiction_handling", data)
        return data

    def generate_fig6_ablation_degradation(self, results: List[BenchmarkResult]) -> List[Dict[str, Any]]:
        """Figure 6: Degradation metrics of ablations relative to ManiGit Full."""
        baseline_trials = [r for r in results if r.method == "ManiGit (full)"]
        ablation_names = [
            "ManiGit (no_contradiction)",
            "ManiGit (no_confidence)",
            "ManiGit (no_tier)",
        ]

        data = []
        for ab_name in ablation_names:
            ab_trials = [r for r in results if r.method == ab_name]
            if not ab_trials or not baseline_trials:
                continue

            paired_recall = compute_paired_comparison(
                baseline_trials, ab_trials, lambda t: 1.0 if t.metrics.fact_recall else 0.0
            )
            paired_acc = compute_paired_comparison(
                baseline_trials, ab_trials, lambda t: 1.0 if t.metrics.answer_correctness else 0.0
            )
            paired_ctx = compute_paired_comparison(
                baseline_trials, ab_trials, lambda t: float(t.metrics.context_tokens)
            )

            # Contradiction pairing
            base_contra = [t for t in baseline_trials if t.metrics.contradiction_accuracy is not None]
            ab_contra = [t for t in ab_trials if t.metrics.contradiction_accuracy is not None]
            paired_contra = compute_paired_comparison(
                base_contra, ab_contra, lambda t: 1.0 if t.metrics.contradiction_accuracy else 0.0
            )

            data.append({
                "ablation": ab_name,
                "fact_recall_delta": paired_recall["mean_delta"],
                "answer_correctness_delta": paired_acc["mean_delta"],
                "context_token_delta": paired_ctx["mean_delta"],
                "contradiction_accuracy_delta": paired_contra["mean_delta"],
                "degraded_trials_count": paired_acc["degraded"],
                "total_pairs_evaluated": paired_acc["pairs_evaluated"],
            })

        self._save_json_and_csv("fig6_ablation_degradation", data)
        return data

    def generate_fig7_efficiency_tradeoff(self, results: List[BenchmarkResult]) -> List[Dict[str, Any]]:
        """Figure 7: Context tokens vs Answer correctness trade-off curve across all methods."""
        methods = sorted(list(set(r.method for r in results)))
        data = []
        for m in methods:
            m_trials = [r for r in results if r.method == m]
            if m_trials:
                ctx_stats = compute_continuous_stats([r.metrics.context_tokens for r in m_trials])
                successes = sum(1 for r in m_trials if r.metrics.answer_correctness)
                p, lower, upper = wilson_score_interval(successes, len(m_trials))
                data.append({
                    "method": m,
                    "avg_context_tokens": ctx_stats["mean"],
                    "std_context_tokens": ctx_stats["std"],
                    "answer_correctness": p,
                    "ci_lower": lower,
                    "ci_upper": upper,
                    "trials_count": len(m_trials),
                })
        self._save_json_and_csv("fig7_efficiency_tradeoff", data)
        return data
