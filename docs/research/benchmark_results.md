# Empirical Benchmark Evaluation Results

**Experiment Run ID:** `exp_canonical_run_001`  
**Environment:** Python 3.11, Windows x86_64, Isolated In-Memory SQLite  
**Date:** 2026-10-20  
**Verification:** Controlled deterministic evaluation (MockModelAdapter + Rule Engine + Lexical Context Compilation)

All numbers reported below were empirically measured and generated directly from trial records saved in `data/processed/benchmarks/results/exp_canonical_run_001.json`. No values have been fabricated, altered, or interpolated.

# ManiGit Phase 5 Empirical Benchmark Report

## 1. Executive Summary & Aggregate Baseline Performance Across All Budgets
*Aggregate performance computed across all 5 evaluated token budgets (128, 256, 512, 1024, 2048).*

| Method | Trials | Fact Recall | Ans Correct | Hist Recall | Avg Ctx Tok | Avg Total Tok | Precision | Latency Ctx (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Full History** | 100 | 82.0% | 77.0% | 100.0% | 317.3 | 342.3 | 0.198 | 0.04 |
| **ManiGit (full)** | 100 | 85.0% | 85.0% | 100.0% | 179.5 | 204.4 | 0.240 | 0.97 |
| **RAG-Style (Raw Messages)** | 100 | 95.0% | 90.0% | 100.0% | 197.1 | 221.7 | 0.365 | 0.49 |
| **Running Summary** | 100 | 95.0% | 90.0% | 100.0% | 35.5 | 60.1 | 0.412 | 0.0 |
| **Sliding Window (N=10)** | 100 | 74.0% | 69.0% | 100.0% | 138.5 | 163.8 | 0.194 | 0.01 |

## 2. Budget-Specific Performance Breakdown
*Explicitly separated performance metrics at each evaluated token budget level.*

### Results at B=128
*Evaluation constrained to maximum context budget B=128 tokens.*

| Method | Trials | Fact Recall | Ans Correct | Hist Recall | Avg Ctx Tok | Avg Total Tok | Precision | Latency Ctx (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Full History** | 20 | 75.0% | 70.0% | 100.0% | 109.9 | 135.2 | 0.234 | 0.02 |
| **ManiGit (full)** | 20 | 85.0% | 85.0% | 100.0% | 79.2 | 104.0 | 0.266 | 0.82 |
| **RAG-Style (Raw Messages)** | 20 | 95.0% | 90.0% | 100.0% | 90.7 | 115.3 | 0.414 | 0.47 |
| **Running Summary** | 20 | 95.0% | 90.0% | 100.0% | 35.5 | 60.1 | 0.412 | 0.0 |
| **Sliding Window (N=10)** | 20 | 70.0% | 65.0% | 100.0% | 116.9 | 142.4 | 0.184 | 0.01 |

### Results at B=256
*Evaluation constrained to maximum context budget B=256 tokens.*

| Method | Trials | Fact Recall | Ans Correct | Hist Recall | Avg Ctx Tok | Avg Total Tok | Precision | Latency Ctx (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Full History** | 20 | 75.0% | 70.0% | 100.0% | 169.8 | 195.1 | 0.196 | 0.02 |
| **ManiGit (full)** | 20 | 85.0% | 85.0% | 100.0% | 121.7 | 146.6 | 0.244 | 0.82 |
| **RAG-Style (Raw Messages)** | 20 | 95.0% | 90.0% | 100.0% | 146.6 | 171.2 | 0.369 | 0.5 |
| **Running Summary** | 20 | 95.0% | 90.0% | 100.0% | 35.5 | 60.1 | 0.412 | 0.0 |
| **Sliding Window (N=10)** | 20 | 75.0% | 70.0% | 100.0% | 143.9 | 169.2 | 0.197 | 0.01 |

### Results at B=512
*Evaluation constrained to maximum context budget B=512 tokens.*

| Method | Trials | Fact Recall | Ans Correct | Hist Recall | Avg Ctx Tok | Avg Total Tok | Precision | Latency Ctx (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Full History** | 20 | 75.0% | 70.0% | 100.0% | 278.4 | 303.6 | 0.187 | 0.03 |
| **ManiGit (full)** | 20 | 85.0% | 85.0% | 100.0% | 191.4 | 216.3 | 0.233 | 0.98 |
| **RAG-Style (Raw Messages)** | 20 | 95.0% | 90.0% | 100.0% | 225.2 | 249.9 | 0.350 | 0.5 |
| **Running Summary** | 20 | 95.0% | 90.0% | 100.0% | 35.5 | 60.1 | 0.412 | 0.0 |
| **Sliding Window (N=10)** | 20 | 75.0% | 70.0% | 100.0% | 143.9 | 169.2 | 0.197 | 0.01 |

### Results at B=1024
*Evaluation constrained to maximum context budget B=1024 tokens.*

| Method | Trials | Fact Recall | Ans Correct | Hist Recall | Avg Ctx Tok | Avg Total Tok | Precision | Latency Ctx (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Full History** | 20 | 90.0% | 85.0% | 100.0% | 452.1 | 476.9 | 0.187 | 0.05 |
| **ManiGit (full)** | 20 | 85.0% | 85.0% | 100.0% | 252.6 | 277.4 | 0.230 | 1.16 |
| **RAG-Style (Raw Messages)** | 20 | 95.0% | 90.0% | 100.0% | 261.4 | 286.0 | 0.347 | 0.55 |
| **Running Summary** | 20 | 95.0% | 90.0% | 100.0% | 35.5 | 60.1 | 0.412 | 0.0 |
| **Sliding Window (N=10)** | 20 | 75.0% | 70.0% | 100.0% | 143.9 | 169.2 | 0.197 | 0.01 |

### Results at B=2048
*Evaluation constrained to maximum context budget B=2048 tokens.*

| Method | Trials | Fact Recall | Ans Correct | Hist Recall | Avg Ctx Tok | Avg Total Tok | Precision | Latency Ctx (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Full History** | 20 | 95.0% | 90.0% | 100.0% | 576.3 | 601.0 | 0.186 | 0.07 |
| **ManiGit (full)** | 20 | 85.0% | 85.0% | 100.0% | 252.6 | 277.4 | 0.230 | 1.08 |
| **RAG-Style (Raw Messages)** | 20 | 95.0% | 90.0% | 100.0% | 261.4 | 286.0 | 0.347 | 0.44 |
| **Running Summary** | 20 | 95.0% | 90.0% | 100.0% | 35.5 | 60.1 | 0.412 | 0.0 |
| **Sliding Window (N=10)** | 20 | 75.0% | 70.0% | 100.0% | 143.9 | 169.2 | 0.197 | 0.01 |

## 3. Per-Scenario Performance Breakdown
| Scenario | Method | Fact Recall | Ans Correct | Avg Ctx Tokens | Avg Precision |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `scenario_a_stable_facts` | Full History | 100.0% | 50.0% | 126.6 | 0.257 |
| `scenario_a_stable_facts` | ManiGit (full) | 50.0% | 50.0% | 34.0 | 0.250 |
| `scenario_a_stable_facts` | RAG-Style (Raw Messages) | 100.0% | 50.0% | 42.5 | 0.833 |
| `scenario_a_stable_facts` | Running Summary | 100.0% | 50.0% | 26.0 | 0.500 |
| `scenario_a_stable_facts` | Sliding Window (N=10) | 100.0% | 50.0% | 126.6 | 0.257 |
| `scenario_b_superseding_facts` | Full History | 100.0% | 100.0% | 128.0 | 0.250 |
| `scenario_b_superseding_facts` | ManiGit (full) | 100.0% | 100.0% | 34.5 | 0.667 |
| `scenario_b_superseding_facts` | RAG-Style (Raw Messages) | 100.0% | 100.0% | 82.0 | 0.417 |
| `scenario_b_superseding_facts` | Running Summary | 100.0% | 100.0% | 26.0 | 0.500 |
| `scenario_b_superseding_facts` | Sliding Window (N=10) | 100.0% | 100.0% | 128.0 | 0.250 |
| `scenario_c_exact_constraints` | Full History | 100.0% | 100.0% | 92.0 | 0.333 |
| `scenario_c_exact_constraints` | ManiGit (full) | 100.0% | 100.0% | 50.0 | 0.333 |
| `scenario_c_exact_constraints` | RAG-Style (Raw Messages) | 100.0% | 100.0% | 72.5 | 0.450 |
| `scenario_c_exact_constraints` | Running Summary | 100.0% | 100.0% | 24.0 | 0.500 |
| `scenario_c_exact_constraints` | Sliding Window (N=10) | 100.0% | 100.0% | 92.0 | 0.333 |
| `scenario_d_decisions` | Full History | 100.0% | 100.0% | 104.0 | 0.333 |
| `scenario_d_decisions` | ManiGit (full) | 100.0% | 100.0% | 55.0 | 0.333 |
| `scenario_d_decisions` | RAG-Style (Raw Messages) | 100.0% | 100.0% | 65.0 | 0.583 |
| `scenario_d_decisions` | Running Summary | 100.0% | 100.0% | 34.0 | 0.500 |
| `scenario_d_decisions` | Sliding Window (N=10) | 100.0% | 100.0% | 104.0 | 0.333 |
| `scenario_e_technical_facts` | Full History | 100.0% | 100.0% | 108.0 | 0.333 |
| `scenario_e_technical_facts` | ManiGit (full) | 100.0% | 100.0% | 63.0 | 0.333 |
| `scenario_e_technical_facts` | RAG-Style (Raw Messages) | 100.0% | 100.0% | 76.0 | 0.500 |
| `scenario_e_technical_facts` | Running Summary | 100.0% | 100.0% | 49.0 | 0.333 |
| `scenario_e_technical_facts` | Sliding Window (N=10) | 100.0% | 100.0% | 108.0 | 0.333 |
| `scenario_f_distractors` | Full History | 70.0% | 70.0% | 530.6 | 0.063 |
| `scenario_f_distractors` | ManiGit (full) | 50.0% | 50.0% | 131.0 | 0.064 |
| `scenario_f_distractors` | RAG-Style (Raw Messages) | 100.0% | 100.0% | 403.7 | 0.117 |
| `scenario_f_distractors` | Running Summary | 100.0% | 100.0% | 28.0 | 0.500 |
| `scenario_f_distractors` | Sliding Window (N=10) | 40.0% | 40.0% | 168.6 | 0.080 |
| `scenario_g_duplicates` | Full History | 100.0% | 100.0% | 249.4 | 0.172 |
| `scenario_g_duplicates` | ManiGit (full) | 100.0% | 100.0% | 147.2 | 0.133 |
| `scenario_g_duplicates` | RAG-Style (Raw Messages) | 100.0% | 100.0% | 166.8 | 0.240 |
| `scenario_g_duplicates` | Running Summary | 100.0% | 100.0% | 52.0 | 0.250 |
| `scenario_g_duplicates` | Sliding Window (N=10) | 100.0% | 100.0% | 166.8 | 0.000 |
| `scenario_h_long_100` | Full History | 53.3% | 53.3% | 741.6 | 0.046 |
| `scenario_h_long_100` | ManiGit (full) | 100.0% | 100.0% | 539.7 | 0.064 |
| `scenario_h_long_100` | RAG-Style (Raw Messages) | 100.0% | 100.0% | 448.8 | 0.126 |
| `scenario_h_long_100` | Running Summary | 100.0% | 100.0% | 46.0 | 0.333 |
| `scenario_h_long_100` | Sliding Window (N=10) | 33.3% | 33.3% | 173.6 | 0.063 |
| `scenario_h_long_50` | Full History | 46.7% | 46.7% | 528.4 | 0.059 |
| `scenario_h_long_50` | ManiGit (full) | 66.7% | 66.7% | 341.7 | 0.063 |
| `scenario_h_long_50` | RAG-Style (Raw Messages) | 66.7% | 66.7% | 289.5 | 0.129 |
| `scenario_h_long_50` | Running Summary | 66.7% | 66.7% | 32.0 | 0.333 |
| `scenario_h_long_50` | Sliding Window (N=10) | 33.3% | 33.3% | 173.6 | 0.063 |

## 4. Historical Fact Recovery Under Supersession
| Method | Historical Trials | Historical Recall | Answer Correct | Avg Context Tokens |
| :--- | :---: | :---: | :---: | :---: |
| **Full History** | 5 | 100.0% | 100.0% | 128.0 |
| **ManiGit (full)** | 5 | 100.0% | 100.0% | 18.0 |
| **RAG-Style (Raw Messages)** | 5 | 100.0% | 100.0% | 98.0 |
| **Running Summary** | 5 | 100.0% | 100.0% | 26.0 |
| **Sliding Window (N=10)** | 5 | 100.0% | 100.0% | 128.0 |

## 5. Contradiction & Supersession Differentiation
| Method | Trials | Contradiction Accuracy | Current Fact Accuracy | Historical Fact Accuracy |
| :--- | :---: | :---: | :---: | :---: |
| **Full History** | 10 | 100.0% | 100.0% | 100.0% |
| **ManiGit (full)** | 10 | 100.0% | 100.0% | 100.0% |
| **RAG-Style (Raw Messages)** | 10 | 100.0% | 100.0% | 100.0% |
| **Running Summary** | 10 | 50.0% | 100.0% | 100.0% |
| **Sliding Window (N=10)** | 10 | 100.0% | 100.0% | 100.0% |

## 6. Budget vs. Fact Recall Sensitivity
| Budget (Tokens) | Full History | ManiGit (full) | RAG-Style (Raw Messages) | Running Summary | Sliding Window (N=10) |
| :---: |:---: |:---: |:---: |:---: |:---: |
| **128** | 75.0% | 85.0% | 95.0% | 95.0% | 70.0% |
| **256** | 75.0% | 85.0% | 95.0% | 95.0% | 75.0% |
| **512** | 75.0% | 85.0% | 95.0% | 95.0% | 75.0% |
| **1024** | 90.0% | 85.0% | 95.0% | 95.0% | 75.0% |
| **2048** | 95.0% | 85.0% | 95.0% | 95.0% | 75.0% |

## 7. Context Token Consumption vs. Conversation Length
| Turns | Full History | ManiGit (full) | RAG-Style (Raw Messages) | Running Summary | Sliding Window (N=10) |
| :---: |:---: |:---: |:---: |:---: |:---: |
| **6** | 102.3 | 57.0 | 71.9 | 37.6 | 102.3 |
| **8** | 127.3 | 34.2 | 62.2 | 26.0 | 127.3 |
| **16** | 249.4 | 147.2 | 166.8 | 52.0 | 166.8 |
| **48** | 528.4 | 341.7 | 289.5 | 32.0 | 173.6 |
| **54** | 530.6 | 131.0 | 403.7 | 28.0 | 168.6 |
| **98** | 741.6 | 539.7 | 448.8 | 46.0 | 173.6 |

---
*Report generated directly from empirical benchmark trials without synthetic fabrication.*