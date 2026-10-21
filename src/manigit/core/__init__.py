"""
Core Memory Repository Subsystem.

Architectural Responsibility:
----------------------------
The core repository manages the low-level version-controlled storage primitives:
- Persistent SQLite storage management
- Raw messages archive (immutable, append-only)
- Memory records and state snapshots
- Commits (parents, author, timestamp, commit message, why report, token deltas)
- Branches and HEAD reference tracking
- Commit history navigation and DAG traversal
- Deterministic reconstruction of previous memory states at any commit

Key Principle:
--------------
Raw conversation history is permanently preserved in an append-only archive.
Working memory state is derived and versioned through commits.
"""

from manigit.core.database import Database
from manigit.core.exceptions import (
    BranchAlreadyExistsError,
    BranchNotFoundError,
    CommitNotFoundError,
    DatabaseError,
    ImmutableRecordError,
    InvalidCommitError,
    ManiGitError,
    MemoryNotFoundError,
    MessageNotFoundError,
    RepositoryError,
)
from manigit.core.models import (
    Branch,
    Commit,
    Memory,
    MemoryStatus,
    MemoryTier,
    Message,
    MessageRole,
)
from manigit.core.repository import ManiGitRepository
from manigit.core.tokens import estimate_tokens

__all__ = [
    "Database",
    "ManiGitRepository",
    "Message",
    "Memory",
    "Commit",
    "Branch",
    "MessageRole",
    "MemoryTier",
    "MemoryStatus",
    "estimate_tokens",
    "ManiGitError",
    "RepositoryError",
    "DatabaseError",
    "MessageNotFoundError",
    "MemoryNotFoundError",
    "CommitNotFoundError",
    "BranchNotFoundError",
    "BranchAlreadyExistsError",
    "ImmutableRecordError",
    "InvalidCommitError",
]
