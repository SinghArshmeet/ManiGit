"""
Integration tests validating repository immutability guarantees.
"""

import os
import sqlite3
import tempfile
import unittest

from manigit.core.models import MemoryTier, MessageRole
from manigit.core.repository import ManiGitRepository


class TestImmutability(unittest.TestCase):
    """Explicit tests verifying that historical records cannot be modified or deleted."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "immutability_test.db")
        self.repo = ManiGitRepository(self.db_path)
        self.repo.initialize_repository()

        self.msg = self.repo.append_message("sess_immut", MessageRole.USER, "Ground truth message")
        self.mem = self.repo.create_memory("Ground truth fact", MemoryTier.VERBATIM, [self.msg.id])
        self.commit = self.repo.create_commit("Root fact commit", "Genesis of fact", [self.mem.id])

    def tearDown(self):
        self.repo.db.close()
        self.temp_dir.cleanup()

    def test_raw_message_cannot_be_updated_or_deleted(self):
        """Verify messages table blocks UPDATE and DELETE."""
        conn = self.repo.db.connect()

        with self.assertRaises(sqlite3.DatabaseError) as ctx_upd:
            conn.execute("UPDATE messages SET content = 'Changed' WHERE id = ?;", (self.msg.id,))
        self.assertIn("ManiGit immutability violation: raw messages cannot be modified", str(ctx_upd.exception))

        with self.assertRaises(sqlite3.DatabaseError) as ctx_del:
            conn.execute("DELETE FROM messages WHERE id = ?;", (self.msg.id,))
        self.assertIn("ManiGit immutability violation: raw messages cannot be deleted", str(ctx_del.exception))

    def test_historical_commits_cannot_be_updated_or_deleted(self):
        """Verify commits table blocks UPDATE and DELETE."""
        conn = self.repo.db.connect()

        with self.assertRaises(sqlite3.DatabaseError) as ctx_upd:
            conn.execute("UPDATE commits SET message = 'Rewritten history' WHERE id = ?;", (self.commit.id,))
        self.assertIn("ManiGit immutability violation: historical commits cannot be modified", str(ctx_upd.exception))

        with self.assertRaises(sqlite3.DatabaseError) as ctx_del:
            conn.execute("DELETE FROM commits WHERE id = ?;", (self.commit.id,))
        self.assertIn("ManiGit immutability violation: historical commits cannot be deleted", str(ctx_del.exception))

    def test_commit_memory_state_cannot_be_updated_or_deleted(self):
        """Verify commit_memories table blocks UPDATE and DELETE."""
        conn = self.repo.db.connect()

        with self.assertRaises(sqlite3.DatabaseError) as ctx_upd:
            conn.execute(
                "UPDATE commit_memories SET status = 'TOMBSTONE' WHERE commit_id = ?;",
                (self.commit.id,),
            )
        self.assertIn("ManiGit immutability violation: historical commit memory states cannot be modified", str(ctx_upd.exception))

        with self.assertRaises(sqlite3.DatabaseError) as ctx_del:
            conn.execute(
                "DELETE FROM commit_memories WHERE commit_id = ?;",
                (self.commit.id,),
            )
        self.assertIn("ManiGit immutability violation: historical commit memory states cannot be deleted", str(ctx_del.exception))

    def test_provenance_links_cannot_be_updated_or_deleted(self):
        """Verify memory_sources table blocks UPDATE and DELETE."""
        conn = self.repo.db.connect()

        with self.assertRaises(sqlite3.DatabaseError) as ctx_upd:
            conn.execute(
                "UPDATE memory_sources SET message_id = 'other' WHERE memory_id = ?;",
                (self.mem.id,),
            )
        self.assertIn("ManiGit immutability violation: provenance relationships cannot be modified", str(ctx_upd.exception))

        with self.assertRaises(sqlite3.DatabaseError) as ctx_del:
            conn.execute(
                "DELETE FROM memory_sources WHERE memory_id = ?;",
                (self.mem.id,),
            )
        self.assertIn("ManiGit immutability violation: provenance relationships cannot be deleted", str(ctx_del.exception))

    def test_inspecting_old_commit_does_not_rewrite_history(self):
        """
        Verify that reconstructing or inspecting earlier commits does not alter
        the current branch HEAD or wipe out subsequent commits.
        """
        c2 = self.repo.create_commit("Second commit", "Progressing", [self.mem.id])
        c3 = self.repo.create_commit("Third commit", "Finishing", [self.mem.id])

        # Inspect old commit state
        state_c1 = self.repo.reconstruct_memory_state(self.commit.id)
        self.assertEqual(len(state_c1), 1)

        # Verify HEAD is still c3
        current_head = self.repo.get_current_head("main")
        self.assertEqual(current_head.id, c3.id)

        # Verify all 3 commits remain intact in history
        history = self.repo.get_commit_history("main")
        history_ids = [c.id for c in history]
        self.assertIn(c3.id, history_ids)
        self.assertIn(c2.id, history_ids)
        self.assertIn(self.commit.id, history_ids)


if __name__ == "__main__":
    unittest.main()
