"""
Report generation engine for ManiGit research benchmarking.

Generates structured Markdown research tables consuming actual trial records:
A. Per-scenario comparison table
B. Method-level aggregate metrics
C. Token efficiency comparison
D. Historical recall comparison
E. Contradiction handling comparison
F. Budget-vs-recall relationship
G. Conversation-length-vs-token-usage relationship
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

from manigit.evaluation.models import BenchmarkResult


class BenchmarkReportGenerator:
    """
    Consumes empirical trial results to synthesize rigorous research reports.
    Never invents, fabricates, or interpolates artificial metrics.
    """

    def __init__(self, results: List[BenchmarkResult]):
        self.results = results

    def generate_method_aggregates(self, budget: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """Computes high-level performance metrics per evaluation method, optionally filtered by budget."""
        target_results = [r for r in self.results if r.budget == budget] if budget is not None else self.results
        groups: Dict[str, List[BenchmarkResult]] = defaultdict(list)
        for r in target_results:
            groups[r.method].append(r)

        aggregates: Dict[str, Dict[str, Any]] = {}
        for method, res_list in sorted(groups.items()):
            n = len(res_list)
            if n == 0:
                continue

            fact_recall_count = sum(1 for r in res_list if r.metrics.fact_recall)
            ans_correct_count = sum(1 for r in res_list if r.metrics.answer_correctness)
            avg_ctx_tokens = sum(r.metrics.context_tokens for r in res_list) / n
            avg_total_tokens = sum(r.metrics.total_tokens for r in res_list) / n
            avg_util = sum(r.metrics.context_utilization for r in res_list) / n
            avg_precision = sum(r.metrics.retrieval_precision for r in res_list) / n
            avg_recall = sum(r.metrics.retrieval_recall for r in res_list) / n
            avg_lat_ctx = sum(r.metrics.latency_context_ms for r in res_list) / n
            avg_lat_total = sum(r.metrics.latency_total_ms for r in res_list) / n

            # Historical queries subset
            hist_res = [r for r in res_list if r.config_metadata.get("is_historical")]
            hist_recall = (sum(1 for r in hist_res if r.metrics.fact_recall) / len(hist_res)) if hist_res else None

            aggregates[method] = {
                "trials": n,
                "fact_recall_rate": round(fact_recall_count / n, 4),
                "answer_correctness_rate": round(ans_correct_count / n, 4),
                "historical_recall_rate": round(hist_recall, 4) if hist_recall is not None else "N/A",
                "avg_context_tokens": round(avg_ctx_tokens, 1),
                "avg_total_tokens": round(avg_total_tokens, 1),
                "avg_context_utilization": round(avg_util, 4),
                "avg_precision": round(avg_precision, 4),
                "avg_recall": round(avg_recall, 4),
                "avg_latency_context_ms": round(avg_lat_ctx, 2),
                "avg_latency_total_ms": round(avg_lat_total, 2),
            }

        return aggregates

    def format_method_aggregates_table(self, budget: Optional[int] = None) -> str:
        """Markdown table for method-level metrics, optionally filtered for a specific budget."""
        aggs = self.generate_method_aggregates(budget=budget)
        lines = [
            "| Method | Trials | Fact Recall | Ans Correct | Hist Recall | Avg Ctx Tok | Avg Total Tok | Precision | Latency Ctx (ms) |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
        for m, d in aggs.items():
            hist_str = f"{d['historical_recall_rate'] * 100:.1f}%" if isinstance(d['historical_recall_rate'], float) else d['historical_recall_rate']
            lines.append(
                f"| **{m}** | {d['trials']} | {d['fact_recall_rate'] * 100:.1f}% | "
                f"{d['answer_correctness_rate'] * 100:.1f}% | {hist_str} | "
                f"{d['avg_context_tokens']} | {d['avg_total_tokens']} | "
                f"{d['avg_precision']:.3f} | {d['avg_latency_context_ms']} |"
            )
        return "\n".join(lines)

    def format_budget_breakdown_section(self) -> str:
        """Markdown sections breaking down method performance for each distinct evaluated budget."""
        budgets = sorted(set(r.budget for r in self.results))
        sections = []
        for b in budgets:
            sections.append(f"### Results at B={b}")
            sections.append(f"*Evaluation constrained to maximum context budget B={b} tokens.*")
            sections.append("")
            sections.append(self.format_method_aggregates_table(budget=b))
            sections.append("")
        return "\n".join(sections)

    def format_scenario_comparison_table(self) -> str:
        """Markdown table breaking down accuracy and context tokens per scenario."""
        groups: Dict[Tuple[str, str], List[BenchmarkResult]] = defaultdict(list)
        for r in self.results:
            groups[(r.scenario_id, r.method)].append(r)

        lines = [
            "| Scenario | Method | Fact Recall | Ans Correct | Avg Ctx Tokens | Avg Precision |",
            "| :--- | :--- | :---: | :---: | :---: | :---: |",
        ]
        for (sc_id, method), res_list in sorted(groups.items()):
            n = len(res_list)
            rec = sum(1 for r in res_list if r.metrics.fact_recall) / n
            corr = sum(1 for r in res_list if r.metrics.answer_correctness) / n
            ctx = sum(r.metrics.context_tokens for r in res_list) / n
            prec = sum(r.metrics.retrieval_precision for r in res_list) / n
            lines.append(
                f"| `{sc_id}` | {method} | {rec * 100:.1f}% | {corr * 100:.1f}% | {ctx:.1f} | {prec:.3f} |"
            )
        return "\n".join(lines)

    def format_historical_recall_table(self) -> str:
        """Markdown table comparing historical recovery of superseded facts."""
        hist_results = [r for r in self.results if r.config_metadata.get("is_historical")]
        if not hist_results:
            return "No historical queries present in current experiment dataset."

        groups: Dict[str, List[BenchmarkResult]] = defaultdict(list)
        for r in hist_results:
            groups[r.method].append(r)

        lines = [
            "| Method | Historical Trials | Historical Recall | Answer Correct | Avg Context Tokens |",
            "| :--- | :---: | :---: | :---: | :---: |",
        ]
        for method, res_list in sorted(groups.items()):
            n = len(res_list)
            rec = sum(1 for r in res_list if r.metrics.fact_recall) / n
            corr = sum(1 for r in res_list if r.metrics.answer_correctness) / n
            ctx = sum(r.metrics.context_tokens for r in res_list) / n
            lines.append(
                f"| **{method}** | {n} | {rec * 100:.1f}% | {corr * 100:.1f}% | {ctx:.1f} |"
            )
        return "\n".join(lines)

    def format_contradiction_handling_table(self) -> str:
        """Markdown table comparing contradiction handling accuracy on superseding facts."""
        superseding_results = [r for r in self.results if "superseding" in r.scenario_id]
        if not superseding_results:
            return "No superseding fact scenarios present in current dataset."

        groups: Dict[str, List[BenchmarkResult]] = defaultdict(list)
        for r in superseding_results:
            groups[r.method].append(r)

        lines = [
            "| Method | Trials | Contradiction Accuracy | Current Fact Accuracy | Historical Fact Accuracy |",
            "| :--- | :---: | :---: | :---: | :---: |",
        ]
        for method, res_list in sorted(groups.items()):
            n = len(res_list)
            contra_acc = sum(1 for r in res_list if r.metrics.contradiction_accuracy) / n
            current_trials = [r for r in res_list if not r.config_metadata.get("is_historical")]
            curr_acc = (sum(1 for r in current_trials if r.metrics.fact_recall) / len(current_trials)) if current_trials else 0.0
            hist_trials = [r for r in res_list if r.config_metadata.get("is_historical")]
            hist_acc = (sum(1 for r in hist_trials if r.metrics.fact_recall) / len(hist_trials)) if hist_trials else 0.0

            lines.append(
                f"| **{method}** | {n} | {contra_acc * 100:.1f}% | {curr_acc * 100:.1f}% | {hist_acc * 100:.1f}% |"
            )
        return "\n".join(lines)

    def format_budget_vs_recall_table(self) -> str:
        """Markdown table showing Recall vs Context Budget."""
        groups: Dict[Tuple[int, str], List[BenchmarkResult]] = defaultdict(list)
        budgets: Set[int] = set()
        methods: Set[str] = set()

        for r in self.results:
            groups[(r.budget, r.method)].append(r)
            budgets.add(r.budget)
            methods.add(r.method)

        sorted_budgets = sorted(budgets)
        sorted_methods = sorted(methods)

        header = ["| Budget (Tokens) |"] + [f" {m} |" for m in sorted_methods]
        separator = ["| :---: |"] + [":---: |" for _ in sorted_methods]
        lines = ["".join(header), "".join(separator)]

        for b in sorted_budgets:
            row = [f"| **{b}** |"]
            for m in sorted_methods:
                res_list = groups.get((b, m), [])
                if res_list:
                    rec = sum(1 for r in res_list if r.metrics.fact_recall) / len(res_list)
                    row.append(f" {rec * 100:.1f}% |")
                else:
                    row.append(" N/A |")
            lines.append("".join(row))

        return "\n".join(lines)

    def format_conversation_length_vs_tokens_table(self) -> str:
        """Markdown table showing Context Token Consumption vs Conversation Length."""
        groups: Dict[Tuple[int, str], List[BenchmarkResult]] = defaultdict(list)
        lengths: Set[int] = set()
        methods: Set[str] = set()

        for r in self.results:
            groups[(r.conversation_length, r.method)].append(r)
            lengths.add(r.conversation_length)
            methods.add(r.method)

        sorted_lengths = sorted(lengths)
        sorted_methods = sorted(methods)

        header = ["| Turns |"] + [f" {m} |" for m in sorted_methods]
        separator = ["| :---: |"] + [":---: |" for _ in sorted_methods]
        lines = ["".join(header), "".join(separator)]

        for length in sorted_lengths:
            row = [f"| **{length}** |"]
            for m in sorted_methods:
                res_list = groups.get((length, m), [])
                if res_list:
                    ctx = sum(r.metrics.context_tokens for r in res_list) / len(res_list)
                    row.append(f" {ctx:.1f} |")
                else:
                    row.append(" N/A |")
            lines.append("".join(row))

        return "\n".join(lines)

    def format_table_1_overall_comparison(self) -> str:
        """
        Table 1: Overall comparative performance across all 8 evaluation methods/variants.
        Columns: Method, Fact Recall (with 95% CI), Answer Correctness, Historical Recovery,
        Avg Context Tokens, Avg Total Tokens, Retrieval Precision, Retrieval Recall, Latency Total (ms).
        """
        methods = sorted(list(set(r.method for r in self.results)))
        lines = [
            "| Method | Fact Recall (95% CI) | Answer Correctness | Historical Recovery | Avg Context Tokens | Avg Total Tokens | Retrieval Prec | Retrieval Recall | Latency Total (ms) |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]

        from manigit.evaluation.statistics import compute_continuous_stats, wilson_score_interval

        for m in methods:
            m_trials = [r for r in self.results if r.method == m]
            n = len(m_trials)
            if n == 0:
                continue

            # Fact Recall with Wilson CI
            recall_succ = sum(1 for r in m_trials if r.metrics.fact_recall)
            r_p, r_low, r_high = wilson_score_interval(recall_succ, n)
            recall_str = f"{r_p * 100:.1f}% [{r_low * 100:.1f}%, {r_high * 100:.1f}%]"

            # Answer Correctness
            ans_succ = sum(1 for r in m_trials if r.metrics.answer_correctness)
            a_p, _, _ = wilson_score_interval(ans_succ, n)
            ans_str = f"{a_p * 100:.1f}%"

            # Historical Recovery
            hist_trials = [r for r in m_trials if r.metrics.historical_recall is not None]
            if hist_trials:
                h_succ = sum(1 for r in hist_trials if r.metrics.historical_recall)
                h_p, _, _ = wilson_score_interval(h_succ, len(hist_trials))
                hist_str = f"{h_p * 100:.1f}%"
            else:
                hist_str = "N/A"

            # Continuous stats
            ctx_stats = compute_continuous_stats([r.metrics.context_tokens for r in m_trials])
            tot_stats = compute_continuous_stats([r.metrics.total_tokens for r in m_trials])
            prec_stats = compute_continuous_stats([r.metrics.retrieval_precision for r in m_trials])
            rec_stats = compute_continuous_stats([r.metrics.retrieval_recall for r in m_trials])
            lat_stats = compute_continuous_stats([r.metrics.latency_total_ms for r in m_trials])

            lines.append(
                f"| **{m}** | {recall_str} | {ans_str} | {hist_str} | "
                f"{ctx_stats['mean']:.1f} ± {ctx_stats['std']:.1f} | {tot_stats['mean']:.1f} | "
                f"{prec_stats['mean']:.3f} | {rec_stats['mean']:.3f} | {lat_stats['mean']:.2f} |"
            )

        return "\n".join(lines)

    def format_table_2_ablation_degradation(self) -> str:
        """
        Table 2: Ablation degradation relative to ManiGit Full.
        Quantifies the contribution of individual mechanisms via paired differences.
        """
        from manigit.evaluation.statistics import compute_paired_comparison

        baseline_trials = [r for r in self.results if r.method == "ManiGit (full)"]
        ablation_names = [
            ("ManiGit (full)", "Reference condition"),
            ("ManiGit (no_contradiction)", "Without contradiction/supersession"),
            ("ManiGit (no_confidence)", "Without confidence-aware classification"),
            ("ManiGit (no_tier)", "Without tier-aware context selection"),
        ]

        lines = [
            "| Experimental Condition | Mechanism Description | Fact Recall Δ | Answer Correctness Δ | Historical Recovery Δ | Context Token Δ | Contradiction Acc Δ |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: |",
        ]

        for ab_name, desc in ablation_names:
            if ab_name == "ManiGit (full)":
                lines.append(f"| **{ab_name}** | {desc} | 0.0% (Ref) | 0.0% (Ref) | 0.0% (Ref) | 0.0 (Ref) | 0.0% (Ref) |")
                continue

            ab_trials = [r for r in self.results if r.method == ab_name]
            if not ab_trials or not baseline_trials:
                continue

            p_recall = compute_paired_comparison(
                baseline_trials, ab_trials, lambda t: 1.0 if t.metrics.fact_recall else 0.0
            )
            p_ans = compute_paired_comparison(
                baseline_trials, ab_trials, lambda t: 1.0 if t.metrics.answer_correctness else 0.0
            )
            p_ctx = compute_paired_comparison(
                baseline_trials, ab_trials, lambda t: float(t.metrics.context_tokens)
            )

            # Historical delta
            base_hist = [t for t in baseline_trials if t.metrics.historical_recall is not None]
            ab_hist = [t for t in ab_trials if t.metrics.historical_recall is not None]
            p_hist = compute_paired_comparison(
                base_hist, ab_hist, lambda t: 1.0 if t.metrics.historical_recall else 0.0
            )

            # Contradiction delta
            base_contra = [t for t in baseline_trials if t.metrics.contradiction_accuracy is not None]
            ab_contra = [t for t in ab_trials if t.metrics.contradiction_accuracy is not None]
            p_contra = compute_paired_comparison(
                base_contra, ab_contra, lambda t: 1.0 if t.metrics.contradiction_accuracy else 0.0
            )

            r_delta = f"{p_recall['mean_delta'] * 100:+.1f}%"
            a_delta = f"{p_ans['mean_delta'] * 100:+.1f}%"
            h_delta = f"{p_hist['mean_delta'] * 100:+.1f}%"
            c_delta = f"{p_ctx['mean_delta']:+.1f}"
            k_delta = f"{p_contra['mean_delta'] * 100:+.1f}%"

            lines.append(f"| **{ab_name}** | {desc} | {r_delta} | {a_delta} | {h_delta} | {c_delta} | {k_delta} |")

        return "\n".join(lines)

    def format_table_3_budget_breakdown(self) -> str:
        """
        Table 3: Budget-specific performance across 128, 256, 512, 1024, 2048.
        """
        budgets = sorted(list(set(r.budget for r in self.results)))
        methods = sorted(list(set(r.method for r in self.results)))

        lines = [
            "| Budget | Method | Fact Recall | Answer Correctness | Avg Context Tokens | Context Utilization |",
            "| :---: | :--- | :---: | :---: | :---: | :---: |",
        ]

        for b in budgets:
            b_trials = [r for r in self.results if r.budget == b]
            for m in methods:
                mb_trials = [r for r in b_trials if r.method == m]
                if not mb_trials:
                    continue
                n = len(mb_trials)
                recall = sum(1 for r in mb_trials if r.metrics.fact_recall) / n
                ans_corr = sum(1 for r in mb_trials if r.metrics.answer_correctness) / n
                avg_ctx = sum(r.metrics.context_tokens for r in mb_trials) / n
                avg_util = sum(r.metrics.context_utilization for r in mb_trials) / n
                lines.append(
                    f"| {b} | **{m}** | {recall * 100:.1f}% | {ans_corr * 100:.1f}% | {avg_ctx:.1f} | {avg_util * 100:.1f}% |"
                )

        return "\n".join(lines)

    def format_table_4_mechanism_scenarios(self) -> str:
        """
        Table 4: Mechanism-specific scenario performance.
        Breakdown of target mechanism scenarios:
        1. Contradiction scenarios (scenario_b_superseding_facts)
        2. Confidence-sensitive scenarios (scenario_i_ambiguous_confidence)
        3. Tier-selection scenarios (scenario_j_tier_competition)
        4. Historical reconstruction scenarios (is_historical=True)
        """
        categories = [
            ("Contradiction (PostgreSQL -> MongoDB)", lambda r: r.scenario_id == "scenario_b_superseding_facts"),
            ("Confidence-Aware Preservation", lambda r: r.scenario_id == "scenario_i_ambiguous_confidence"),
            ("Tier Selection Competition (B=128)", lambda r: r.scenario_id == "scenario_j_tier_competition" and r.budget == 128),
            ("Historical Reconstruction Queries", lambda r: bool(r.config_metadata.get("is_historical"))),
        ]

        methods = [
            "Full History",
            "Sliding Window (N=10)",
            "Running Summary",
            "RAG-Style (Raw Messages)",
            "ManiGit (full)",
            "ManiGit (no_contradiction)",
            "ManiGit (no_confidence)",
            "ManiGit (no_tier)",
        ]

        lines = [
            "| Mechanism Category | Method | Target Metric | Metric Value | Interpretation |",
            "| :--- | :--- | :--- | :---: | :--- |",
        ]

        for cat_name, filter_fn in categories:
            for m in methods:
                cat_trials = [r for r in self.results if filter_fn(r) and r.method == m]
                if not cat_trials:
                    continue
                n = len(cat_trials)

                if "Contradiction" in cat_name:
                    metric_name = "Contradiction Accuracy"
                    val = sum(1 for r in cat_trials if r.metrics.contradiction_accuracy) / n
                    interp = "Cleanly superseded" if val == 1.0 else "Unresolved conflict / stale fact"
                elif "Confidence" in cat_name:
                    metric_name = "Ambiguous Fact Recall"
                    val = sum(1 for r in cat_trials if r.metrics.fact_recall) / n
                    interp = "Preserved via escalation" if val == 1.0 else "Lost due to uncalibrated archive"
                elif "Tier" in cat_name:
                    metric_name = "Verbatim Fact Recall @ B=128"
                    val = sum(1 for r in cat_trials if r.metrics.fact_recall) / n
                    interp = "Verbatim prioritized over summary" if val == 1.0 else "Summary outranks verbatim; fact dropped"
                else:  # Historical
                    metric_name = "Historical Recovery Rate"
                    val = sum(1 for r in cat_trials if r.metrics.historical_recall) / n
                    interp = "Immutable commit recovered" if val == 1.0 else "Historical state lost"

                lines.append(f"| {cat_name} | **{m}** | {metric_name} | {val * 100:.1f}% | {interp} |")

        return "\n".join(lines)

    def generate_full_report(self, title: str = "ManiGit Empirical Evaluation Report") -> str:
        """Synthesizes the complete comprehensive markdown research report."""
        sections = [
            f"# {title}",
            "",
            "## 1. Executive Summary & Table 1: Overall Comparative Performance",
            self.format_table_1_overall_comparison(),
            "",
            "## Table 2: Ablation Degradation Relative to ManiGit Full",
            self.format_table_2_ablation_degradation(),
            "",
            "## Table 3: Budget-Specific Performance Breakdown",
            self.format_table_3_budget_breakdown(),
            "",
            "## Table 4: Mechanism-Specific Scenarios",
            self.format_table_4_mechanism_scenarios(),
            "",
            "## 5. Per-Scenario Performance Breakdown",
            self.format_scenario_comparison_table(),
            "",
            "## 6. Historical Fact Recovery Under Supersession",
            self.format_historical_recall_table(),
            "",
            "## 7. Contradiction & Supersession Differentiation",
            self.format_contradiction_handling_table(),
            "",
            "## 8. Budget vs. Fact Recall Sensitivity",
            self.format_budget_vs_recall_table(),
            "",
            "## 9. Context Token Consumption vs. Conversation Length",
            self.format_conversation_length_vs_tokens_table(),
            "",
            "---",
            "*Report generated directly from empirical benchmark trials without synthetic fabrication.*",
        ]
        return "\n".join(sections)

