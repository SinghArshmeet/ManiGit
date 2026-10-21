# ManiGit: Architecture & Conceptual Overview

> **Transparent, Versioned Context Memory for Long-Running AI Agents**

---

## 1. What ManiGit Is

**ManiGit** is a version-controlled memory architecture for AI agents. It applies Git-inspired version control semantics—commits, branches, diffs, checkouts, and provenance tracking—to agent memory. 

Rather than treating context as a fragile, opaque buffer that gets silently truncated or compressed, ManiGit separates raw conversation history from the active memory state and treats every memory transition as an auditable, reversible commit.

---

## 2. The Problem It Solves

Long-running AI agents face severe degradation when engaging across extended, multi-session interactions:
1. **Context Window Saturation & Cost:** Sending thousands of previous tokens increases latency and cost linearly or quadratically.
2. **Loss of Salient Information:** Common heuristics like sliding-window truncation drop early foundational constraints (e.g., user preferences, API keys, system rules).
3. **Opaque Summarization & Hallucination Drift:** Blanket summarization blurs exact figures, error codes, and IDs. Once a summary introduces an error, the agent accepts it as truth with no way to trace or roll back.
4. **Irreversibility & Lack of Explainability:** When an agent misinterprets a turn or retains incorrect knowledge, users cannot inspect *why* it was retained, nor can they surgically revert the agent's memory to an earlier valid state.

---

## 3. Core Architecture

ManiGit is designed around four foundational architectural pillars:
- **Immutable Append-Only Message Archive:** Every user prompt and assistant output is recorded permanently with monotonic sequence IDs and timestamps. Nothing is deleted from raw history.
- **Explicit Versioned Memory State:** Active knowledge is modeled as discrete memory units (facts, summaries, constraints). State mutations are bundled into atomic **Commits** forming a Directed Acyclic Graph (DAG) via parent references.
- **Budget-Aware Context Compilation:** Memory is compiled into model prompt context on demand, prioritizing pinned items, topical summaries, and a recent verbatim window under a strict token budget.
- **Explainability & Human In The Loop:** Every memory update produces a "Why Report" detailing the operation applied, rationale, confidence, and token count impact. Humans can pin, trim, or hand-edit memories, creating new auditable commits.

```
+-----------------------------------------------------------------------+
|                             USER / CLI / UI                           |
+-----------------------------------------------------------------------+
                                  │
                                  ▼
                    +---------------------------+
                    |       Agent Runtime       |
                    +---------------------------+
                     │            │           │
     1. Append Raw   │            │ 2. Read   │ 5. Commit State
        History      ▼            ▼    Memory ▼    & Why Report
+-----------------------+     +-------------------------------+
|  Raw Messages Archive |     |    Core Memory Repository     |
|   (Immutable SQLite)  |     | (Commits, Branches, DAG, DB)  |
+-----------------------+     +-------------------------------+
                                  ▲               ▲
                      3. Compile  │               │ 4. Classify &
                         Context  │               │    Propose Edits
                                  │               │
                    +--------------------+ +--------------------+
                    |  Context Compiler  | | Memory Intelligence|
                    +--------------------+ +--------------------+
                                  │               │
                                  ▼               ▼
                    +-------------------------------------------+
                    |          Model Adapter (Agnostic)         |
                    +-------------------------------------------+
```

---

## 4. Difference Between Memory and Context

A fundamental architectural distinction in ManiGit is that **Memory is NOT Context**:

| Attribute | Memory | Context |
| :--- | :--- | :--- |
| **Definition** | The persistent, versioned repository of all knowledge the agent has acquired. | The ephemeral, budgeted prompt payload passed to an LLM for a specific turn. |
| **Lifespan** | Long-lived, persistent, structured in SQLite across sessions. | Short-lived, generated just-in-time for a single inference call. |
| **Capacity** | Unbounded (stored relationally on disk). | Strictly bounded by token budget (e.g., 4,096 or 8,192 tokens). |
| **Structure** | Commits, memory units, parent links, branches, and diffs. | Structured prompt blocks (System prompt, Pinned, Summaries, Recent window). |

