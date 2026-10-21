# Unified Taxonomy of LLM Agent Memory Architectures

**Project:** ManiGit — Transparent, Versioned Context Memory for Long-Running AI Agents  
**Document:** Research Taxonomy  
**Date:** October 2026  

---

## 1. Overview

Research into agent memory has produced diverse architectural approaches spanning operating-system metaphors, cognitive theories, vector databases, and knowledge graphs. To rigorously position ManiGit within this landscape, we categorize existing systems across eight structural dimensions:

1. **Storage Substrate**
2. **Memory Representation**
3. **Core Memory Operations**
4. **Control & Decision Flow**
5. **Temporal & Mutation Model**
6. **Provenance & Auditability**
7. **Historical State Behavior**
8. **Context Selection & Compilation**

---

## 2. Dimension 1: Storage Substrate

Where does memory physically reside during and across agent sessions?

* **Context Window (In-Prompt Buffer):** Memory resides solely within the model's active attention context (e.g., standard few-shot prompts, sliding conversation buffers, in-context scratchpads).
  * *Characteristics:* Ephemeral, reset upon inference termination, strictly bounded by model context length $L$.
  * *Examples:* Basic ChatGPT, ReAct scratchpads.
* **Model Parameters (Parametric Memory):** Memory is baked directly into the neural network weights via pre-training, fine-tuning, or parameter-efficient adapters (LoRA).
  * *Characteristics:* Static between training rounds, high compute cost to update, black-box opacity.
  * *Examples:* Standard foundation models (GPT-4, Claude).
* **Flat External Database (Key-Value / Document Store):** Memory is externalized into relational or document databases (e.g., SQLite, PostgreSQL, MongoDB, JSON files).
  * *Characteristics:* Persistent, queryable via SQL or text search, human-readable.
  * *Examples:* Early agent backends, MemGPT archival storage.
* **Vector Store (Dense Embedding Index):** Text chunks or memory assertions are embedded into dense vector spaces and indexed via approximate nearest neighbors (ANN) libraries (e.g., FAISS, Qdrant, Pinecone, Chroma).
  * *Characteristics:* Excellent semantic matching for unstructured text, but lacks relational constraints, temporal ordering, and exact keyword guarantees.
  * *Examples:* Standard RAG, Generative Agents memory stream, early Mem0.
* **Structured / Knowledge Graph:** Memories are represented as entity-relationship-entity triples $(h, r, t)$ or property graphs.
  * *Characteristics:* Supports multi-hop associative traversal, entity linking, and hierarchical community detection.
  * *Examples:* HippoRAG, Graph RAG, Mem0 graph layer.
* **Immutable Commit DAG (Version-Controlled Repository):** Memories are stored in an append-only directed acyclic graph (DAG) where each state change is captured as a parent-linked, cryptographically identified commit object.
  * *Characteristics:* Complete non-destructive history, branching support, instant point-in-time state reconstruction, tamper-evident audit logs.
  * *Examples:* **ManiGit**, Git Context Controller (file-system level), GitOfThoughts.

---

## 3. Dimension 2: Memory Representation

In what format is knowledge stored within the memory substrate?

* **Raw Conversational Tokens:** Unmodified dialogue turns between the user and assistant.
  * *Pros:* Preserves 100% of original fidelity, tone, and verbatim constraints.
  * *Cons:* Highly redundant, token-expensive, prone to context explosion.
* **Running Summaries:** Periodically condensed prose synthesizing past interactions into a continuous preamble.
  * *Pros:* Token-compact.
  * *Cons:* Subject to semantic drift, hallucinated consolidation, and irreversible erasure of subtle numerical or technical constraints.
* **Atomic Semantic Facts / Claims:** Discrete natural language assertions (e.g., `"User prefers PostgreSQL for production"`).
  * *Pros:* Modular, individually indexable, cleanly updatable.
  * *Cons:* Strips conversational tone, requires an active extraction pipeline.
