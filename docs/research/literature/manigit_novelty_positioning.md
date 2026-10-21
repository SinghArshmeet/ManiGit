# ManiGit Novelty & Scientific Positioning

**Project:** ManiGit — Transparent, Versioned Context Memory for Long-Running AI Agents  
**Document:** Novelty Decomposition & Scientific Positioning  
**Date:** October 2026  

---

## 1. Positioning Overview

Scientific progress rarely occurs through ex-nihilo invention; rather, it advances by identifying the structural limitations of existing paradigms, adopting robust principles from adjacent fields, and synthesizing them into a coherent, verifiable architecture.

ManiGit does not claim that version control, token budgets, or text classification are individually novel inventions. Instead, ManiGit's scientific contribution lies in **formulating, implementing, and empirically validating a unified, transparent context-memory architecture** that resolves the acute failure modes of long-running conversational agents.

To ensure academic precision and avoid inflated novelty claims, this document explicitly decomposes ManiGit into five distinct categories:

1. **What ManiGit Inherits**
2. **What ManiGit Combines**
3. **What ManiGit Introduces**
4. **What the Experiments Demonstrate**
5. **What Remains Future Work**

---

## 2. Category Breakdown

### 2.1 What ManiGit Inherits (Prior Art)

ManiGit builds directly upon well-established foundations in computer science and artificial intelligence:

* **From Software Version Control (Git):**
  * The Directed Acyclic Graph (DAG) commit model, where state transitions are represented by parent-linked, cryptographically identified nodes (`SHA-256` content hashes).
  * Branch isolation and branching workflows, enabling speculative explorations without mutating the primary line of development.
  * Point-in-time checkout semantics, allowing state reconstruction at any historical commit $C_k$.
* **From Information Retrieval & RAG:**
  * Lexical indexing and deterministic retrieval (Okapi BM25 and term-frequency scoring) for finding relevant text segments given a query.
* **From Cognitive Architectures & AGM Belief Revision:**
  * The foundational separation between bounded active working memory (the prompt context window) and persistent long-term storage (Newell & Simon, 1972).
  * The principle of rational belief change: incorporating new contradictory information while preserving non-contradictory historical knowledge (Alchourrón et al., 1985).
* **From Knapsack Optimization:**
  * The mathematical formulation of budget-constrained subset selection under additive utility and cost functions.

---

### 2.2 What ManiGit Combines (Novel Integration)

While individual mechanisms have existed in isolation, prior systems kept them disconnected. ManiGit is the first architecture to systematically combine:

1. **Immutable Message Storage + Active Memory DAG:**
   Decoupling the raw chronological conversation transcript (stored append-only in SQLite) from the distilled, active semantic memory state (versioned via parent-linked commits).
2. **Hybrid Rule-First Intake + LLM Judge with Confidence Thresholding:**
   Routing incoming statements through zero-latency deterministic pattern rules for critical constraints and credentials, while passing ambiguous statements to an LLM judge that outputs calibrated confidence scores mapped to explicit functional tiers.
3. **Discrete Lifecycle Tiers + Knapsack Context Selection:**
   Classifying memories into `VERBATIM`, `SUMMARY`, `ARCHIVED`, and `TOMBSTONE` tiers, and applying tier-specific density multipliers during greedy budget compilation.
4. **Contradiction Detection + Auditable Why Reports:**
   Automatically detecting factual supersession between new incoming memories and active memories, archiving the superseded memory, and generating an immutable audit trail explaining the exact reason for the transition.

---

### 2.3 What ManiGit Introduces (Original Contributions)

ManiGit introduces specific architectural and methodological mechanisms previously absent in agent memory literature:

1. **Automated, Transparent Context Memory Lifecycle:**
   Unlike prior Git-inspired agent projects (e.g., Git Context Controller, GitOfThoughts) which require the LLM agent to manually execute `COMMIT`, `BRANCH`, and `MERGE` tool calls, ManiGit operates as a **transparent infrastructure layer**. Memory extraction, classification, DAG committing, and context compilation happen automatically in the background, consuming zero agent tool-calling turns and zero prompt overhead.
