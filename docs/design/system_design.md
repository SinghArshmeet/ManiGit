# ManiGit: System Design & Implemented Storage Architecture

This document defines the technical boundaries, storage design, interface contracts, and the implemented SQLite repository schema for Phase 1.

---

## 1. Architectural Responsibilities & Subsystem Boundaries

To prevent coupling and maintain testability, each subsystem has strictly demarcated responsibilities:

### 1.1 Core / Memory Repository (`manigit.core`) — [IMPLEMENTED: Phase 1]
- **Responsibilities:**
  - Manages SQLite database connection and transaction lifecycles with WAL mode and strict foreign key enforcement.
  - Implements relational tables for messages, memory units, provenance links, commits, commit trees, and branches.
  - Maintains the commit DAG using relational parent references (`parent_commit_id`).
  - Implements deterministic state reconstruction (reconstructing active memory snapshots for any given `commit_id`).
  - Enforces database-level immutability triggers preventing `UPDATE` or `DELETE` on historical records.
- **Explicit Exclusions:**
  - Does NOT perform LLM calls.
  - Does NOT make judgment decisions about what to keep or summarize.

### 1.2 Memory Intelligence (`manigit.memory`) — [IMPLEMENTED: Phase 2]
- **Responsibilities:**
  - Analyzes new interaction exchanges against current active memory state.
  - Applies hybrid decision pipeline (RuleEngine + MemoryJudge).
  - Classifies items into 3 tiers:
    - **Tier 1 (VERBATIM):** Constraints, numbers, code, IDs, paths, configs, errors, explicit decisions.
    - **Tier 2 (SUMMARY):** Multi-turn discussions and reasoning synthesized with strict provenance retention.
    - **Tier 3 (ARCHIVED):** Conversational filler (greetings, acknowledgements, small talk, duplicates) preserved in raw history.
  - Enforces conservative confidence policy: low-confidence archive candidates (<0.75) are escalated to VERBATIM to prevent silent data loss.
  - Detects contradictions and explicit supersessions (e.g. database choice updated from PostgreSQL to MongoDB) without erasing historical records.
  - Produces structured **Why Reports** explaining state change justifications, rules matched, and lineage.

### 1.3 Context Compiler (`manigit.context`) — [IMPLEMENTED: Phase 3]
- **Responsibilities:**
  - Receives current active memory snapshot, user query, and token budget.
  - Reconstructs active memory state from repository using `reconstruct_memory_state()` at HEAD, a branch pointer, or a historical commit ID.
  - Filters out `ARCHIVED` and `TOMBSTONE` items, presenting only eligible `VERBATIM` and `SUMMARY` candidates.
  - Scores candidates deterministically via `MemoryScorer`:
    - Textual relevance (exact token overlap + phrase matching).
    - Prioritizes direct relevance over blind tier ranking (unrelated VERBATIM memories are discounted so relevant summaries outrank them).
    - Tier weights, confidence weighting, and constraint/decision boosting.
    - Deterministic tie-breaking by token count and memory ID.
  - Manages token budget via `ContextBudget` with Greedy Token-Budget Selection under strict `<= max_tokens` guarantee.
  - Produces inspectable and auditable `ContextResult` containing selected memories (with selection reasons), excluded memories (with exclusion reasons), token accounting, and provenance links.
  - Provides `to_prompt_context()` formatter for direct injection into agent prompt templates.
- **Explicit Invariants & Exclusions:**
  - Strictly **READ-ONLY**: Never executes `INSERT`, `UPDATE`, or `DELETE`.
  - Never mutates branches, commits, memories, or messages.
  - Does NOT introduce embeddings, vector databases, or cloud infrastructure.

### 1.4 Model Adapter (`manigit.models`) — [IMPLEMENTED: Phase 2]
- **Responsibilities:**
  - Provides a uniform, swappable interface across model providers (`ModelAdapter` base class).
  - Exposes essential primitives: `generate()`, `summarize()`, `judge_memory()`, `count_tokens()`.
  - Provides `MockModelAdapter` for fully offline, deterministic testing without API keys.


