# Research Limitations & Scope Boundaries

Transparent research requires explicit documentation of empirical constraints, methodological assumptions, and known limitations. ManiGit is designed as a principled, version-controlled memory architecture; the findings reported in Phase 8 must be interpreted in light of the following boundary conditions:

---

## 1. Synthetic Benchmark Domain
- **Nature of Scenarios**: The benchmark evaluation suite consists of 11 handcrafted synthetic conversation scenarios (22 queries, 880 total ablation trials). While synthetic scenarios allow precise, controlled measurement of specific mechanisms (such as token boundaries, supersession pairs, and distractor noise), they do not capture the messy, unstructured complexity of organic human-agent conversations.
- **Distributional Assumptions**: Real dialogue displays non-uniform topic drift, multi-turn implicit corrections, colloquial idioms, and non-literal intent that synthetic benchmarks do not fully replicate.

## 2. Deterministic & Mock Model Evaluation
- **Offline Adapter**: To guarantee 100% deterministic reproducibility, zero flaky network calls, and eliminate non-deterministic LLM variance, the primary benchmark utilizes `MockModelAdapter`.
- **Heuristic Boundaries**: While the mock adapter faithfully simulates factual extraction from compiled context and adheres strictly to prompt-contained facts, actual frontier LLMs (such as Gemini 1.5/2.0 or GPT-4) may exhibit subtle reasoning quirks, hallucination tendencies under incomplete context, or different tokenization distributions.

## 3. Finite Sample Size & Statistical Power
- **Sample Scale**: The benchmark matrix comprises 880 total trials across 8 methods, 5 budgets, and 22 queries. Each individual method is evaluated across 110 trials.
- **Confidence Interval Breadth**: While 95% Wilson score confidence intervals are provided for all proportions, the sample size produces interval widths of approximately $\pm 6.5\%$ for overall rates. Statistical conclusions must be interpreted as descriptive evidence of mechanism contributions within this suite rather than asymptotic claims of universal significance.

## 4. Deterministic Lexical Retrieval vs. Semantic Dense Embeddings
- **Design Decision**: In accordance with the foundational architectural constraints of ManiGit, the system employs exact token-overlap lexical scoring and heuristic priority ranking rather than dense vector embeddings or a vector database.
- **Trade-offs**: Lexical retrieval guarantees instant, zero-cost, local execution without external vector infrastructure or embedding drift. However, it cannot perform semantic generalization over synonyms or paraphrases that share zero lexical tokens (e.g., matching "physician" to "doctor") without explicit rules or judge intervention.

## 5. Non-Universal Superiority
- **No Free Lunch**: ManiGit does NOT claim universal superiority across all conversational settings. When context budgets are completely unconstrained ($B \ge 2048$) and conversation histories are brief ($<10$ turns), simple Full History concatenation is simpler and achieves equal recall without commit overhead.
- **Niche of Advantage**: ManiGit's measurable advantages emerge specifically under **tight token budgets**, **long conversations with distractor noise**, **superseded facts requiring time travel**, and **explicit provenance auditing**.

## 6. Human Evaluation Not Established
- **Automated Grading**: All trial outcomes are evaluated via automated exact-match and alternative-key grading functions.
- **Absence of Qualitative Human Study**: No longitudinal user studies or human qualitative evaluations of agent responsiveness, conversational naturalness, or subjective coherence have been conducted yet.

## 7. Scaling and Concurrency Limits
- **Single-Node SQLite Architecture**: ManiGit is intentionally implemented over local, embedded SQLite to guarantee single-file transparency and zero cloud dependencies. It is not engineered for high-throughput distributed microservice clusters with hundreds of concurrent agent write-threads.
- **DAG Depth**: While DAG commit chains of up to 100 turns have been validated with sub-millisecond retrieval latency, performance over 10,000+ sequential commits in a single branch without database reindexing remains unbenchmarked.
