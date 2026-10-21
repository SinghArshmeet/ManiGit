# Comprehensive Comparison Matrix of Agent Memory Systems

**Project:** ManiGit — Transparent, Versioned Context Memory for Long-Running AI Agents  
**Document:** System Comparison Matrix  
**Date:** October 2026  

---

## 1. Legend

* **✓ (Full):** The capability is a primary, first-class design feature explicitly implemented and evaluated.
* **Partial:** The capability is addressed through heuristics, third-party libraries, partial metadata, or manual agent tool calls, but lacks formal guarantees.
* **— (Not Present):** The capability is explicitly not supported by the system architecture.
* **Not Reported:** The feature is neither mentioned nor evaluated in the primary literature.

---

## 2. System Comparison Table

| System | Year | Raw Memory | Summarization | Retrieval | Reflection | Structured Memory | Memory Evolution | Versioning | Branching | Provenance | Contradiction Handling | Historical Reconstruction | Budget-Aware Context | Human Inspection | Decision Trace | Evaluation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Newell & Simon** | 1972 | — | — | ✓ | — | ✓ | Partial | — | Partial | — | Partial | — | ✓ | ✓ | — | Protocol analysis |
| **AGM Logic** | 1985 | — | — | Partial | — | ✓ | ✓ | — | — | Partial | ✓ | — | — | ✓ | — | Theoretical proof |
| **Neural Turing Mach.** | 2014 | — | — | ✓ | — | — | Partial | — | — | — | Partial | — | ✓ | — | — | Synthetic algorithmic |
| **Memory Networks** | 2014 | ✓ | — | ✓ | — | — | — | — | — | Partial | — | — | Partial | — | — | bAbI QA tasks |
| **Diff. Neural Comp.** | 2016 | — | — | ✓ | — | — | Partial | Partial | — | — | Partial | Partial | ✓ | — | — | Graph reasoning |
| **Transformer (Vanilla)**| 2017 | ✓ | — | ✓ | — | — | — | — | Partial | — | — | Partial | ✓ | — | — | Machine translation |
| **REALM** | 2020 | — | — | ✓ | — | — | — | — | — | Partial | — | — | Partial | ✓ | — | Open-domain QA |
| **RAG (Lewis et al.)** | 2020 | — | — | ✓ | — | — | — | — | — | Partial | — | — | Partial | ✓ | — | Open-domain QA |
| **Sliding Window** | 2022 | ✓ | — | — | — | — | — | — | — | — | — | — | Partial | ✓ | — | Heuristic buffer |
| **Running Summary** | 2022 | — | ✓ | — | — | — | Partial | — | — | — | Partial | — | Partial | ✓ | — | Heuristic buffer |
| **Generative Agents** | 2023 | ✓ | ✓ | ✓ | ✓ | — | Partial | — | — | Partial | — | — | Partial | ✓ | — | Sandbox simulation |
| **MemGPT** | 2023 | ✓ | Partial | ✓ | — | Partial | ✓ | — | — | — | Partial | — | Partial | ✓ | — | Multi-session chat |
| **Reflexion** | 2023 | — | Partial | — | ✓ | — | Partial | — | — | Partial | — | — | Partial | ✓ | Partial | Agent benchmarks |
| **MemoryBank** | 2023 | — | ✓ | ✓ | — | Partial | ✓ | — | — | — | Partial | — | Partial | ✓ | — | Dialogue recall |
| **LongMem** | 2023 | — | — | ✓ | — | — | — | — | — | — | — | — | Partial | — | — | Long-text modeling |
| **Mem0** | 2024 | — | Partial | ✓ | — | ✓ | ✓ | Partial | — | Partial | Partial | Not reported | Partial | ✓ | — | Personalization tasks |
| **HippoRAG** | 2024 | — | — | ✓ | — | ✓ | Partial | — | — | Partial | — | — | Partial | ✓ | — | Multi-hop QA |
| **A-MEM** | 2024 | — | Partial | ✓ | Partial | ✓ | ✓ | Partial | — | Partial | Partial | — | Partial | ✓ | — | Multi-hop synthesis |
| **GCC (Wu et al.)** | 2025 | ✓ | Partial | Partial | — | Partial | Partial | ✓ | ✓ | Partial | Partial | Partial | Partial | ✓ | — | SWE-bench Lite |
| **GitOfThoughts** | 2025 | — | — | Partial | — | Partial | — | ✓ | ✓ | ✓ | — | ✓ | — | ✓ | — | Math reasoning |
| **TOKI** | 2025 | — | — | ✓ | — | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | — | ✓ | Partial | Concurrency tests |
| **ManiGit (This Work)**| 2026 | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Controlled benchmark |

---

## 3. Key Observations & Systematic Takeaways

1. **The Versioning & Provenance Void in Mainstream Frameworks:**
   Despite widespread adoption, prominent agent frameworks (MemGPT, Generative Agents, Mem0) do not implement formal commit versioning, branch DAGs, or cryptographic provenance. State mutations in MemGPT and Mem0 are destructive in-place text replacements or SQL updates.
2. **Emergence of Git Metaphors in 2025:**
   GCC (Wu et al., 2025) and GitOfThoughts (Shekar et al., 2025/2026) validated the utility of Git concepts for coding workspaces and reasoning trees. However, both systems treat Git as an explicit, user/agent-invoked tool command rather than an automated, transparent context-compilation engine with four-tier memory representations.
3. **The Unaddressed Knapsack Context Selection:**
   Existing systems universally employ top-$k$ similarity truncation or fixed memory slot blocks. ManiGit is unique in formalizing context compilation as a bounded knapsack optimization problem under strict, pre-allocated token budgets.
4. **ManiGit's Architectural Unification:**
   ManiGit is the first system to integrate:
   - Automated rule/judge memory classification into four functional tiers.
   - Non-destructive, immutable message archiving and SQLite commit DAGs.
   - Automated contradiction detection with supersession Why Reports.
   - Point-in-time historical reconstruction.
   - Greedy knapsack context compilation under hard token budgets.
