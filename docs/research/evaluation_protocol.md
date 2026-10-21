# ManiGit Research Evaluation Protocol

## 1. Research Question

**Primary Question:**  
“Under constrained context budgets, does versioned, provenance-aware, budget-aware memory selection improve historical information retention and context efficiency compared with conventional approaches?”

**Sub-Questions:**
1. Does versioned memory commit history allow recovery of superseded historical states that running summaries or sliding windows lose?
2. Does greedy token-budget packing over classified memory units yield higher important-fact recall than naive message truncation under tight budgets ($B \le 256$ tokens)?
3. How do the context overheads of ManiGit scale relative to full-history and raw message RAG as conversation length increases ($T \ge 100$ turns)?

---

## 2. Research Hypotheses

*All hypotheses are formulated as empirical research propositions to be tested experimentally, not foregone conclusions.*

- **Hypothesis 1 (H1 — Low-Budget Retention):**  
  Under a constrained context budget of $B=128$ tokens, ManiGit achieves higher critical fact recall than naive full-history truncation evaluated under the identical $B=128$ budget constraint (empirically $85.0\%$ fact recall consuming $79.2$ average context tokens for ManiGit vs. $75.0\%$ fact recall consuming $109.9$ average context tokens for Full History). Across all five evaluated budgets ($B \in \{128, 256, 512, 1024, 2048\}$), ManiGit achieves $85.0\%$ aggregate fact recall consuming $179.5$ average context tokens, compared to Full History's $82.0\%$ aggregate fact recall consuming $317.3$ average context tokens.

- **Hypothesis 2 (H2 — Historical Recovery):**  
  ManiGit recovers superseded historical facts more reliably than running summaries and sliding windows through explicit DAG-based historical state reconstruction.

- **Hypothesis 3 (H3 — Context Token Efficiency):**  
  ManiGit consumes fewer context tokens per query than full-history concatenation while achieving comparable or superior answer correctness.

- **Hypothesis 4 (H4 — Contradiction Disambiguation):**  
  ManiGit's explicit tiering and supersession mechanics differentiate current active state from superseded historical state with higher precision than flat conversational summaries.

- **Hypothesis 5 (H5 — Long Conversation Scalability):**  
  As dialogue length increases ($T = 50 \to 100 \to 250+$ turns), sliding window and full-history recall decay rapidly, while ManiGit's classified memory selection sustains stable recall.

---

## 3. Experimental Methodology

The evaluation framework executes controlled, multi-trial experiments across an orthogonal matrix of evaluation methods, context budgets, and dialogue scenarios.

### Matrix Dimensions & Trial Cardinality:
- **Scenario Categories (8):** Stable facts, superseding facts, exact constraints, architectural decisions, technical identifiers/paths, conversational distractors, duplicate statements, and scaled long conversations.
- **Scenario Instances (9):** A, B, C, D, E, F, G, H-50, and H-100.
- **Evaluation Queries (20):**
  - Scenario A: 2 queries
  - Scenario B: 2 queries
  - Scenario C: 2 queries
  - Scenario D: 2 queries
  - Scenario E: 3 queries
  - Scenario F: 2 queries
  - Scenario G: 1 query
  - Scenario H-50: 3 queries
  - Scenario H-100: 3 queries
- **Methods (5):** Full History, Sliding Window ($N=10$), Running Summary, RAG-Style (Raw Messages), ManiGit (Full).
- **Context Budgets (5):** $B \in \{128, 256, 512, 1024, 2048\}$ tokens.
- **Total Canonical Trial Cardinality:**  
  $$\text{Total Trials} = 20 \text{ queries} \times 5 \text{ methods} \times 5 \text{ budgets} = 500 \text{ trials}$$
  *(Note: There are 20 discrete probe queries evaluated across the 9 scenario instances, yielding 100 trials per evaluation method).*

---

## 4. Baselines

All baseline methods are implemented as evaluation-layer wrappers in `src/manigit/evaluation/baselines.py` and strictly preserve core architecture immutability:

1. **Full History Baseline (`FullHistoryBaseline`):**
   - Accumulates raw dialogue messages from turn 0 chronologically until budget $B$ is reached.
   - Represents unmanaged conversational memory.

2. **Sliding Window Baseline (`SlidingWindowBaseline`):**
   - Retains the most recent $N=10$ turns within budget $B$.
   - Represents standard bounded session buffers.

3. **Running Summary Baseline (`SummaryBaseline`):**
   - Condenses conversation into a running summary block, packing it into budget $B$.
   - Represents conventional single-tier summary agents.

4. **RAG-Style Baseline (`RAGStyleBaseline`):**
   - Computes deterministic lexical term-overlap scores between the query and raw conversational turns.
   - Greedily selects top-scoring raw message turns into budget $B$.
   - Does *not* have access to ManiGit's structured tiers, Why Reports, or commit graph.

5. **ManiGit Evaluation Path (`ManiGitEvaluationMethod`):**
   - Executes scenario turns through `AgentRuntime`, persisting immutable messages, extracting classified memories (`VERBATIM`, `SUMMARY`), recording Why Reports, and committing state.
   - Compiles budgeted context via `ContextCompiler`.
   - Supports historical state queries via `commit_id` targeting without HEAD state leakage.

---

## 5. Dataset & Benchmark Scenario Construction

