"""
Unit tests for commits, parent relationships, token accounting, and commit immutability.
"""

import os
import sqlite3
import tempfile
import unittest

from manigit.core.exceptions import CommitNotFoundError
from manigit.core.models import MemoryTier, MessageRole
from manigit.core.repository import ManiGitRepository


class TestCommits(unittest.TestCase):
    """Test suite for commit creation, DAG traversal, and token accounting."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_commits.db")
        self.repo = ManiGitRepository(self.db_path)
        self.root_branch = self.repo.initialize_repository()

        # Seed messages and memories
        self.msg = self.repo.append_message("s1", MessageRole.USER, "Store critical API token: 12345.")
        self.mem1 = self.repo.create_memory("Token: 12345", MemoryTier.VERBATIM, [self.msg.id])
        self.mem2 = self.repo.create_memory("Provider: Auth0", MemoryTier.VERBATIM, [self.msg.id])

    def tearDown(self):
        self.repo.db.close()
        self.temp_dir.cleanup()

    def test_create_and_get_commit(self):
        """Verify commit creation, parent linkage, and token calculation."""
        commit = self.repo.create_commit(
            message="Add auth token and provider",
            reason="User shared auth credentials",
            active_memory_ids=[self.mem1.id, self.mem2.id],
        )

        self.assertIsNotNone(commit.id)
        self.assertEqual(commit.parent_commit_id, self.root_branch.head_commit_id)
        self.assertEqual(commit.message, "Add auth token and provider")
        self.assertEqual(commit.reason, "User shared auth credentials")
        self.assertEqual(commit.branch, "main")
        self.assertEqual(commit.token_count_before, 0)
        self.assertEqual(commit.token_count_after, self.mem1.token_count + self.mem2.token_count)

        fetched = self.repo.get_commit(commit.id)
        self.assertEqual(fetched.id, commit.id)
        self.assertEqual(fetched.parent_commit_id, self.root_branch.head_commit_id)

    def test_token_accounting_delta(self):
        """Verify token_count_before, token_count_after, and tokens_saved."""
        # Commit 1: two memories
        c1 = self.repo.create_commit(
            message="Commit 1",
            reason="Adding 2 memories",
            active_memory_ids=[self.mem1.id, self.mem2.id],
        )

        # Commit 2: prune one memory to save tokens
        c2 = self.repo.create_commit(
            message="Commit 2",
            reason="Prune auth provider, retain token only",
            active_memory_ids=[self.mem1.id],
        )

        self.assertEqual(c2.parent_commit_id, c1.id)
        self.assertEqual(c2.token_count_before, self.mem1.token_count + self.mem2.token_count)
        self.assertEqual(c2.token_count_after, self.mem1.token_count)
        self.assertEqual(c2.tokens_saved, self.mem2.token_count)

    def test_commit_history_dag_traversal(self):
        """Verify commit history traverses parents backward from HEAD."""
        c1 = self.repo.create_commit("Step 1", "Reason 1", [self.mem1.id])
        c2 = self.repo.create_commit("Step 2", "Reason 2", [self.mem1.id, self.mem2.id])

        history = self.repo.get_commit_history(branch_name="main")
        commit_ids = [c.id for c in history]

        self.assertEqual(commit_ids[0], c2.id)
        self.assertEqual(commit_ids[1], c1.id)
        self.assertEqual(commit_ids[2], self.root_branch.head_commit_id)

    def test_commit_immutability_trigger(self):
        """Verify SQLite triggers prevent UPDATE and DELETE on commits."""
        commit = self.repo.create_commit("Original commit", "Reason", [self.mem1.id])
        conn = self.repo.db.connect()

        # Direct SQL UPDATE attempt
        with self.assertRaises(sqlite3.DatabaseError) as ctx:
            conn.execute("UPDATE commits SET message = 'Tampered' WHERE id = ?;", (commit.id,))
        self.assertIn("ManiGit immutability violation", str(ctx.exception))

        # Direct SQL DELETE attempt
        with self.assertRaises(sqlite3.DatabaseError) as ctx:
            conn.execute("DELETE FROM commits WHERE id = ?;", (commit.id,))
        self.assertIn("ManiGit immutability violation", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
