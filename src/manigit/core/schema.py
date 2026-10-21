"""
Database DDL schema, migrations, and immutability triggers for SQLite.
"""

CURRENT_SCHEMA_VERSION = 1

SCHEMA_V1_SQL = """
-- Schema migration metadata
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

-- Raw conversation events (append-only, immutable history)
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    sequence_num INTEGER NOT NULL,
    token_count INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    metadata TEXT,
    CONSTRAINT uq_session_sequence UNIQUE (session_id, sequence_num)
);

CREATE INDEX IF NOT EXISTS idx_messages_session_seq 
    ON messages(session_id, sequence_num);

CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
    ON messages(timestamp);

-- Persistent memory units (derived knowledge records)
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    tier TEXT NOT NULL,
    status TEXT NOT NULL,
    confidence REAL NOT NULL,
    token_count INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_memories_status 
    ON memories(status);

CREATE INDEX IF NOT EXISTS idx_memories_tier 
    ON memories(tier);

-- Many-to-many provenance link between memories and source messages
CREATE TABLE IF NOT EXISTS memory_sources (
    memory_id TEXT NOT NULL,
    message_id TEXT NOT NULL,
    PRIMARY KEY (memory_id, message_id),
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE RESTRICT,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_memory_sources_message 
    ON memory_sources(message_id);

-- Versioned commits (atomic snapshots of memory mutations)
CREATE TABLE IF NOT EXISTS commits (
    id TEXT PRIMARY KEY,
    parent_commit_id TEXT,
    branch TEXT NOT NULL,
    message TEXT NOT NULL,
    reason TEXT NOT NULL,
    author TEXT NOT NULL,
    token_count_before INTEGER NOT NULL,
    token_count_after INTEGER NOT NULL,
    tokens_saved INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (parent_commit_id) REFERENCES commits(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_commits_parent 
    ON commits(parent_commit_id);

CREATE INDEX IF NOT EXISTS idx_commits_branch 
    ON commits(branch);

-- Commit memory tree (reconstructable memory state for every commit)
CREATE TABLE IF NOT EXISTS commit_memories (
    commit_id TEXT NOT NULL,
    memory_id TEXT NOT NULL,
    tier TEXT NOT NULL,
    status TEXT NOT NULL,
    PRIMARY KEY (commit_id, memory_id),
    FOREIGN KEY (commit_id) REFERENCES commits(id) ON DELETE RESTRICT,
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_commit_memories_mem 
    ON commit_memories(memory_id);

-- Named branch references (HEAD pointers)
CREATE TABLE IF NOT EXISTS branches (
    name TEXT PRIMARY KEY,
    head_commit_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (head_commit_id) REFERENCES commits(id) ON DELETE RESTRICT
);

-- ============================================================================
-- Immutability Triggers
-- Prevent destructive UPDATE and DELETE operations on historical records
-- ============================================================================

-- Messages Immutability
CREATE TRIGGER IF NOT EXISTS trg_messages_prevent_update
BEFORE UPDATE ON messages
BEGIN
    SELECT RAISE(ABORT, 'ManiGit immutability violation: raw messages cannot be modified');
END;

CREATE TRIGGER IF NOT EXISTS trg_messages_prevent_delete
BEFORE DELETE ON messages
BEGIN
    SELECT RAISE(ABORT, 'ManiGit immutability violation: raw messages cannot be deleted');
END;

-- Commits Immutability
CREATE TRIGGER IF NOT EXISTS trg_commits_prevent_update
BEFORE UPDATE ON commits
BEGIN
    SELECT RAISE(ABORT, 'ManiGit immutability violation: historical commits cannot be modified');
END;

CREATE TRIGGER IF NOT EXISTS trg_commits_prevent_delete
BEFORE DELETE ON commits
BEGIN
    SELECT RAISE(ABORT, 'ManiGit immutability violation: historical commits cannot be deleted');
END;

-- Commit Memory State Immutability
CREATE TRIGGER IF NOT EXISTS trg_commit_memories_prevent_update
BEFORE UPDATE ON commit_memories
BEGIN
    SELECT RAISE(ABORT, 'ManiGit immutability violation: historical commit memory states cannot be modified');
END;

CREATE TRIGGER IF NOT EXISTS trg_commit_memories_prevent_delete
BEFORE DELETE ON commit_memories
BEGIN
    SELECT RAISE(ABORT, 'ManiGit immutability violation: historical commit memory states cannot be deleted');
END;

-- Provenance Link Immutability
CREATE TRIGGER IF NOT EXISTS trg_memory_sources_prevent_update
BEFORE UPDATE ON memory_sources
BEGIN
    SELECT RAISE(ABORT, 'ManiGit immutability violation: provenance relationships cannot be modified');
END;

CREATE TRIGGER IF NOT EXISTS trg_memory_sources_prevent_delete
BEFORE DELETE ON memory_sources
BEGIN
    SELECT RAISE(ABORT, 'ManiGit immutability violation: provenance relationships cannot be deleted');
END;
"""
