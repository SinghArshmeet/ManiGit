# ManiGit: Planned Evaluation Strategy

This document outlines the rigorous, empirical methodology designed to evaluate the ManiGit memory architecture against conventional agent memory approaches.

> [!NOTE]
> All figures in this document represent planned methodology, baseline definitions, and experimental protocols. In accordance with Phase 0 standards, no unmeasured performance gains or benchmark scores are claimed prior to empirical execution.

---

## 1. Evaluation Objectives

The objective of the ManiGit evaluation framework is to test the following hypotheses under controlled multi-session agent workloads:
1. **Token Cost Hypothesis:** Versioned, tiered context compilation maintains a stable token footprint per request as conversation length scales, compared to raw history accumulation.
2. **Precision Retention Hypothesis:** Three-tier memory with verbatim retention for critical constraints prevents the factual degradation observed in sliding window and blanket summarization baselines.
3. **Reversibility Hypothesis:** Branching and rollback allow rapid recovery from conversational mistakes or hallucinated knowledge without agent restarts.

---

## 2. Baseline Comparison Systems

ManiGit will be benchmarked against three industry-standard memory approaches:

| Baseline System | Operational Mechanism | Expected Failure Mode |
| :--- | :--- | :--- |
| **Baseline 1: Full History (Naive)** | Appends all prior user and assistant turns verbatim into context. | Hits context window limits; linear/quadratic token cost growth. |
| **Baseline 2: Sliding Window** | Retains only the most recent $N$ conversational turns verbatim; discards earlier turns. | Immediate loss of early critical facts, instructions, and constraints. |
| **Baseline 3: Blanket Summarizer** | Runs an LLM summarization step over history to generate a single evolving text summary. | Information blurring, loss of exact numbers/IDs/code, hallucination accumulation. |
| **ManiGit (Proposed)** | Version-controlled 3-tier memory with provenance, commits, and budget-aware assembly. | Balanced trade-off: bounded token size with exact verbatim constraint preservation. |

---

## 3. Benchmark Tasks & Test Scenarios

### 3.1 Long-Session Needle-in-a-Haystack (NIAH)
- **Protocol:** A critical factual anchor (e.g., unique database credentials, client preference, exact constraint) is introduced at turn 1. The agent engages in 50–100 turns of varied domain dialogue. At turn 100, the user requests a task requiring the initial anchor.
- **Metric:** Fact Recall Accuracy (Exact Match / F1).

### 3.2 Constraint Revision & Contradiction Resolution
- **Protocol:** The user introduces constraint A at turn 5, then explicitly alters it to constraint B at turn 35. At turn 60, the user asks the agent to perform an operation dependent on the constraint.
- **Metric:** Revision Accuracy (did the agent follow constraint B and discard constraint A, without conflicting hallucination?).

### 3.3 Reversibility & Rollback Test
- **Protocol:** An intentional distraction or erroneous turn is introduced at turn 20. A rollback command reverts the state to turn 19. Subsequent queries verify that memory cleanly matches the pre-distraction state.
- **Metric:** State Purity Score (absence of tainted facts in compiled context post-rollback).

---

## 4. Quantitative Metrics

1. **Tokens Per Request:** Number of prompt tokens sent to the LLM on each turn over a session of length $T$.
2. **Cumulative Token Cost:** Total tokens consumed across multi-session benchmarks.
3. **Inference Latency:** End-to-end response time including memory operations.
4. **Memory Operation Overhead:** Time taken to execute classification, commit persistence, and context compilation.
5. **Factual Accuracy Score:** Percentage of test questions correctly answered using recalled memory.

---

## 5. Experimental Reproducibility Protocol

- Standardized benchmark conversation traces stored in `data/raw/`.
- Seeded random inputs for deterministic repeatability.
- Automated evaluation runner in `src/manigit/evaluation/` logging metrics into structured JSON outputs in `data/processed/`.