---

## 5. Difference Between Raw History and Active Memory

ManiGit strictly separates **Raw History** from **Active Memory**:

- **Raw History (The Immutable Log):**
  - An append-only sequence of all raw interactions (user messages, tool outputs, model responses).
  - Never deleted, truncated, or modified.
  - Serves as the ground-truth audit trail from which any past state can be audited or reconstructed.
- **Active Memory (The Versioned Working State):**
  - The curated set of active knowledge units (constraints, facts, summaries, decisions).
  - Modified via explicit commits (Add, Update, Discard/Tombstone).
  - When information is "discarded," it is removed from active memory views but retained in raw history with a tombstone record explaining why it was superseded.

---

## 6. Major System Components

1. **Core / Memory Repository (`src/manigit/core/`):**
   - Manages SQLite persistence, table schemas, and relational commit DAG.
   - Handles commits, branch references (`HEAD`, `main`), and state reconstruction at any commit hash.
2. **Memory Intelligence (`src/manigit/memory/`):**
   - Evaluates incoming exchanges and determines what to keep verbatim, summarize, or discard.
   - Generates confidence scores, provenance pointers to raw message IDs, and detects contradictions.
3. **Context Compiler (`src/manigit/context/`):**
   - Retrieves active memory units, ranks them, and packs them into prompt context adhering to a strict token budget.
4. **Model Adapter (`src/manigit/models/`):**
   - Provider-agnostic abstraction for LLM interactions (`generate`, `summarize`, `judge_memory`, `count_tokens`).
5. **Agent Runtime (`src/manigit/agent/`):**
   - Coordinates the loop: message ingress → retrieval → context assembly → inference → memory judgment → commit.
6. **Evaluation Framework (`src/manigit/evaluation/`):**
   - Provides repeatable benchmark suites and baseline comparisons.
7. **CLI & Web UI (`src/manigit/cli/`, `web/`):**
   - User interfaces for inspection, branching, merging, and visual exploration of commit DAGs.

---

## 7. Planned Data Flow

For every interaction turn in the agent runtime:
```
[User Message]
       │
       ▼
[Step 1: Ingest & Persist Raw] ──────> Store in messages table (immutable)
       │
       ▼
[Step 2: Context Compilation] ───────> Fetch current branch HEAD memory records
       │                               Pack: Pinned -> Topical Summaries -> Recent Verbatim
       │                               Validate against Token Budget
       ▼
[Step 3: Model Inference] ───────────> Model Adapter calls LLM with compiled context
       │                               Obtain Agent Response
       ▼
[Step 4: Memory Intelligence] ───────> Model / Rules Judge analyzes turn
       │                               Identifies: Kept facts, Updated summaries, Discarded items
       │                               Calculates: Confidence, Provenance, Token delta
       │                               Generates: "Why Report"
       ▼
[Step 5: Atomic Commit] ─────────────> Insert commit record with parent pointers
                                       Insert/update active memory records
                                       Update branch HEAD reference
```

---

## 8. Planned Version-Control Semantics

ManiGit implements Git-like semantics mapped to agent memory:

- **Commit:** An immutable snapshot of memory mutations containing:
  - `commit_id`: Unique identifier (UUID / hash).
  - `parent_ids`: References to parent commit(s) (supports single-parent and merge commits).
  - `timestamp`: UTC ISO-8601 timestamp.
  - `author`: "agent:auto" or "human:curator".
  - `message`: Commit summary message.
  - `why_report`: Explicit justification of what changed and why.
  - `tokens_before` / `tokens_after`: Exact context size impact.
- **Branch:** Named pointers to commits (e.g., `main`, `experiment-task-a`).
- **Checkout:** Reconstruct memory state at a past commit without losing newer commits.
- **Diff:** Semantic and structured difference between two memory states.
- **Merge:** Combining two memory branches with automated or human-assisted conflict resolution.
- **Tombstone:** Explicit marker indicating a memory unit was superseded, maintaining lineage without polluting active context.

