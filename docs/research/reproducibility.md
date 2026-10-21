# ManiGit Reproducibility Guide

## 1. Environment Specifications
- **Operating System**: Windows / Linux / macOS (POSIX & Windows compatible)
- **Python Version**: `>=3.10` (Tested on Python 3.11.15)
- **Package & Environment Manager**: `uv` (Fast Python package installer and resolver)
- **Primary Dependencies**:
  - `pydantic>=2.0.0`
  - `pytest>=8.0.0`
  - `pytest-cov>=4.0.0`
  - `fastapi>=0.110.0`
  - `uvicorn>=0.28.0`

## 2. Installation & Setup
From the repository root, install dependencies into a local isolated virtual environment:

```powershell
# Using uv (recommended)
uv sync

# Or using standard pip in a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # On Windows PowerShell
pip install -e .
```

## 3. Dataset & Scenario Sources
The benchmark dataset consists of 11 structured, version-controlled conversation scenarios implemented programmatically in [scenarios.py](file:///c:/Users/Arshmeet/OneDrive/Desktop/Projects/ManiGit/src/manigit/evaluation/scenarios.py):
1. `scenario_a_stable_facts` (2 queries)
2. `scenario_b_superseding_facts` (2 queries)
3. `scenario_c_exact_constraints` (2 queries)
4. `scenario_d_decisions` (2 queries)
5. `scenario_e_technical_facts` (3 queries)
6. `scenario_f_distractors` (2 queries)
7. `scenario_g_duplicates` (2 queries)
8. `scenario_h_long_50` (2 queries)
9. `scenario_h_long_100` (3 queries)
10. `scenario_i_ambiguous_confidence` (1 query)
11. `scenario_j_tier_competition` (1 query)

Total unique queries across the ablation benchmark suite: **22 queries**.

## 4. Random Seed & Determinism
All experiments use a fixed deterministic seed:
```json
"random_seed": 42
```
This guarantees exact, bit-for-bit repeatability of token allocations, priority orderings, and evaluation grading.

## 5. Experiment Configurations
- Canonical Run Config: [evaluation_protocol.md](file:///c:/Users/Arshmeet/OneDrive/Desktop/Projects/ManiGit/docs/research/evaluation_protocol.md)
- Ablation Run Config: [ablation_config.json](file:///c:/Users/Arshmeet/OneDrive/Desktop/Projects/ManiGit/data/processed/benchmarks/ablation_config.json)

## 6. Execution Commands

### Reproducing the Ablation Experiment (Phase 8)
To run the full ablation matrix (880 trials) and regenerate all paper-ready figure data:

```powershell
uv run python -c "
import sys; sys.path.insert(0, 'src')
from manigit.evaluation.runner import BenchmarkConfig, BenchmarkRunner
from manigit.evaluation.scenarios import get_ablation_benchmark_suite
from manigit.evaluation.figures import FigureDataGenerator
from manigit.evaluation.models import BaselineType, AblationMode

config = BenchmarkConfig(
    experiment_id='exp_ablation_run_001',
    methods=[
        BaselineType.FULL_HISTORY,
        BaselineType.SLIDING_WINDOW,
        BaselineType.SUMMARY,
        BaselineType.RAG_STYLE,
        BaselineType.MANIGIT,
    ],
    ablation_modes=[
        AblationMode.FULL,
        AblationMode.NO_CONTRADICTION,
        AblationMode.NO_CONFIDENCE,
        AblationMode.NO_TIER,
    ],
    budgets=[128, 256, 512, 1024, 2048],
    random_seed=42,
    storage_dir='data/processed/benchmarks/results',
)

runner = BenchmarkRunner(config=config)
suite = get_ablation_benchmark_suite()
results = runner.run_benchmark(suite=suite, save_results=True)
fig_gen = FigureDataGenerator(output_dir='data/processed/benchmarks/figures')
fig_gen.generate_all_figures(results)
print(f'Successfully reproduced ablation experiment: {len(results)} trials.')
"
```

## 7. Raw Output Locations
- Canonical Baseline Results: `data/processed/benchmarks/results/exp_canonical_run_001.json` (500 trials, read-only)
- Ablation Results: `data/processed/benchmarks/results/exp_ablation_run_001.json` (880 trials)
- Machine-Readable Figure Data: `data/processed/benchmarks/figures/` (7 JSON files + 7 CSV files + 1 index file)

## 8. Aggregation Process
Aggregates are computed directly from the raw trial records using `BenchmarkReportGenerator` in [reporting.py](file:///c:/Users/Arshmeet/OneDrive/Desktop/Projects/ManiGit/src/manigit/evaluation/reporting.py):

```powershell
uv run python -c "
import sys, json; sys.path.insert(0, 'src')
from manigit.evaluation.models import BenchmarkResult
from manigit.evaluation.reporting import BenchmarkReportGenerator

with open('data/processed/benchmarks/results/exp_ablation_run_001.json') as f:
    trials = [BenchmarkResult.from_dict(d) for d in json.load(f)]

report = BenchmarkReportGenerator(trials)
print(report.format_table_1_overall_comparison())
print(report.format_table_2_ablation_degradation())
"
```

## 9. Statistical Analysis
All binomial proportions (fact recall, answer correctness, historical recovery, contradiction accuracy) are evaluated with closed-form 95% Wilson score confidence intervals implemented in [statistics.py](file:///c:/Users/Arshmeet/OneDrive/Desktop/Projects/ManiGit/src/manigit/evaluation/statistics.py):
$$p \pm \frac{z}{1 + z^2/n} \sqrt{\frac{p(1-p)}{n} + \frac{z^2}{4n^2}}$$
Continuous token metrics report sample mean, sample standard deviation, median, min, and max.

## 10. Figure Generation
Figure data is exported as both JSON and CSV files via `FigureDataGenerator` in [figures.py](file:///c:/Users/Arshmeet/OneDrive/Desktop/Projects/ManiGit/src/manigit/evaluation/figures.py):
1. `fig1_context_vs_budget` (.json, .csv)
2. `fig2_fact_recall_vs_budget` (.json, .csv)
3. `fig3_correctness_vs_budget` (.json, .csv)
4. `fig4_historical_recovery` (.json, .csv)
5. `fig5_contradiction_handling` (.json, .csv)
6. `fig6_ablation_degradation` (.json, .csv)
7. `fig7_efficiency_tradeoff` (.json, .csv)

## 11. Verifying Result Counts
Run the following verification script:
```powershell
uv run python -c "
import json
with open('data/processed/benchmarks/results/exp_canonical_run_001.json') as f:
    canon = json.load(f)
assert len(canon) == 500, f'Expected 500 canonical trials, got {len(canon)}'

with open('data/processed/benchmarks/results/exp_ablation_run_001.json') as f:
    ab = json.load(f)
assert len(ab) == 880, f'Expected 880 ablation trials, got {len(ab)}'
print('Verified: Canonical = 500 trials; Ablation = 880 trials. All counts match.')
"
```

## 12. Safe Canonical Reproduction (Without Overwriting)
To verify or regenerate canonical trials safely into a separate verification file without modifying `exp_canonical_run_001.json`:
```powershell
uv run python -c "
import sys; sys.path.insert(0, 'src')
from manigit.evaluation.runner import BenchmarkConfig, BenchmarkRunner
from manigit.evaluation.scenarios import get_standard_benchmark_suite

config = BenchmarkConfig(
    experiment_id='exp_canonical_verification_001',
    storage_dir='data/processed/benchmarks/results',
)
runner = BenchmarkRunner(config=config)
res = runner.run_benchmark(suite=get_standard_benchmark_suite(), save_results=True)
print(f'Safely generated canonical verification run: {len(res)} trials.')
"
```
The storage layer explicitly protects `exp_canonical_run_001.json` via a write-permission barrier. Attempting to overwrite it directly raises `PermissionError`.

## 13. Running the Test Suite
To run all 176 test cases (including unit, integration, web, and Phase 8 ablation verification):
```powershell
uv run pytest -v
```
All 176 tests must pass with 0 failures and 0 skips.
