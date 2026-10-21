"""
Unit tests for branch creation, switching, HEAD movement, and branch isolation.
"""

import os
import tempfile
import unittest

from manigit.core.exceptions import (
    BranchAlreadyExistsError,
    BranchNotFoundError,
)
from manigit.core.models import MemoryTier, MessageRole
from manigit.core.repository import ManiGitRepository


class TestBranches(unittest.TestCase):
    """Test suite for branch management and HEAD tracking."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_branches.db")
        self.repo = ManiGitRepository(self.db_path)
        self.root_branch = self.repo.initialize_repository()

        self.msg = self.repo.append_message("s1", MessageRole.USER, "Initial input")
        self.mem = self.repo.create_memory("Fact 1", MemoryTier.VERBATIM, [self.msg.id])

    def tearDown(self):
        self.repo.db.close()
        self.temp_dir.cleanup()

    def test_default_branch_is_main(self):
        """Verify default branch is created as 'main' pointing to root commit."""
        branch = self.repo.get_branch("main")
        self.assertEqual(branch.name, "main")
        self.assertIsNotNone(branch.head_commit_id)

    def test_create_and_switch_branch(self):
        """Verify creating and switching to a new branch."""
        new_branch = self.repo.create_branch("feature-analysis")
        self.assertEqual(new_branch.name, "feature-analysis")
        self.assertEqual(new_branch.head_commit_id, self.root_branch.head_commit_id)

        switched = self.repo.switch_branch("feature-analysis")
        self.assertEqual(self.repo.active_branch, "feature-analysis")
        self.assertEqual(switched.name, "feature-analysis")

    def test_create_duplicate_branch_raises_error(self):
        """Verify creating existing branch raises BranchAlreadyExistsError."""
        with self.assertRaises(BranchAlreadyExistsError):
            self.repo.create_branch("main")

    def test_switch_non_existent_branch_raises_error(self):
        """Verify switching to missing branch raises BranchNotFoundError."""
        with self.assertRaises(BranchNotFoundError):
            self.repo.switch_branch("ghost-branch")

    def test_independent_branch_heads(self):
        """Verify commits to one branch do not advance HEAD on another branch."""
        # Commit to main
        c_main_1 = self.repo.create_commit("Main commit 1", "Reason", [self.mem.id])
        self.assertEqual(self.repo.get_branch("main").head_commit_id, c_main_1.id)

        # Create experiment branch off main
        exp_branch = self.repo.create_branch("experiment", source_commit_id=c_main_1.id)
        self.assertEqual(exp_branch.head_commit_id, c_main_1.id)

        # Switch to experiment and make a commit
        self.repo.switch_branch("experiment")
        mem2 = self.repo.create_memory("Fact 2", MemoryTier.SUMMARY, [self.msg.id])
        c_exp_1 = self.repo.create_commit("Experiment commit 1", "Reason", [self.mem.id, mem2.id])

        # Verify experiment HEAD advanced
        self.assertEqual(self.repo.get_branch("experiment").head_commit_id, c_exp_1.id)

        # Verify main HEAD remained unchanged at c_main_1
        self.assertEqual(self.repo.get_branch("main").head_commit_id, c_main_1.id)


if __name__ == "__main__":
    unittest.main()