---

## 9. Planned Memory Tiers

ManiGit categorizes all active information into three distinct tiers:

```
+-----------------------------------------------------------------------+
| TIER 1: VERBATIM (High Priority, Uncompressed)                       |
| Constraints, strict instructions, code blocks, IDs, numbers, errors   |
+-----------------------------------------------------------------------+
| TIER 2: SUMMARIES (Medium Priority, Condensed Lineage)                |
| Topical syntheses of multi-turn reasoning, discussions, background    |
+-----------------------------------------------------------------------+
| TIER 3: DISCARDED / TOMBSTONES (Zero Context Weight, Preserved)       |
| Small talk, superseded facts, redundant outputs; kept for audit       |
+-----------------------------------------------------------------------+
```

1. **Tier 1 (Verbatim / Pinned):** Information where loss of precision causes catastrophic agent failure (API contracts, user constraints, exact identifiers, errors, code, paths, config values). Stored verbatim and guaranteed first allocation in token budget.
2. **Tier 2 (Summarized):** Multi-turn discussions and iterative reasoning condensed into concise topic summaries while strictly referencing all raw source message IDs and preserving key figures/decisions.
3. **Tier 3 (Archived / Tombstoned):** Superseded assertions, conversational filler (greetings, acknowledgements, small talk), and duplicates. Excluded from active prompt context to save tokens, but permanently preserved in raw history and recoverable through provenance.

---

## 10. Memory Intelligence Architecture (Phase 2 Implemented)

ManiGit implements a **Hybrid Decision Pipeline**:

```
[Raw Message]
      │
      ▼
[1. Deterministic Rule Engine] ─────> High-confidence factual or filler match?
      │                                   │
      │ (No / Ambiguous)                  │ (Yes - Fast Path)
      ▼                                   ▼
[2. Semantic LLM Judge]             [Immediate Classification]
      │                                   │
      ▼                                   │
[3. Confidence Policy & Synthesis] <──────┘
      │
      ▼
[4. Contradiction & Supersession Check]
      │
      ▼
[5. Structured Why Report Generation]
      │
      ▼
[6. Commit Staging to Core Repository]
```

### Key Principles
- **Fast Path:** Clear deterministic patterns (code, URLs, constraints, errors, IDs, greetings, acknowledgements) bypass the LLM judge, eliminating unnecessary API cost and latency.
- **Conservative Confidence Strategy:**
  - $0.90 - 1.00$: Very High confidence
  - $0.75 - 0.89$: High confidence
  - $0.50 - 0.74$: Uncertain
  - $< 0.50$: Low confidence
  - *Non-Destructive Principle:* Any candidate suggested for Tier 3 archiving with confidence $< 0.75$ is automatically escalated to Tier 1 VERBATIM preservation, preventing silent data loss.
- **Contradiction without Erasure:** When a new fact conflicts with an active fact (e.g. database choice updated from PostgreSQL to MongoDB), the historical fact is superseded and tombstoned from active view, but remains 100% reconstructable in earlier commits and immutable raw history.
- **Explainability via Why Report:** Every memory classification and commit produces an auditable `WhyReport` detailing decision, tier, confidence, matched rules, reason, source messages, and predecessor memory lineage.


---

## 11. Context Compilation & Retrieval Subsystem (Phase 3 Implemented)

### 11.1 Memory vs. Context Distinction
A foundational invariant in ManiGit is the strict boundary between repository state and runtime prompt state:
- **Memory (Persistent Repository State):** The versioned, immutable, append-only SQLite store holding all messages, memories, provenance links, commits, and branch pointers. Never mutated during context assembly.
- **Context (Ephemeral Inference Payload):** A transient, read-only selection of active memories deterministically retrieved, scored, and packed under a specified token budget for a specific request.

