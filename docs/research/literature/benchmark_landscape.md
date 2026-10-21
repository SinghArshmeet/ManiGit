# The Agent Memory Benchmark Landscape

**Project:** ManiGit — Transparent, Versioned Context Memory for Long-Running AI Agents  
**Document:** Benchmark Landscape & Evaluation Context  
**Date:** October 2026  

---

## 1. Overview

To properly evaluate long-term memory architectures, the research community has developed benchmarks ranging from synthetic in-context stress tests to multi-session interactive dialogue suites. This document surveys the leading benchmarks, analyzes their evaluation focus, and explicitly contrasts them with ManiGit's controlled evaluation protocol.

---

## 2. Benchmark Landscape Comparison

| Benchmark | Primary Purpose | Task Type | Memory Evaluated | Primary Metrics | Corpus Scale | Temporal Evaluation | Contradiction Evaluation | Historical Replay | Relevance to ManiGit |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **Needle-In-A-Haystack** (Kamradt, 2023) | Test raw context window depth retrieval | Single-fact retrieval | In-context attention | Exact string recall | 1k–128k+ tokens | — | — | — | Demonstrates depth retrieval degradation in raw context. |
| **BAMBOO** (Dong et al., 2023) | Multi-task long-text comprehension | QA, summarization, hallucination, code | In-context long prompt | Task-specific accuracy (F1, ROUGE) | 10 datasets, up to 16k tokens | — | — | — | Confirms that prompt stuffing degrades model reasoning. |
| **LoCoMo** (Maharana et al., 2024) | Long-context conversational memory | Multi-hop QA, temporal reasoning, persona | Multi-session dialogue memory | QA semantic accuracy (LLM judge) | 35 sessions, ~300 turns, ~9k tokens | Partial (chronology) | Partial | — | Evaluates temporal order of events across extended dialogues. |
| **LongMemEval** (Wu et al., 2024) | Multi-session interactive assistant memory | Fact recall, preference tracking, knowledge updates | Persistent chat memory | Extraction accuracy, update success rate | 35+ sessions, 100k+ tokens | ✓ | ✓ | — | Directly tests knowledge updates and multi-session fact persistence. |
| **STALE** (Anon, 2025) | Implicit contradiction adaptation | Multi-turn task execution with changing constraints | Working & persistent context | Premise resistance, state resolution accuracy | Multi-turn scenario corpus | ✓ | ✓ | — | Proves frontier LLMs retain stale premises in over 40% of trials. |
| **ManiGit Benchmark Suite** (This Work, 2026) | Controlled evaluation of memory mechanisms under token budgets | Multi-turn technical & conversational state tracking | Versioned commit memory, RAG, baselines | Fact recall, answer correctness, history recovery, tokens, budget compliance | 11 scenarios, 22 queries, 5 budgets, 880 trials | ✓ | ✓ | ✓ | Specifically isolates the causal impact of contradiction handling, confidence thresholds, and memory tiers under strict token budgets. |

---

## 3. Detailed Benchmark Analysis

### 3.1 In-Context Needle & Capacity Tests (Needle-In-A-Haystack, BAMBOO)
* **What they measure:** How effectively a transformer architecture attends to an isolated factual string buried within thousands of irrelevant background tokens.
* **Key Findings:** Models exhibit significant "Lost-in-the-Middle" degradation (Liu et al., 2024) and performance drops as prompt length increases, even when context capacity is nominally supported.
* **Limitations:** These benchmarks are **static**. They feature no state evolution, no multi-session dialogue, no updating of stale facts, and no memory budgeting.

### 3.2 Conversational & Multi-Session Benchmarks (LoCoMo, LongMemEval)
* **What they measure:** How well commercial assistants and open models retain user preferences and navigate multi-hop questions across disconnected sessions.
* **Key Findings:** Both LoCoMo and LongMemEval demonstrated that frontier models suffer sharp drops when required to synthesize information scattered across 30+ sessions or update beliefs when a user modifies a previously stated fact.
* **Limitations:** Primarily focused on chat dialogues and conversational personas rather than technical software engineering state, versioned branch trees, or deterministic context budgeting.

### 3.3 Contradiction & Belief Adaptation Benchmarks (STALE)
* **What they measure:** How models handle implicit contradictions where a subsequent turn invalidates a prior instruction without an explicit `"Forget the previous rule"` prompt.
* **Key Findings:** Confirmed that frontier models suffer from "ghost context," hallucinating or combining conflicting constraints in over 40% of evaluation trials.
* **Significance for ManiGit:** Validates that contradiction resolution cannot be left to probabilistic prompt interpretation; it requires explicit structural memory supersession.

---

## 4. Methodological Distinction: ManiGit's Controlled Evaluation Suite

To maintain scientific integrity, the relationship between ManiGit's evaluation and existing external benchmarks must be clearly defined:

1. **Synthetic, Controlled Micro-Benchmark:**
   ManiGit's evaluation suite (880 trials across 11 scenarios, 8 methods/ablations, and 5 budgets) is a **controlled synthetic micro-benchmark designed for causal ablation analysis**, not a massive web-scale natural language dataset.
2. **Deterministic Fairness Controls:**
   Unlike benchmarks that rely on stochastic frontier API calls and non-deterministic LLM-as-a-judge grading, ManiGit uses deterministic rule/mock model adapters with fixed random seeds (42) and identical queries across all methods. This guarantees that observed differences reflect the **mechanisms being ablated** rather than API sampling jitter.
3. **No Claim of Direct Benchmark Superiority:**
   ManiGit does not claim to have been evaluated on the entire public LongMemEval or LoCoMo corpora. Rather, ManiGit's scenarios mirror the core failure modes identified by LongMemEval and STALE (knowledge updates, superseding technical facts, temporal recovery) while adding formal token budget constraints ($B \in [128, 2048]$) and historical DAG checkouts.
4. **Future Evaluation Path:**
   Evaluating ManiGit against the full external LongMemEval and LoCoMo datasets using hosted foundation models remains an explicit item of future work.
