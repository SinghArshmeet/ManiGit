"""
ManiGit Core Repository implementation.

Centralizes data access, versioning, memory storage, commit management,
provenance tracking, and deterministic state reconstruction.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Union
import uuid

from manigit.core.database import Database
from manigit.core.exceptions import (
    BranchAlreadyExistsError,
    BranchNotFoundError,
    CommitNotFoundError,
    DatabaseError,
    ImmutableRecordError,
    InvalidCommitError,
    MemoryNotFoundError,
    MessageNotFoundError,
)
from manigit.core.models import (
    Branch,
    Commit,
    Memory,
    MemoryStatus,
    MemoryTier,
    Message,
    MessageRole,
    utc_now_iso,
)
from manigit.core.tokens import estimate_tokens


class ManiGitRepository:
    """
    Main repository interface for ManiGit.
    
    Provides high-level methods for:
    - Appending raw messages (immutable)
    - Storing memory records with provenance
    - Committing active memory states to the commit DAG
    - Branching and moving HEAD pointers
    - Reconstructing historical memory states
    """

    DEFAULT_BRANCH = "main"

    def __init__(self, db_path: Union[str, Path] = "data/database/manigit.db"):
        self.db = Database(db_path)
        self.active_branch: str = self.DEFAULT_BRANCH

    def initialize_repository(self) -> Branch:
        """
        Initialize the database schema, default branch, and initial root commit.
        
        Returns the default 'main' Branch.
        """
        self.db.initialize_schema()
        conn = self.db.connect()
        cursor = conn.cursor()

        # Check if default branch already exists
        cursor.execute("SELECT name, head_commit_id, created_at, updated_at FROM branches WHERE name = ?;", (self.DEFAULT_BRANCH,))
        row = cursor.fetchone()

        if row:
            self.active_branch = self.DEFAULT_BRANCH
            return Branch(
                name=row["name"],
                head_commit_id=row["head_commit_id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

        # Create initial root commit
        now_iso = utc_now_iso()
        root_commit_id = f"c_root_{uuid.uuid4().hex[:12]}"
        
        with self.db.transaction() as tx:
            tx.execute(
                """
                INSERT INTO commits (
                    id, parent_commit_id, branch, message, reason, author,
                    token_count_before, token_count_after, tokens_saved,
                    timestamp, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    root_commit_id,
                    None,
                    self.DEFAULT_BRANCH,
                    "Initialize ManiGit repository",
                    "Root commit establishing clean repository baseline",
                    "system",
                    0,
                    0,
                    0,
                    now_iso,
                    json.dumps({"type": "root_commit"}),
                ),
            )

            tx.execute(
                """
                INSERT INTO branches (name, head_commit_id, created_at, updated_at)
                VALUES (?, ?, ?, ?);
                """,
                (self.DEFAULT_BRANCH, root_commit_id, now_iso, now_iso),
            )

        self.active_branch = self.DEFAULT_BRANCH
        return Branch(
            name=self.DEFAULT_BRANCH,
            head_commit_id=root_commit_id,
            created_at=now_iso,
            updated_at=now_iso,
        )

    # --------------------------------------------------------------------------
    # Raw Messages API (Immutable History)
    # --------------------------------------------------------------------------

    def append_message(
        self,
        session_id: str,
        role: Union[MessageRole, str],
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        token_count: Optional[int] = None,
    ) -> Message:
        """
        Append a raw conversational event to the immutable archive.
        
        Sequence numbers are automatically assigned monotonically per session.
        """
        if isinstance(role, MessageRole):
            role_val = role.value
        else:
            role_val = str(role)

        msg_id = f"msg_{uuid.uuid4().hex[:12]}"
        now_iso = utc_now_iso()
        meta = metadata or {}
        tokens = token_count if token_count is not None else estimate_tokens(content)

        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COALESCE(MAX(sequence_num), 0) + 1 FROM messages WHERE session_id = ?;",
                (session_id,),
            )
            next_seq = cursor.fetchone()[0]

            try:
                conn.execute(
                    """
                    INSERT INTO messages (
                        id, session_id, role, content, sequence_num,
                        token_count, timestamp, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        msg_id,
                        session_id,
                        role_val,
                        content,
                        next_seq,
                        tokens,
                        now_iso,
                        json.dumps(meta),
                    ),
                )
            except sqlite3.IntegrityError as e:
                raise DatabaseError(f"Failed to append message: {e}") from e

        return Message(
            id=msg_id,
            session_id=session_id,
            role=role_val,
            content=content,
            sequence_num=next_seq,
            token_count=tokens,
            timestamp=now_iso,
            metadata=meta,
        )

    def get_message(self, message_id: str) -> Message:
        """Retrieve an immutable message by its unique ID."""
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, session_id, role, content, sequence_num,
                   token_count, timestamp, metadata
            FROM messages WHERE id = ?;
            """,
            (message_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise MessageNotFoundError(f"Message '{message_id}' not found.")

        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        return Message(
            id=row["id"],
            session_id=row["session_id"],
            role=row["role"],
            content=row["content"],
            sequence_num=row["sequence_num"],
            token_count=row["token_count"],
            timestamp=row["timestamp"],
            metadata=metadata,
        )

    def get_messages(
        self,
        session_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Message]:
        """Retrieve ordered messages, optionally filtered by session ID."""
        conn = self.db.connect()
        query = "SELECT id, session_id, role, content, sequence_num, token_count, timestamp, metadata FROM messages"
        params: List[Any] = []

        if session_id:
            query += " WHERE session_id = ?"
            params.append(session_id)

        query += " ORDER BY sequence_num ASC, timestamp ASC"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
            if offset is not None:
                query += " OFFSET ?"
                params.append(offset)

        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        messages = []
        for r in rows:
            meta = json.loads(r["metadata"]) if r["metadata"] else {}
            messages.append(
                Message(
                    id=r["id"],
                    session_id=r["session_id"],
                    role=r["role"],
                    content=r["content"],
                    sequence_num=r["sequence_num"],
                    token_count=r["token_count"],
                    timestamp=r["timestamp"],
                    metadata=meta,
                )
            )
        return messages

    # --------------------------------------------------------------------------
    # Memory & Provenance API
    # --------------------------------------------------------------------------

    def create_memory(
        self,
        content: str,
        tier: Union[MemoryTier, str],
        source_message_ids: List[str],
        confidence: float = 1.0,
        status: Union[MemoryStatus, str] = MemoryStatus.ACTIVE,
        metadata: Optional[Dict[str, Any]] = None,
        token_count: Optional[int] = None,
    ) -> Memory:
        """
        Create a memory unit linked to its source messages (provenance).
        """
        if not source_message_ids:
            raise InvalidCommitError("Memory must have at least one source message ID for provenance.")

        tier_val = tier.value if isinstance(tier, MemoryTier) else str(tier)
        status_val = status.value if isinstance(status, MemoryStatus) else str(status)

        # Validate that all source messages exist
        conn = self.db.connect()
        cursor = conn.cursor()
        placeholders = ",".join("?" for _ in source_message_ids)
        cursor.execute(f"SELECT id FROM messages WHERE id IN ({placeholders});", source_message_ids)
        found_ids = {r[0] for r in cursor.fetchall()}
        missing = set(source_message_ids) - found_ids
        if missing:
            raise MessageNotFoundError(f"Source message(s) not found for provenance: {missing}")

        mem_id = f"mem_{uuid.uuid4().hex[:12]}"
        now_iso = utc_now_iso()
        meta = metadata or {}
        tokens = token_count if token_count is not None else estimate_tokens(content)

        with self.db.transaction() as tx:
            tx.execute(
                """
                INSERT INTO memories (
                    id, content, tier, status, confidence,
                    token_count, created_at, updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    mem_id,
                    content,
                    tier_val,
                    status_val,
                    confidence,
                    tokens,
                    now_iso,
                    now_iso,
                    json.dumps(meta),
                ),
            )

            # Insert many-to-many provenance links
            for msg_id in source_message_ids:
                tx.execute(
                    "INSERT INTO memory_sources (memory_id, message_id) VALUES (?, ?);",
                    (mem_id, msg_id),
                )

        return Memory(
            id=mem_id,
            content=content,
            tier=tier_val,
            status=status_val,
            confidence=confidence,
            token_count=tokens,
            source_message_ids=list(source_message_ids),
            created_at=now_iso,
            updated_at=now_iso,
            metadata=meta,
        )

    def get_memory(self, memory_id: str) -> Memory:
        """Retrieve a memory record with all its source message provenance IDs."""
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, content, tier, status, confidence, token_count,
                   created_at, updated_at, metadata
            FROM memories WHERE id = ?;
            """,
            (memory_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise MemoryNotFoundError(f"Memory '{memory_id}' not found.")

        cursor.execute(
            "SELECT message_id FROM memory_sources WHERE memory_id = ? ORDER BY message_id;",
            (memory_id,),
        )
        source_ids = [r[0] for r in cursor.fetchall()]
        meta = json.loads(row["metadata"]) if row["metadata"] else {}

        return Memory(
            id=row["id"],
            content=row["content"],
            tier=row["tier"],
            status=row["status"],
            confidence=row["confidence"],
            token_count=row["token_count"],
            source_message_ids=source_ids,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=meta,
        )

    # --------------------------------------------------------------------------
    # Commit & Memory State Reconstruction API
    # --------------------------------------------------------------------------

    def create_commit(
        self,
        message: str,
        reason: str,
        active_memory_ids: Optional[List[str]] = None,
        branch_name: Optional[str] = None,
        author: str = "agent:auto",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Commit:
        """
        Create an immutable versioned commit recording active memory state mutations.
        
        If active_memory_ids is None, inherits active memory state from current HEAD.
        """
        branch_target = branch_name or self.active_branch
        branch = self.get_branch(branch_target)
        parent_commit_id = branch.head_commit_id

        # Calculate token counts
        tokens_before = 0
        if parent_commit_id:
            parent_memories = self.reconstruct_memory_state(parent_commit_id)
            tokens_before = sum(m.token_count for m in parent_memories)

        # Resolve active memory IDs
        resolved_memory_ids: List[str] = []
        if active_memory_ids is None:
            if parent_commit_id:
                resolved_memory_ids = [m.id for m in parent_memories]
        else:
            resolved_memory_ids = list(active_memory_ids)

        # Validate that all memories exist and load them
        memories_map: Dict[str, Memory] = {}
        for m_id in resolved_memory_ids:
            memories_map[m_id] = self.get_memory(m_id)

        tokens_after = sum(m.token_count for m in memories_map.values())
        tokens_saved = max(0, tokens_before - tokens_after)

        commit_id = f"c_{uuid.uuid4().hex[:12]}"
        now_iso = utc_now_iso()
        meta = metadata or {}

        with self.db.transaction() as tx:
            tx.execute(
                """
                INSERT INTO commits (
                    id, parent_commit_id, branch, message, reason, author,
                    token_count_before, token_count_after, tokens_saved,
                    timestamp, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    commit_id,
                    parent_commit_id,
                    branch_target,
                    message,
                    reason,
                    author,
                    tokens_before,
                    tokens_after,
                    tokens_saved,
                    now_iso,
                    json.dumps(meta),
                ),
            )

            # Record commit memory state snapshot
            for mem in memories_map.values():
                tx.execute(
                    """
                    INSERT INTO commit_memories (commit_id, memory_id, tier, status)
                    VALUES (?, ?, ?, ?);
                    """,
                    (commit_id, mem.id, mem.tier, mem.status),
                )

            # Move branch HEAD pointer
            tx.execute(
                "UPDATE branches SET head_commit_id = ?, updated_at = ? WHERE name = ?;",
                (commit_id, now_iso, branch_target),
            )

        return Commit(
            id=commit_id,
            parent_commit_id=parent_commit_id,
            branch=branch_target,
            message=message,
            reason=reason,
            author=author,
            token_count_before=tokens_before,
            token_count_after=tokens_after,
            tokens_saved=tokens_saved,
            timestamp=now_iso,
            metadata=meta,
        )

    def get_commit(self, commit_id: str) -> Commit:
        """Retrieve an immutable commit by ID."""
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, parent_commit_id, branch, message, reason, author,
                   token_count_before, token_count_after, tokens_saved,
                   timestamp, metadata
            FROM commits WHERE id = ?;
            """,
            (commit_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise CommitNotFoundError(f"Commit '{commit_id}' not found.")

        meta = json.loads(row["metadata"]) if row["metadata"] else {}
        return Commit(
            id=row["id"],
            parent_commit_id=row["parent_commit_id"],
            branch=row["branch"],
            message=row["message"],
            reason=row["reason"],
            author=row["author"],
            token_count_before=row["token_count_before"],
            token_count_after=row["token_count_after"],
            tokens_saved=row["tokens_saved"],
            timestamp=row["timestamp"],
            metadata=meta,
        )

    def reconstruct_memory_state(self, commit_id: str) -> List[Memory]:
        """
        Deterministically reconstruct the active memory state at a specific commit.
        
        Only ACTIVE memories linked to this commit are returned.
        """
        # Validate commit existence
        self.get_commit(commit_id)

        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.id, m.content, cm.tier, cm.status, m.confidence,
                   m.token_count, m.created_at, m.updated_at, m.metadata
            FROM commit_memories cm
            JOIN memories m ON cm.memory_id = m.id
            WHERE cm.commit_id = ? AND cm.status = 'ACTIVE'
            ORDER BY m.created_at ASC;
            """,
            (commit_id,),
        )
        rows = cursor.fetchall()

        reconstructed: List[Memory] = []
        for r in rows:
            cursor.execute(
                "SELECT message_id FROM memory_sources WHERE memory_id = ? ORDER BY message_id;",
                (r["id"],),
            )
            source_ids = [s[0] for s in cursor.fetchall()]
            meta = json.loads(r["metadata"]) if r["metadata"] else {}
            reconstructed.append(
                Memory(
                    id=r["id"],
                    content=r["content"],
                    tier=r["tier"],
                    status=r["status"],
                    confidence=r["confidence"],
                    token_count=r["token_count"],
                    source_message_ids=source_ids,
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    metadata=meta,
                )
            )

        return reconstructed

    def get_commit_history(
        self, branch_name: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Commit]:
        """
        Traverse the commit DAG backwards from the branch HEAD.
        """
        branch = self.get_branch(branch_name or self.active_branch)
        current_id = branch.head_commit_id
        commits: List[Commit] = []

        while current_id is not None:
            commit = self.get_commit(current_id)
            commits.append(commit)
            if limit and len(commits) >= limit:
                break
            current_id = commit.parent_commit_id

        return commits

    # --------------------------------------------------------------------------
    # Branching API
    # --------------------------------------------------------------------------

    def get_branch(self, branch_name: str) -> Branch:
        """Retrieve a branch by name."""
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, head_commit_id, created_at, updated_at FROM branches WHERE name = ?;",
            (branch_name,),
        )
        row = cursor.fetchone()
        if not row:
            raise BranchNotFoundError(f"Branch '{branch_name}' not found.")
        return Branch(
            name=row["name"],
            head_commit_id=row["head_commit_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_branches(self) -> List[Branch]:
        """List all branches in the repository."""
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name, head_commit_id, created_at, updated_at FROM branches ORDER BY name ASC;")
        rows = cursor.fetchall()
        return [
            Branch(
                name=r["name"],
                head_commit_id=r["head_commit_id"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]

    def create_branch(
        self, branch_name: str, source_commit_id: Optional[str] = None
    ) -> Branch:
        """
        Create a new branch pointing to source_commit_id or the current branch HEAD.
        """
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM branches WHERE name = ?;", (branch_name,))
        if cursor.fetchone():
            raise BranchAlreadyExistsError(f"Branch '{branch_name}' already exists.")

        target_commit_id = source_commit_id
        if target_commit_id is None:
            current_branch = self.get_branch(self.active_branch)
            target_commit_id = current_branch.head_commit_id

        if target_commit_id is not None:
            # Validate commit exists
            self.get_commit(target_commit_id)

        now_iso = utc_now_iso()
        with self.db.transaction() as tx:
            tx.execute(
                """
                INSERT INTO branches (name, head_commit_id, created_at, updated_at)
                VALUES (?, ?, ?, ?);
                """,
                (branch_name, target_commit_id, now_iso, now_iso),
            )

        return Branch(
            name=branch_name,
            head_commit_id=target_commit_id,
            created_at=now_iso,
            updated_at=now_iso,
        )

    def switch_branch(self, branch_name: str) -> Branch:
        """Switch active working branch."""
        branch = self.get_branch(branch_name)
        self.active_branch = branch.name
        return branch

    def get_current_head(self, branch_name: Optional[str] = None) -> Optional[Commit]:
        """Get the current HEAD commit for the specified or active branch."""
        target = branch_name or self.active_branch
        branch = self.get_branch(target)
        if not branch.head_commit_id:
            return None
        return self.get_commit(branch.head_commit_id)