### 11.2 Retrieval Architecture
The retrieval subsystem operates strictly locally and deterministically via `MemoryRetriever`:
- **Active State Authoritativeness:** Reuses `reconstruct_memory_state()` from the core repository. Operates exclusively on active memories associated with the targeted commit or branch head.
- **Tier Filtering:** Memories in Tier 1 (`VERBATIM`) and Tier 2 (`SUMMARY`) with `ACTIVE` status are eligible. `ARCHIVED` and `TOMBSTONE` memories are excluded from regular context compilation.
- **Deterministic Lexical Token Matcher:** Evaluates textual relevance using normalized word token sets, exact match counts, and exact multi-word phrase bonuses. No external dependencies, cloud services, or non-deterministic components.
- **Zero Memory Duplication:** Candidates are references to existing repository memory records with attached provenance IDs (`source_message_ids`).

### 11.3 Scoring Strategy & Priorities
Priority scoring enforces a strict hierarchical ordering:
1. **PRIMARY — Query Relevance (Strictly Dominant):**
   - Active memories are partitioned into **Relevant** ($R > 0.0$) and **Unrelated** ($R = 0.0$).
   - Any memory with genuine query relevance receives a base score offset $\ge 1.0000$ (`priority = 1.0 + (relevance * 2.0 * relevance_weight) + secondary_boosts`).
   - Any unrelated memory ($R = 0.0$) is strictly bounded below $0.0500$ (`priority = secondary_boosts * 0.10`).
   - **Mathematical Guarantee:** An unrelated memory (regardless of tier, confidence, or constraint markers) can never outrank a memory possessing genuine query relevance ($1.0001 > 0.0500$).
2. **SECONDARY — Explicit Constraints & Decisions:**
   - Within candidates of identical relevance, memories containing recognized constraints (`must`, `cannot`, `strictly`, etc.) or decisions (`decided`, `selected`, `agreed`, etc.) receive an additive boost ($+0.15$ and $+0.10$ respectively).
3. **TERTIARY — Confidence:**
   - Scaled by `confidence_weight` (up to $+0.08$), ranking higher-confidence items above uncertain ones.
4. **QUATERNARY — Memory Tier:**
   - Preserves tier preferences when relevance and secondary signals are identical: `VERBATIM` ($+0.05$) vs `SUMMARY` ($+0.02$).
5. **FINAL — Deterministic Tie-Breaking:**
   - Ties in composite priority score are broken deterministically downstream by `(token_count ASC, memory_id ASC)`.

### 11.4 Token Budget & Packing
Implemented via `ContextBudget`:
- **Greedy Token-Budget Selection:** Candidates sorted by descending priority score (with deterministic tie-breakers) are evaluated sequentially against remaining token budget. When a candidate exceeds remaining tokens, it is skipped and evaluation continues on subsequent candidates to find smaller items that still fit.
- **Strict Budget Invariant:** The compiler guarantees that `total_tokens <= max_tokens` across all code paths, including exact boundary saturation, candidates larger than total budget, zero budgets, and empty candidate sets.
- **Auditability:** Maintains discrete lists of `included_candidates` and `excluded_candidates` with explicit machine-readable reasons (`outside budget`, `low relevance`, `archived`, `duplicate`, `tier excluded`).

### 11.5 Historical & Branch-Aware Compilation
- **Time Travel:** `compile(query, commit_id=...)` reconstructs active memory from the specified historical commit. Current HEAD memories never leak into historical context compilation.
- **Branch Awareness:** `compile(query, branch=...)` resolves the branch's specific head commit without changing branch pointers.
- **Read-Only Safety:** The compiler performs zero SQL `INSERT`, `UPDATE`, or `DELETE` statements.

