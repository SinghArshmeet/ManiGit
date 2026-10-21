# ManiGit

**Transparent, Versioned Context Memory for Long-Running AI Agents**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

---

## Overview

**ManiGit** is a version-controlled memory architecture for AI agents. It applies Git-inspired semantics—commits, branches, diffs, checkouts, and auditable lineage—to agent memory management.

In traditional agent systems, conversational context is treated as a transient text buffer that is either naively truncated or opaquely summarized. This causes severe context degradation, loss of critical constraints, hallucination compounding, and inability to inspect or revert agent state.

ManiGit treats agent memory as a managed, versioned repository with full provenance and budget-aware context compilation.

---

## Core Principles

1. **Raw Conversation History is Permanent:** Raw interactions are stored in an immutable, append-only archive. Nothing is ever silently deleted.
2. **Memory is Managed State:** Active memory is structured into discrete units (constraints, summaries, facts) with clear lineage back to raw messages.
3. **Every Mutation is a Commit:** Every change to active memory generates an atomic commit with an author, timestamp, parent links, token deltas, and an explanatory "Why Report".
4. **Inspectable & Reversible:** Memory can be scrolled, compared via diffs, branched to explore alternative conversation paths, and rolled back without agent restarts.
5. **Budget-Aware Context Assembly:** Prompts are dynamically compiled from memory under strict token budgets using tiered prioritization.
6. **Human-in-the-Loop Curation:** Users can pin, trim, or hand-edit memories; human edits become first-class commits in the repository history.

---

## Key Architectural Distinctions

### Memory ≠ Context
- **Memory** is the persistent, structured repository containing all knowledge the agent has acquired across sessions.
- **Context** is the ephemeral, budgeted subset compiled for a specific model prompt under token constraints.

### Raw History ≠ Active Memory
- **Raw History** is an immutable append-only log of every interaction. It remains fully recoverable even when information is summarized or pruned.
- **Active Memory** is the versioned working state curated for relevance, accuracy, and token efficiency. Discarded items receive explicit tombstone markers rather than silent erasure.

---

## Three-Tier Memory Structure

| Tier | Name | Target Content | Treatment |
| :---: | :--- | :--- | :--- |
| **Tier 1** | **Verbatim** | Constraints, decisions, exact numbers, IDs, code, error messages | Stored verbatim; uncompressed; prioritized first in token budget |
| **Tier 2** | **Summarized** | Multi-turn reasoning, iterative discussion, background context | Synthesized into concise topic summaries with lineage to source message IDs |
| **Tier 3** | **Discarded / Tombstone** | Chit-chat, duplicates, superseded assertions, temporary noise | Excluded from context prompt; retained in storage with explanatory tombstone |

---

## Project Structure

```
ManiGit/
│
├── README.md                   # Project overview, concepts, and getting started
├── .gitignore                  # Git ignore rules for Python, OS, DBs, and data
├── .env.example                # Sample environment configuration
├── requirements.txt            # Dependency manifest
├── pyproject.toml              # Build system, package discovery, and metadata
│
├── docs/
│   ├── architecture/           # System architecture and conceptual overviews
│   │   └── overview.md
│   ├── design/                 # Technical design, component boundaries, and schemas
│   │   └── system_design.md
│   └── research/               # Evaluation methodology, baselines, and test designs
│       └── evaluation_strategy.md
│
├── data/                       # Structured data organization
│   ├── raw/                    # Original raw conversation logs & datasets
│   ├── processed/              # Transformed & benchmark-ready datasets
│   ├── database/               # Runtime SQLite databases (*.db ignored)
│   └── backups/                # Database snapshots and state backups
│
├── src/
│   └── manigit/
│       ├── core/               # Persistent storage, commit DAG, branches, reconstruction
│       ├── memory/             # 3-tier classification, confidence, provenance, why report
│       ├── context/            # Memory retrieval, ranking, and budget context compilation
│       ├── models/             # Provider-agnostic model adapter (generate, summarize, etc.)
│       ├── agent/              # Agent execution runtime loop
│       ├── evaluation/         # Benchmarks, baseline comparisons, and metric tracking
│       ├── cli/                # Developer & user CLI interface
│       └── config/             # Application configuration and environment settings
│
├── tests/
│   ├── unit/                   # Unit test suite
│   ├── integration/            # Multi-component integration tests
│   ├── memory/                 # Tests for memory intelligence and classification
│   ├── context/                # Tests for context compilation and token packing
│   └── evaluation/             # Tests for evaluation harnesses
│
├── scripts/                    # Development, migration, and operational scripts
│
└── web/
    ├── frontend/               # Visual commit graph, memory inspector UI
    └── backend/                # API service mediating between web UI and core library
```

---

## Planned Architecture Flow

```
[User Message]
       │
       ▼
1. Raw Message Log ──────────> Stored in immutable append-only SQLite archive
       │
       ▼
2. Context Compilation ──────> Active memory retrieved from current branch HEAD
       │                       Budget-packed: Pinned -> Summaries -> Verbatim Window
       ▼
3. Model Inference ──────────> Model Adapter calls provider-agnostic LLM
       │
       ▼
4. Memory Intelligence ──────> Analyzes exchange, updates tiers, generates "Why Report"
       │
       ▼
5. Commit Creation ──────────> Atomic commit added to DAG; HEAD reference updated
```

---

## Quickstart (Development Setup)

### Prerequisites
- Python 3.10 or higher
- Git

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/your-org/ManiGit.git
cd ManiGit

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -e ".[dev]"
```

### 3. Verify Installation
```bash
pytest
```

---

## Phase Roadmap

- [x] **Phase 0: Foundation & Architecture** (Structure, component boundaries, documentation, package configuration)
- [x] **Phase 1: Core Storage & Version Control Engine** (SQLite schema, commits, branches, DAG traversal, deterministic reconstruction, immutability triggers, provenance)
- [x] **Phase 2: Model Adapter & Memory Intelligence** (Provider-agnostic interface, 3-tier classification rules, hybrid judge, conservative confidence, contradiction detection, Why Reports)
- [x] **Phase 3: Context Compiler & Token Budget Packing** (Deterministic retrieval, textual relevance scoring, tier prioritization, greedy token-budget selection, branch/historical context, auditable ContextResult)
- [x] **Phase 4: Agent Runtime Loop & Model Adapter Integration** (Multi-turn turn orchestration, immutable raw history, ContextCompiler integration, ModelAdapter abstraction, auditable AgentResponse/AgentTurn, mathematical context formalization)
- [ ] **Phase 5: Evaluation & Benchmarks** (Baselines, NIAH benchmarks, token efficiency tracking)
- [ ] **Phase 6: Web UI Dashboard & CLI** (Interactive commit DAG visualization, tier-colored memory inspection)


---

## License

This project is licensed under the MIT License - see the LICENSE file for details.