Scenarios are deterministically synthesized in `src/manigit/evaluation/scenarios.py` to mirror realistic long-running agent challenges:

| Scenario ID | Category | Turns | Queries | Focus Area |
| :--- | :--- | :---: | :---: | :--- |
| `scenario_a_stable_facts` | Stable Facts | 8 | 2 | PostgreSQL DB, Argon2id hashing |
| `scenario_b_superseding_facts` | Supersession | 8 | 2 | PostgreSQL $\to$ MongoDB migration (current vs historical) |
| `scenario_c_exact_constraints` | Exact Constraints | 6 | 2 | 500 ms timeout, 16 worker pool |
| `scenario_d_decisions` | Decisions | 6 | 2 | JWT authentication, Event Sourcing architecture |
| `scenario_e_technical_facts` | Technical Facts | 6 | 3 | `/etc/manigit/runtime.conf`, `ERR_SOCKET_TIMEOUT_902`, `/api/v2/telemetry/events` |
| `scenario_f_distractors` | Distractors | 54 | 2 | Cache port 6379, cluster `us-central1-k8s-prod` among chit-chat |
| `scenario_g_duplicates` | Duplicates | 16 | 1 | 90-day retention repeated 4 times with filler |
| `scenario_h_long_50` | Scaled Long | 50 | 3 | Early (turn 0), mid (turn 25), and late (turn 46) facts |
| `scenario_h_long_100` | Scaled Long | 100 | 3 | Early (turn 0), mid (turn 50), and late (turn 96) facts |

---

## 6. Metrics & Mathematical Formulation

The mathematical formulation established in Phase 3 defines context compilation as:

$$\max_{C_t \subseteq M_t} \sum_{m_i \in C_t} U(m_i, q_t) \quad \text{subject to} \quad \sum_{m_i \in C_t} L(m_i) \le B$$

Evaluation directly connects to this formulation through:

1. **Context Token Count ($C_{\text{tok}}$):** $\sum_{m_i \in C_t} L(m_i)$
2. **Context Budget Utilization ($U_B$):** $\frac{C_{\text{tok}}}{B}$
3. **Important-Fact Recall ($R_{\text{fact}}$):** $\mathbb{I}[\text{expected fact} \in \text{Compiled Context}]$
4. **Answer Correctness ($A_{\text{corr}}$):** $\mathbb{I}[\text{expected answer} \in \text{Model Output}]$
5. **Historical Recovery Accuracy ($H_{\text{acc}}$):** Recall of superseded fact when querying historical commit state.
6. **Contradiction Differentiation ($C_{\text{acc}}$):** Context distinguishes active vs superseded facts without conflation.
7. **Retrieval Precision ($P_{\text{ret}}$):** $\frac{|\text{Retrieved} \cap \text{Relevant}|}{|\text{Retrieved}|}$
8. **Retrieval Recall ($R_{\text{ret}}$):** $\frac{|\text{Retrieved} \cap \text{Relevant}|}{|\text{Relevant}|}$
9. **Latency Metrics:** Context compilation latency ($\tau_{\text{ctx}}$), model generation latency ($\tau_{\text{gen}}$), total latency ($\tau_{\text{total}}$).

---

## 7. Experimental Controls & Variables

- **Independent Variables:**
  - Memory / Context Strategy (`method`)
  - Token Budget $B \in \{128, 256, 512, 1024, 2048\}$
  - Conversation Length $T \in \{6, 8, 16, 50, 54, 100\}$
- **Dependent Variables:**
  - Fact recall, answer correctness, context tokens, total tokens, precision, recall, latency.
- **Controlled Variables:**
  - Identical scenario dialogue history presented to all methods.
  - Identical query formulation.
  - Identical token budget constraint $B$.
  - Identical evaluation adapter (`MockModelAdapter` with deterministic prompt extraction logic).
  - Identical token estimation routine (`estimate_tokens`).
  - Fixed pseudorandom seeds (`seed=42`).

---

## 8. Reproducibility Protocol

1. **Deterministic Execution:**  
   Execute via CLI:
   ```powershell
   uv run python -m manigit.evaluation.run_experiments
   ```
2. **Ledger Storage:**  
   Every trial record is serialized with experiment ID, timestamps, query metadata, retrieved indices, and exact metrics in `data/processed/benchmarks/results/<experiment_id>.json`.
3. **Automated Verification:**  
   Automated unit and integration test suite enforces reproducibility:
   ```powershell
   uv run pytest -v
   ```

---

## 9. Limitations

1. **Synthetic Dialogue:** Current scenarios use deterministic synthetic dialogue rather than human multi-day transcripts.
2. **Mock Evaluator:** Initial experiments evaluate system-level context compilation precision using deterministic extraction rather than a frontier LLM judge (such as Gemini 1.5 Pro).
3. **Fixed Window Heuristic:** Sliding window baseline uses $N=10$, which may be suboptimal for very short or very long turns.

---

## 10. Threats to Validity

- **Internal Validity:** Lexical matching in the RAG baseline uses Jaccard token overlap; differences in tokenization could affect raw message ranking.
- **External Validity:** Synthetic scenarios represent clean engineering constraints; conversational drift in unconstrained human dialogues may present more ambiguous contradiction signals.
- **Construct Validity:** Fact presence in compiled context is a necessary but not always sufficient condition for open-ended LLM reasoning; live LLM evaluations are needed for nuanced qualitative answers.
