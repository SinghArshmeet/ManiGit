"""
Unit tests for memory units, tiers, and many-to-many provenance tracking.
"""

import os
import sqlite3
import tempfile
import unittest

from manigit.core.exceptions import (
    InvalidCommitError,
    MemoryNotFoundError,
    MessageNotFoundError,
)
from manigit.core.models import MemoryStatus, MemoryTier, MessageRole
from manigit.core.repository import ManiGitRepository


class TestMemories(unittest.TestCase):
    """Test suite for memory records and provenance relationships."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_memories.db")
        self.repo = ManiGitRepository(self.db_path)
        self.repo.initialize_repository()

        # Seed source messages
        self.msg1 = self.repo.append_message("s1", MessageRole.USER, "Constraint: Project must use SQLite.")
        self.msg2 = self.repo.append_message("s1", MessageRole.USER, "Constraint: Must run on Python 3.10+.")
        self.msg3 = self.repo.append_message("s1", MessageRole.ASSISTANT, "Acknowledged constraints.")

    def tearDown(self):
        self.repo.db.close()
        self.temp_dir.cleanup()

    def test_create_and_get_memory_with_single_source(self):
        """Verify creating memory with one source message."""
        mem = self.repo.create_memory(
            content="Database engine: SQLite only",
            tier=MemoryTier.VERBATIM,
            source_message_ids=[self.msg1.id],
            confidence=0.98,
            status=MemoryStatus.ACTIVE,
        )
        self.assertIsNotNone(mem.id)
        self.assertEqual(mem.content, "Database engine: SQLite only")
        self.assertEqual(mem.tier, "VERBATIM")
        self.assertEqual(mem.status, "ACTIVE")
        self.assertEqual(mem.confidence, 0.98)
        self.assertEqual(mem.source_message_ids, [self.msg1.id])

        fetched = self.repo.get_memory(mem.id)
        self.assertEqual(fetched.id, mem.id)
        self.assertEqual(fetched.source_message_ids, [self.msg1.id])

    def test_create_memory_with_multiple_sources_provenance(self):
        """Verify a single memory synthesized from multiple source messages (many-to-one)."""
        mem = self.repo.create_memory(
            content="System constraints: SQLite and Python 3.10+.",
            tier=MemoryTier.SUMMARY,
            source_message_ids=[self.msg1.id, self.msg2.id],
            confidence=0.95,
        )
        self.assertEqual(len(mem.source_message_ids), 2)
        self.assertIn(self.msg1.id, mem.source_message_ids)
        self.assertIn(self.msg2.id, mem.source_message_ids)

        fetched = self.repo.get_memory(mem.id)
        self.assertEqual(set(fetched.source_message_ids), {self.msg1.id, self.msg2.id})

    def test_single_message_contributes_to_multiple_memories(self):
        """Verify one source message can link to multiple memories (one-to-many)."""
        mem_a = self.repo.create_memory(
            content="Constraint: SQLite",
            tier=MemoryTier.VERBATIM,
            source_message_ids=[self.msg1.id],
        )
        mem_b = self.repo.create_memory(
            content="Summary: Architecture includes SQLite",
            tier=MemoryTier.SUMMARY,
            source_message_ids=[self.msg1.id, self.msg3.id],
        )
        self.assertIn(self.msg1.id, mem_a.source_message_ids)
        self.assertIn(self.msg1.id, mem_b.source_message_ids)

    def test_create_memory_with_nonexistent_message_fails(self):
        """Verify linking memory to non-existent message raises MessageNotFoundError."""
        with self.assertRaises(MessageNotFoundError):
            self.repo.create_memory(
                content="Ghost fact",
                tier=MemoryTier.VERBATIM,
                source_message_ids=["msg_does_not_exist"],
            )

    def test_create_memory_with_empty_sources_fails(self):
        """Verify creating memory without provenance raises InvalidCommitError."""
        with self.assertRaises(InvalidCommitError):
            self.repo.create_memory(
                content="Orphan fact",
                tier=MemoryTier.VERBATIM,
                source_message_ids=[],
            )

    def test_provenance_immutability_trigger(self):
        """Verify SQLite triggers prevent modification or deletion of provenance links."""
        mem = self.repo.create_memory(
            content="Immutable provenance fact",
            tier=MemoryTier.VERBATIM,
            source_message_ids=[self.msg1.id],
        )
        conn = self.repo.db.connect()

        # Direct SQL UPDATE attempt on memory_sources
        with self.assertRaises(sqlite3.DatabaseError) as ctx:
            conn.execute(
                "UPDATE memory_sources SET message_id = ? WHERE memory_id = ?;",
                (self.msg2.id, mem.id),
            )
        self.assertIn("ManiGit immutability violation", str(ctx.exception))

        # Direct SQL DELETE attempt on memory_sources
        with self.assertRaises(sqlite3.DatabaseError) as ctx:
            conn.execute(
                "DELETE FROM memory_sources WHERE memory_id = ?;",
                (mem.id,),
            )
        self.assertIn("ManiGit immutability violation", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
