"""
Result storage module for ManiGit research benchmarks.

Persists benchmark trial results as structured JSON/JSONL files in:
data/processed/benchmarks/results/
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from manigit.evaluation.models import BenchmarkResult


class BenchmarkResultStorage:
    """
    Handles file-based persistence and retrieval of benchmark experiment records.
    Maintains complete isolation from ManiGit's internal SQLite repository.
    """

    def __init__(self, base_dir: str = "data/processed/benchmarks/results"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_file = self.base_dir / "benchmarks_ledger.jsonl"

    PROTECTED_EXPERIMENTS = {"exp_canonical_run_001"}

    def save_run(
        self,
        experiment_id: str,
        results: List[BenchmarkResult],
        allow_protected_overwrite: bool = False,
    ) -> Path:
        """
        Saves a collection of results from an experiment run as both:
        1. A dedicated run file: <experiment_id>.json
        2. Appended records in: benchmarks_ledger.jsonl

        Guarantees that canonical benchmark results (e.g. exp_canonical_run_001)
        cannot be accidentally modified or overwritten.
        """
        run_file = self.base_dir / f"{experiment_id}.json"

        if experiment_id in self.PROTECTED_EXPERIMENTS and run_file.exists() and not allow_protected_overwrite:
            raise PermissionError(
                f"CANONICAL EXPERIMENT PROTECTION: '{experiment_id}.json' is an immutable "
                "baseline artifact and cannot be overwritten."
            )

        serialized = [r.to_dict() for r in results]

        with open(run_file, "w", encoding="utf-8") as f:
            json.dump(serialized, f, indent=2)

        # Append to continuous ledger
        with open(self.ledger_file, "a", encoding="utf-8") as f:
            for item in serialized:
                f.write(json.dumps(item) + "\n")

        return run_file

    def load_run(self, experiment_id: str) -> List[BenchmarkResult]:
        """Loads all results for a given experiment ID."""
        run_file = self.base_dir / f"{experiment_id}.json"
        if not run_file.exists():
            return []

        with open(run_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return [BenchmarkResult.from_dict(d) for d in data]

    def load_all_results(self) -> List[BenchmarkResult]:
        """Loads all historical benchmark results from the ledger."""
        if not self.ledger_file.exists():
            return []

        results: List[BenchmarkResult] = []
        with open(self.ledger_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    results.append(BenchmarkResult.from_dict(json.loads(line)))

        return results

    def query_results(
        self,
        scenario_id: Optional[str] = None,
        method: Optional[str] = None,
        budget: Optional[int] = None,
    ) -> List[BenchmarkResult]:
        """Filters stored results by scenario, baseline method, and budget."""
        all_res = self.load_all_results()
        filtered: List[BenchmarkResult] = []

        for r in all_res:
            if scenario_id and r.scenario_id != scenario_id:
                continue
            if method and r.method != method:
                continue
            if budget is not None and r.budget != budget:
                continue
            filtered.append(r)

        return filtered
