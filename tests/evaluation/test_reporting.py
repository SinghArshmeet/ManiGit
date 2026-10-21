"""
Unit tests for benchmark report generator and markdown research formatting.
"""

import tempfile
import pytest

from manigit.evaluation.models import BaselineType
from manigit.evaluation.reporting import BenchmarkReportGenerator
from manigit.evaluation.runner import BenchmarkConfig, BenchmarkRunner
from manigit.evaluation.scenarios import (
    create_stable_facts_scenario,
    create_superseding_facts_scenario,
)
from manigit.evaluation.storage import BenchmarkResultStorage


def test_report_generator_with_runner_results():
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = BenchmarkResultStorage(base_dir=tmp_dir)
        config = BenchmarkConfig(
            experiment_id="test_exp_reporting",
            methods=[BaselineType.FULL_HISTORY, BaselineType.MANIGIT],
            budgets=[256, 512],
            scenarios=["superseding_facts"],
            storage_dir=tmp_dir,
            random_seed=42,
        )

        runner = BenchmarkRunner(config=config, storage=storage)
        suite = {"superseding_facts": create_superseding_facts_scenario()}
        results = runner.run_benchmark(suite=suite, save_results=True)

        generator = BenchmarkReportGenerator(results)

        # 1. Method aggregates
        aggs = generator.generate_method_aggregates()
        assert len(aggs) >= 2
        for m, data in aggs.items():
            assert "fact_recall_rate" in data
            assert "avg_context_tokens" in data

        table_aggs = generator.format_method_aggregates_table()
        assert "| Method |" in table_aggs
        assert "ManiGit" in table_aggs

        # 2. Scenario breakdown
        sc_table = generator.format_scenario_comparison_table()
        assert "| Scenario | Method |" in sc_table

        # 3. Historical recall
        hist_table = generator.format_historical_recall_table()
        assert "| Method | Historical Trials |" in hist_table

        # 4. Contradiction handling
        contra_table = generator.format_contradiction_handling_table()
        assert "| Method | Trials | Contradiction Accuracy |" in contra_table

        # 5. Budget vs recall
        b_table = generator.format_budget_vs_recall_table()
        assert "| Budget (Tokens) |" in b_table
        assert "256" in b_table
        assert "512" in b_table

        # 6. Length vs tokens
        len_table = generator.format_conversation_length_vs_tokens_table()
        assert "| Turns |" in len_table

        # 7. Full report
        full_report = generator.generate_full_report()
        assert "# ManiGit Empirical Evaluation Report" in full_report
        assert "Executive Summary" in full_report