### 1.5 Agent Runtime (`manigit.agent`) — [IMPLEMENTED: Phase 4]
- **Responsibilities:**
  - Coordinates the execution loop: Ingest message → Retrieve active memory → Compile context → Model inference → Classify turn → Atomic commit.
  - Exposes `AgentRuntime` coordinating `ManiGitRepository`, `ContextCompiler`, `ModelAdapter`, and `MemoryService`.
  - Produces auditable `AgentResponse` and `AgentTurn` models containing turn metadata, context selection results, token statistics, and Why Reports.
  - Distinguishes immutable raw conversation history from curated active memory states.
  - Enforces failure safety: if model generation fails, raw user prompts are preserved without false assistant messages or invalid commits.
  - Formalizes context selection mathematically via greedy token-budget selection under hard budget invariant $\sum L(m_i) \le B$.

### 1.6 Evaluation (`manigit.evaluation`) — [Planned: Phase 5]
- **Responsibilities:**
  - Reproducible multi-turn benchmark suites against full-history, sliding-window, and blanket-summarization baselines.

### 1.7 Web & Presentation (`web/`, `manigit.cli`) — [Planned: Phase 4/6]
- **Responsibilities:**
  - Visual commit DAG explorer, branch views, tier-colored context inspection, and human curation (pin, trim, edit).

---

## 2. Phase 1 SQLite Relational Schema (Implemented)

The database resides at `data/database/manigit.db`. All tables use explicit primary keys, strict foreign keys, indexing, and immutability triggers.

```
+-------------------------------------------------------------+
|                        schema_version                       |
+-------------------------------------------------------------+
| PK  version (INTEGER)                                       |
|     applied_at (TEXT ISO-8601)                              |
+-------------------------------------------------------------+

+-------------------------------------------------------------+
|                           messages                          |
+-------------------------------------------------------------+
| PK  id (TEXT)                                               |
|     session_id (TEXT)                                       |
|     role (TEXT: user | assistant | system | tool)           |
|     content (TEXT)                                          |
|     sequence_num (INTEGER)                                  |
|     token_count (INTEGER)                                   |
|     timestamp (TEXT ISO-8601)                               |
|     metadata (TEXT JSON)                                    |
| UQ  (session_id, sequence_num)                              |
+-------------------------------------------------------------+
  ▲                          ▲
  │                          │
  │ (FK)                     │ (FK parent)
+──────────────────────+   +──────────────────────────────────+
|    memory_sources    |   |             commits              |
+──────────────────────+   +──────────────────────────────────+
| PK,FK memory_id      |   | PK  id (TEXT)                    |
| PK,FK message_id     |   | FK  parent_commit_id (TEXT, NULL)|
+──────────────────────+   |     branch (TEXT)                |
  │                        |     message (TEXT)               |
  │ (FK)                   |     reason (TEXT)                |
+──────────────────────+   |     author (TEXT)                |
|       memories       |   |     token_count_before (INTEGER) |
+──────────────────────+   |     token_count_after (INTEGER)  |
| PK  id (TEXT)        |   |     tokens_saved (INTEGER)       |
|     content (TEXT)   |   |     timestamp (TEXT ISO-8601)    |
|     tier (TEXT)      |   |     metadata (TEXT JSON)         |
|     status (TEXT)    |   +──────────────────────────────────+
|     confidence (REAL)|     ▲                       ▲
|     token_count (INT)|     │                       │ (FK head)
|     created_at (TEXT)|     │ (FK)                +──────────────────+
|     updated_at (TEXT)|   +─────────────────────+ |     branches     |
|     metadata (JSON)  |   |   commit_memories   | +──────────────────+
+──────────────────────+   +─────────────────────+ | PK  name (TEXT)  |
  ▲                        | PK,FK commit_id     | | FK  head_commit  |
  └────────────────────────┤ PK,FK memory_id     | |     created_at   |
                           |       tier (TEXT)   | |     updated_at   |
                           |       status (TEXT) | +──────────────────+
                           +─────────────────────+
```

