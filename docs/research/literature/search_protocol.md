# Systematic Literature Search Protocol

**Project:** ManiGit — Transparent, Versioned Context Memory for Long-Running AI Agents  
**Phase:** Phase 9 (Literature Research & Academic Paper Preparation)  
**Date:** October 2026  
**Protocol Version:** 1.0  

---

## 1. Objectives

The primary goal of this systematic literature review is to ground ManiGit within the academic context of artificial intelligence, natural language processing, cognitive architectures, and agent state management. Specifically, the search protocol addresses:

1. **Historical Evolution:** Tracing the transition from symbolic production rules, classical belief revision, and neural memory networks to Retrieval-Augmented Generation (RAG), long-context language models, and modern multi-session LLM agent memory architectures.
2. **Current State of the Art (2023–2026):** Cataloging leading agent memory frameworks (e.g., MemGPT, Generative Agents, MemoryBank, Mem0, HippoRAG, A-MEM, Git Context Controller, GitOfThoughts).
3. **Research Gaps & Novelty Counterexample Search:** Actively searching for prior systems that claim git-like versioning, explicit contradiction/supersession handling, provenance tracking, historical point-in-time reconstruction, and budget-constrained context selection.
4. **Evaluation Landscape:** Examining standardized agent memory benchmarks (e.g., LongMemEval, LoCoMo, STALE, BAMBOO) to contextualize ManiGit's controlled experimental evaluation.

---

## 2. Information Sources & Databases

Searches were conducted across primary academic indexing services and preprint servers:
- **arXiv.org** (Computer Science: Computation and Language [cs.CL], Artificial Intelligence [cs.AI], Software Engineering [cs.SE])
- **ACL Anthology** (ACL, EMNLP, NAACL, EACL, Findings)
- **ACM Digital Library** (UIST, KDD, SIGMOD, TOIS)
- **IEEE Xplore** (TKDE, ICDE, Access)
- **OpenReview.net** (ICLR, NeurIPS, ICML)
- **Semantic Scholar & Google Scholar** for citation graph traversal and backward/forward snowballing.

---

## 3. Search Families & Query Syntax

The search was structured into seven conceptual families executed across the aforementioned engines:

### Family 1: LLM Agent Memory & Foundations
- `"LLM agent memory" OR "agent memory architecture"`
- `"long-term memory" AND ("LLM agents" OR "AI agents")`
- `"persistent memory" AND ("language model" OR "conversational agent")`
- `"agent memory management" AND ("multi-session" OR "lifelong learning")`

### Family 2: Memory Paradigms & Cognitive Architectures
- `"episodic memory" AND "semantic memory" AND "LLM"`
- `"reflection" AND "memory consolidation" AND "generative agents"`
- `"hierarchical memory" AND "agent operating system"`
- `"graph memory" OR "knowledge graph" AND "agent memory"`

### Family 3: Context Management & Retrieval
- `"context window management" AND "token budget"`
- `"retrieval-augmented generation" AND ("context selection" OR "context compression")`
- `"knapsack" OR "budget-aware" AND "context selection" AND "LLM"`
- `"long-context language models" AND ("retrieval vs context" OR "lost in the middle")`

### Family 4: Contradiction, Belief Revision, & Memory Updates
- `"belief revision" AND "LLM" AND ("agent memory" OR "knowledge update")`
- `"memory contradiction" OR "supersession" AND "LLM agents"`
- `"stale memory" OR "conflicting facts" AND "conversational memory"`
- `"AGM belief revision" AND "language models"`

### Family 5: Versioning, Auditing, & Git-Based Approaches (Counterexample Search)
- `"versioned memory" AND ("LLM" OR "AI agent")`
- `"git" AND ("agent memory" OR "context management" OR "reasoning tree")`
- `"git context controller" OR "git of thoughts"`
- `"memory provenance" OR "auditability" AND "LLM agent"`
- `"historical reconstruction" OR "time travel" AND "agent memory"`

### Family 6: Long-Term Memory Benchmarks
- `"LongMemEval" OR "LoCoMo" benchmark`
- `"agent memory benchmark" AND ("multi-session" OR "temporal reasoning")`
- `"STALE benchmark" OR "HaluMem" OR "BAMBOO"`