* **Dense Embedding Vectors:** Real-valued vectors capturing semantic proximity in latent space.
  * *Pros:* Fast mathematical similarity search.
  * *Cons:* Completely uninterpretable to human auditors; struggles with exact negation or numerical bounds.
* **Episodic Execution Trajectories:** Step-by-step logs of environment states, agent actions, tool outputs, and execution results.
  * *Pros:* Ideal for reinforcement learning, task replay, and procedural skill acquisition.
  * *Cons:* High token volume; task-specific structure.
* **Networked Concept Notes (Zettelkasten):** Markdown notes enriched with dynamic tags, bidirectional hyperlinks, and evolving synthesis.
  * *Pros:* Facilitates open-ended conceptual ideation and associative discovery.
  * *Cons:* Difficult to bound under strict token budgets.
* **Tiered Typed Memory Objects (ManiGit):** Memories explicitly tagged into functional lifecycle tiers:
  * `VERBATIM`: High-fidelity exact constraints and decisions.
  * `SUMMARY`: High-level aggregated semantic overviews.
  * `ARCHIVED`: Stale, superseded, or low-confidence candidate facts.
  * `TOMBSTONE`: Explicitly retracted or refuted assertions.

---

## 4. Dimension 3: Core Memory Operations

What fundamental operations can the agent or memory manager perform on the store?

| Operation | Description | Representative Systems |
| :--- | :--- | :--- |
| **Write (Ingest)** | Inserting new percepts or statements into memory. | All persistent systems. |
| **Retrieve (Read)** | Querying the memory store based on similarity, recency, or relevance. | RAG, MemGPT, HippoRAG. |
| **Summarize (Compress)** | Compressing multiple past memories into a concise representation. | Running Summary, Generative Agents. |
| **Update (Mutate)** | Modifying an existing memory node to reflect changes. | Mem0, MemGPT (`core_memory_replace`). |
| **Reflect (Synthesize)** | Generating higher-level insights or meta-rules from raw events. | Generative Agents, Reflexion. |
| **Consolidate (Decay)** | Fading, merging, or pruning memories based on cognitive curves. | MemoryBank (Ebbinghaus). |
| **Supersede (ManiGit)** | Marking an older fact as superseded by a newer fact while preserving the older fact's historical record and logging an auditable Why Report. | **ManiGit**. |
| **Checkout (Time-Travel)** | Reconstructing the complete active memory state as it existed at a past commit or timestamp. | **ManiGit**, Git Context Controller. |

---

## 5. Dimension 4: Control & Decision Flow

Who or what governs the memory lifecycle (classification, storage, retrieval, and eviction)?

* **Rule-Based Deterministic Control:** Fixed procedural algorithms, regular expressions, and heuristics dictate memory intake and context selection.
  * *Characteristics:* Highly predictable, zero token cost for control, but brittle on ambiguous natural language.
* **Pure LLM Agent Control (Tool-Driven):** The language model actively decides when to read, write, edit, or delete memory using function/tool calls.
  * *Characteristics:* Highly flexible, but suffers from agent forgetfulness, high tool-invocation latency, and vulnerability to prompt injection.
  * *Examples:* MemGPT, Git Context Controller.
* **Retrieval-Driven Control:** Stateless ranking algorithms (BM25 or vector cosine similarity) select context based purely on mathematical distance to the current query.
  * *Characteristics:* Fast, decoupled from model execution, but oblivious to factual contradictions or user constraints.
  * *Examples:* Standard RAG.
* **Hybrid Rule-First + LLM-Judge (ManiGit):** Deterministic pattern rules handle unambiguous high-priority patterns (constraints, credentials, commands) with zero latency; ambiguous candidate statements fall through to an LLM judge calibrated with explicit confidence thresholds.
  * *Characteristics:* Combines rule-based reliability and speed with natural-language understanding; outputs auditable confidence metrics.
  * *Examples:* **ManiGit**.

---