### 11.6 Deferred Features & Why Vector DBs Are Deferred
ManiGit deliberately defers vector databases, dense embeddings, and external retrieval pipelines:
- **Exact Identifier & Constraint Preservation:** Dense embeddings frequently suffer from nearest-neighbor hallucination when distinguishing exact version numbers, constraint negations, and UUIDs.
- **Deterministic & Auditable Reproducibility:** Exact lexical scoring guarantees bitwise identical context generation across runs.
- **Zero External Infrastructure:** Keeps ManiGit lightweight, portable, and free of cloud dependencies (Supabase, Pinecone, Milvus).
- **Future Integration:** Vector embeddings may be introduced in a future phase as an auxiliary scoring signal, but the core deterministic foundation remains authoritative.

---

## 12. Agent Runtime Subsystem (Phase 4 Implemented)

### 12.1 Responsibility & Orchestration Lifecycle
The Agent Runtime (`src/manigit/agent/`) orchestrates the complete interaction lifecycle, connecting the persistent repository, the Phase 3 context compiler, provider-agnostic model adapters, and Phase 2 memory intelligence:

```
[User Message]
       │
       ▼
[1. Input Validation & Session Resolution]
       │
       ▼
[2. Store Raw User Message] ───────────> Appended to immutable SQLite messages table
       │
       ▼
[3. Compile Context via ContextCompiler] ──> Read-only active memory snapshot compiled
       │                                     under strict token budget B
       ▼
[4. Construct Structured Model Prompt] ────> [System Instructions] + [Active Memory Context] + [User Message]
       │
       ▼
[5. ModelAdapter Inference] ───────────> Calls provider-agnostic LLM (Mock or Gemini)
       │
       ▼
[6. Store Raw Assistant Response] ──────> Appended to immutable SQLite messages table
       │
       ▼
[7. Memory Intelligence Evaluation] ────> MemoryService evaluates exchange (rules, judge, classifier)
       │                                  Detects contradictions/supersessions without erasing history
       ▼
[8. Atomic Versioned Commit] ──────────> Meaningful state change staged as new DAG commit
       │                                  Branch HEAD advanced; Why Report recorded
       ▼
[9. Auditable AgentResponse] ──────────> Returns content, token usage, context result & why report
```

### 12.2 Key Invariants & Distinctions
1. **Raw Conversation vs. Versioned Memory:**
   - Raw conversation messages (user prompts and assistant responses) are permanently archived in the append-only `messages` table. Nothing is ever overwritten or deleted.
   - Versioned memory is a derived, curated state. Memory modifications produce explicit DAG commits.
2. **Context Compilation is Strictly Read-Only:**
   - Assembling context executes zero `INSERT`, `UPDATE`, or `DELETE` statements.
   - Branch HEADs and branch pointers are never switched silently.
3. **Contradictions with Historical Recoverability:**
   - When a fact updates (e.g., PostgreSQL $\to$ MongoDB), the active state reflects MongoDB, while the historical state remains 100% reconstructable at earlier commits.
4. **Mathematical Context Formalization:**
   - Implements bounded context selection under hard constraint $\sum L(m_i) \le B$.
   - Uses deterministic lexical relevance $S_{\text{lexical}}$ and Greedy Token-Budget Selection. Detailed in `docs/research/mathematical_foundation.md`.

---

## 13. Planned Evaluation Strategy

ManiGit will be evaluated empirically against common memory strategies:
- **Comparative Baselines:**
  1. *Full History Concatenation:* Uncompressed raw history until token limit exhaustion.
  2. *Sliding Window:* Fixed-length window of the N most recent turns.
  3. *Blanket Summarization:* Monolithic summary rewritten on every turn.
- **Core Evaluation Dimensions:**
  - **Token Efficiency:** Tokens consumed per request and token cost trajectory over multi-turn sessions.
  - **Information Retention (Needle-in-a-Haystack & Constraint Recall):** Accuracy in recalling critical facts stated 50+ turns earlier.
  - **Contradiction Resolution:** Accuracy when a user explicitly alters or reverses a previous constraint.
  - **Latency:** Overhead of memory compilation and commit operations.
  - **Auditability & Reversibility:** Verification of zero data loss from raw logs and deterministic rollback accuracy.