### Family 7: Classical Foundations & Historical Precedents
- `"Neural Turing Machines" OR "Differentiable Neural Computer"`
- `"Memory Networks" Weston Chopra Bordes`
- `"production systems" "working memory" Newell Simon`

---

## 4. Date Range & Language Criteria

- **Temporal Coverage:** 1972 to October 2026.
  - *Classical & Pre-LLM Foundations:* 1972–2022 (selective foundational works).
  - *Modern LLM Agent Memory:* January 2023 – October 2026 (comprehensive coverage).
- **Language:** English only.

---

## 5. Inclusion & Exclusion Criteria

### Inclusion Criteria:
1. Primary research papers proposing novel memory architectures, storage representations, retrieval mechanisms, or update algorithms for LLM-based agents.
2. Peer-reviewed surveys systematizing memory mechanisms, cognitive architectures, or security/governance in LLM agents.
3. Standardized evaluation benchmarks specifically measuring multi-session memory, temporal reasoning, or factual update tracking in agents.
4. Classical foundational literature establishing formal memory paradigms (working memory, neural external memory, belief revision theory).
5. Explicit counterexamples implementing git-inspired, version-controlled, or provenance-auditable context management for LLMs.

### Exclusion Criteria:
1. Non-peer-reviewed blog posts, corporate marketing summaries, and informal tutorials lacking formal architectural specifications.
2. Generic RAG implementations without persistent agent state or temporal evolution (static document question-answering).
3. Model-internal parameter-tuning methods (e.g., LoRA, fine-tuning) unless framed specifically as parametric memory mechanisms.
4. Work focusing exclusively on hardware/silicon memory hierarchies (e.g., SRAM/DRAM, GPU memory paging) unrelated to agent context.
5. Incomplete preprints with unsubstantiated empirical claims lacking replicable artifacts or open specifications.

---

## 6. Duplicate Handling & Primary Source Preference

- In cases where an arXiv preprint was subsequently published in a peer-reviewed venue (e.g., ACL, EMNLP, NeurIPS, UIST), the peer-reviewed conference/journal version is prioritized for citation metadata and DOI tracking, with the original arXiv ID retained for open-access traceability.
- Redundant workshop versions of papers that expanded into main conference publications are merged into the final conference record.
- Primary authors and official tool repositories are cited directly; third-party re-implementations are explicitly identified as derivatives.

---

## 7. Active Search for Novelty Counterexamples

To prevent confirmation bias, specific adversarial queries were formulated to identify whether ManiGit's key claims were already anticipated or implemented in the literature:

1. *Has Git been used to version agent memory?*
   - **Discovered Systems:**
     - **Git Context Controller (GCC)** (Wu et al., Aug 2025, arXiv:2508.00031): Equips agents with explicit tool commands (`COMMIT`, `BRANCH`, `MERGE`, `CONTEXT`) to manage Markdown files in a `.GCC/` directory for long-horizon software engineering.
     - **GitOfThoughts** (Shekar et al., Jun 2025/2026, arXiv:2606.14470): Maps Tree-of-Thoughts reasoning nodes to Git commits, using `git log` and `git diff` for auditing and mergeable mathematical problem solving.
   - **Differentiation Analysis:** Neither system provides automated background memory extraction, hybrid rule/judge classification with confidence thresholds, four-tiered memory states (VERBATIM, SUMMARY, ARCHIVED, TOMBSTONE), automatic conflict detection/supersession, or deterministic greedy token-budget knapsack compilation.

2. *Have bitemporal or transactional update controls been applied to agent memory?*
   - **Discovered Systems:**
     - **TOKI** (2025): Bitemporal concurrency control and provenance annotations in write-heavy persistent agent memory.
     - **BeliefMem / Nous** (2024/2025): Bayesian probability distributions over entity-attribute conclusions to resolve contradictory evidence.
   - **Differentiation Analysis:** These frameworks model belief uncertainty or database concurrency but do not combine immutable raw message archiving with git-like branch DAGs, historical commit checkout, and budget-constrained greedy context compilation.

---

## 8. Corpus Management

All qualifying papers are cataloged in:
- `docs/research/literature/literature_database.json`
- `docs/research/literature/literature_database.csv`

Every entry includes 24 structured metadata attributes enabling reproducible quantitative and qualitative synthesis.