## 6. Dimension 5: Temporal & Mutation Model

How does the memory store treat the passage of time and state updates?

* **Static (Immutable Corpus):** Memories are ingested once and never change.
  * *Examples:* Wikipedia RAG, static documentation search.
* **Append-Only Flat Log:** New information is continually appended to the end of a log or database without modifying prior entries.
  * *Examples:* Raw chat logs, Generative Agents memory stream.
  * *Failure Mode:* Unbounded bloat; conflicting entries accumulate and cause "ghost context."
* **Destructive Mutable CRUD:** Incoming information executes SQL `UPDATE` or `DELETE` statements or in-place text replacements, permanently overwriting older values.
  * *Examples:* MemGPT core memory, Mem0, standard relational databases.
  * *Failure Mode:* Irreversible information loss; impossible to audit past agent behavior or verify why a decision was made.
* **Evolving Network:** Nodes and edges are continuously merged, rewired, or decayed over time.
  * *Examples:* A-MEM, MemoryBank.
  * *Failure Mode:* Historical truth is blurred into contemporary state.
* **Versioned Commit DAG (ManiGit):** All modifications are packaged into discrete, immutable commits. Updates do not overwrite; they create a new commit node referencing its parent, preserving the entire lineage graph indefinitely.
  * *Examples:* **ManiGit**, GitOfThoughts.

---

## 7. Dimension 6: Provenance & Auditability

Can an external observer verify the lineage and decision rationale behind every stored memory?

* **None (Black-Box):** The agent produces context or answers without explicit attribution.
* **Partial Document Linkage:** Retrieved chunks reference source file names or document IDs (standard in RAG).
* **Source-Linked Message Provenance:** Each memory fact contains a direct foreign-key pointer back to the exact user message, turn index, session ID, and timestamp that originated it.
* **Auditable Decision Trace (Why Reports - ManiGit):** In addition to source-message linkage, the system generates and stores an auditable rationale explaining *why* the fact was accepted, *which rule or judge* classified it, *what confidence score* was assigned, and *which prior fact* it superseded.

---

## 8. Dimension 7: Historical State Behavior

How does the memory system respond when queried about past states or historical facts?

* **Current Only:** The system only knows its present active state; historical queries about previous configurations fail or return hallucinated projections.
* **Implicit Historical Recurrence:** Old facts remain in the database and may accidentally surface if their semantic similarity matches the query, often clashing with current facts.
* **Manual Log Inspection:** Humans can inspect raw execution logs, but the agent itself cannot operate from a previous historical context.
* **Point-in-Time Reconstruction (Time-Travel - ManiGit):** The system can mathematically reconstruct the exact active memory set as of any historical commit $C_k$, enabling the agent to reason accurately within past states without polluting the main production branch.

---

## 9. Dimension 8: Context Selection & Compilation

How does the system select which memories to place into the prompt context window for an incoming query $q$?

* **Recent Sliding Window:** Selects the most recent $k$ tokens or turns.
  * *Pros:* Simple, ensures immediate conversational flow.
  * *Cons:* Bounded horizon; drops early foundational facts.
* **Top-$k$ Similarity Retrieval:** Selects the top $k$ items by embedding similarity or BM25 score.
  * *Pros:* Query-focused.
  * *Cons:* Ignores item length; can overflow token limits or starve the prompt of other necessary context; vulnerable to retrieving mutually contradictory chunks.
* **Heuristic Truncation:** Fills prompt until reaching a safety threshold, truncating whatever falls outside.
* **Deterministic Knapsack Compilation (ManiGit):** Formalizes context selection as a bounded knapsack optimization problem:
  $$\max_{C_t \subseteq M_t} \sum_{m_i \in C_t} U(m_i, q_t) \quad \text{subject to} \quad \sum_{m_i \in C_t} L(m_i) \le B$$
  Solves the problem using a greedy score-density approximation that prioritizes high-utility, tier-weighted memories under a strict token budget $B$.