### 2.1 Table Specifications & Indexes

1. **`messages`**: Append-only log of raw conversation events.
   - Unique constraint: `UNIQUE (session_id, sequence_num)`.
   - Indexes: `idx_messages_session_seq`, `idx_messages_timestamp`.
2. **`memories`**: Discrete units of knowledge derived from conversation events.
   - Indexes: `idx_memories_status`, `idx_memories_tier`.
3. **`memory_sources`**: Many-to-many join table recording provenance.
   - Composite PK: `(memory_id, message_id)`.
   - Index: `idx_memory_sources_message`.
4. **`commits`**: Versioned, immutable change records forming the DAG.
   - Self-referencing FK: `parent_commit_id REFERENCES commits(id) ON DELETE RESTRICT`.
   - Indexes: `idx_commits_parent`, `idx_commits_branch`.
5. **`commit_memories`**: Normalized representation of the active commit tree (Git-tree equivalent).
   - Composite PK: `(commit_id, memory_id)`.
   - Index: `idx_commit_memories_mem`.
6. **`branches`**: Named mutable pointers to commit IDs.
   - Primary key: `name TEXT`.
   - FK: `head_commit_id REFERENCES commits(id) ON DELETE RESTRICT`.

---

## 3. Immutability Strategy

ManiGit implements defense-in-depth immutability at both the application repository layer and the SQLite database layer:

1. **Database-Level Immutability Triggers:**
   - `trg_messages_prevent_update` & `trg_messages_prevent_delete`: Block any attempt to rewrite or delete raw conversation history.
   - `trg_commits_prevent_update` & `trg_commits_prevent_delete`: Block modifying or deleting historical commits.
   - `trg_commit_memories_prevent_update` & `trg_commit_memories_prevent_delete`: Block modifying historical memory state associations.
   - `trg_memory_sources_prevent_update` & `trg_memory_sources_prevent_delete`: Block tampering with provenance links.
2. **Repository API Guarantee:**
   - No update or delete operations are exposed on commits, messages, or commit trees.
   - State modifications always append a new record and produce a new commit.

---

## 4. Deterministic Memory-State Reconstruction

Given any historical `commit_id`, the active memory state is reconstructed deterministically in a single indexed query:

```sql
SELECT m.id, m.content, cm.tier, cm.status, m.confidence, m.token_count, m.created_at, m.updated_at, m.metadata
FROM commit_memories cm
JOIN memories m ON cm.memory_id = m.id
WHERE cm.commit_id = :commit_id AND cm.status = 'ACTIVE'
ORDER BY m.created_at ASC;
```

Provenance links for each memory are loaded in bulk from `memory_sources`. This provides $O(1)$ snapshot access without needing to re-execute event sourcing logs across thousands of parent steps.

---

## 5. Architectural Decisions & Refinements from Phase 0

1. **Explicit Root Commit:**
   - *Decision:* When initializing a new repository, an explicit root commit (`c_root_...`) is created.
   - *Rationale:* In standard Git, an empty repository has an unborn branch HEAD (`ref: refs/heads/main`), creating edge cases where `log` fails and branches cannot be created until the first commit. With an explicit root commit, the repository always has a valid HEAD, new branches can be created immediately, and `reconstruct_memory_state(root_commit_id)` returns an empty state `[]` cleanly.
2. **Normalized Commit Tree (`commit_memories`):**
   - *Decision:* Rather than replaying deltas from commit 1 to $N$, each commit records its tree snapshot in `commit_memories`.
   - *Rationale:* Guarantees instantaneous, bulletproof state reconstruction at any point in the DAG while preserving historical immutability.
3. **Many-to-Many Provenance (`memory_sources`):**
   - *Decision:* Provenance is stored in a dedicated join table rather than a single `message_id` column on `memories`.
   - *Rationale:* Allows synthesis memories (Tier 2 summaries) to be linked back to multiple source message IDs (e.g., M12 derived from Messages 17, 19, and 24).