2. **The Four-Tier Context Memory Model:**
   A formalized state machine (`VERBATIM`, `SUMMARY`, `ARCHIVED`, `TOMBSTONE`) specifically designed for conversational agents, preventing memory drift by ensuring that superseded or refuted facts are cleanly quarantined from active prompt compilation while remaining accessible for historical reconstruction.
3. **Formal Mathematical Context Compilation under Token Budgets:**
   Formulating prompt context construction as a constrained knapsack problem:
   $$\max_{C_t \subseteq M_t} \sum_{m_i \in C_t} U(m_i, q_t) \quad \text{subject to} \quad \sum_{m_i \in C_t} L(m_i) \le B$$
   and providing a deterministic greedy score-density approximation that prioritizes relevance and tier weights while guaranteeing zero budget violations ($C_t \le B$).
4. **First-Class Point-in-Time Context Checkout:**
   The capability to instantly reconstruct the active memory state as of any historical commit $C_k$ and compile a budget-compliant context window for that exact historical moment, resolving the auditability gap inherent in destructive CRUD memory stores.
5. **Bidirectional Why Reports for Memory Auditing:**
   Every memory fact is permanently linked to its originating message ID and accompanied by an explicit Why Report recording the classification rule, LLM confidence score, and supersession target.

---

### 2.4 What the Experiments Demonstrate (Empirical Validation)

Across 880 controlled benchmark trials (22 queries $\times$ 8 methods/ablations $\times$ 5 budgets), the empirical evaluation establishes:

* **Token Efficiency (H1 Confirmed):** ManiGit Full achieves **86.4% fact recall** [95% CI: 78.7%, 91.6%] while consuming an average of **170.2 context tokens**—a **43.0% reduction** compared to Full History (298.4 tokens) and 13.7% fewer tokens than RAG (197.2 tokens).
* **Historical Reconstruction (H2 Confirmed):** ManiGit achieves **100.0% historical recovery** across all evaluation budgets, whereas baseline RAG, Sliding Window, and Running Summary achieve 0.0% on historical queries after factual supersession.
* **Causal Impact of Contradiction Handling (H3 Confirmed):** Ablating contradiction handling (`no_contradiction`) causes a statistically verified **-5.0% drop** in overall answer correctness, dropping to 50.0% on database migration scenarios where stale facts pollute the prompt.
* **Causal Impact of Confidence Thresholds (H4 Confirmed):** Ablating confidence awareness (`no_confidence`) causes a **-5.0% drop** in factual recall and correctness, failing completely (0.0%) on speculative, ambiguous statements.
* **Causal Impact of Memory Tiers (H5 Confirmed):** Ablating tier boosts (`no_tier`) reduces factual recall to 0.0% under ultra-tight budgets ($B=128$) when concise verbatim constraints compete against verbose summaries.
* **Budget Invariant:** Zero budget violations across all 880 trials (100% compliance).

---

### 2.5 What Remains Future Work (Explicit Boundaries)

To maintain scientific humility, the following areas are acknowledged as beyond the scope of ManiGit's current reference implementation:

1. **Dense & Hybrid Vector Retrieval:** The current reference engine uses deterministic lexical scoring (BM25); integrating dense embeddings and learned re-ranking without sacrificing deterministic budget guarantees is future work.
2. **Stochastic Foundation Model Evaluation:** Benchmarks were conducted using deterministic rule and calibrated mock model adapters to ensure rigorous ablation control; evaluating against hosted foundation models (GPT-4o, Claude 3.5, Gemini 1.5) under stochastic conditions is planned.
3. **Real-World Conversational Traces:** Evaluation currently relies on synthetic multi-turn micro-scenarios; testing on open-ended human-agent interaction corpora (e.g., LongMemEval) remains future work.
4. **Human Subject Evaluation:** Correctness was graded programmatically against ground-truth fact assertions; blinded human expert evaluation of agent responses is an important next step.
5. **Cross-Agent Branch Merging:** Exploring automatic three-way merges when multiple parallel sub-agents commit conflicting memories to divergent branches.
