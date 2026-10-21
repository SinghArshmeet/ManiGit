"""
Integration tests for deterministic memory state reconstruction and branch state isolation.
"""

import os
import tempfile
import unittest

from manigit.core.models import MemoryStatus, MemoryTier, MessageRole
from manigit.core.repository import ManiGitRepository


class TestMemoryReconstruction(unittest.TestCase):
    """Integration test suite for historical memory state reconstruction."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "reconstruction_test.db")
        self.repo = ManiGitRepository(self.db_path)
        self.repo.initialize_repository()

        # Seed raw messages
        self.m1 = self.repo.append_message("s1", MessageRole.USER, "Constraint 1: Must use SQLite")
        self.m2 = self.repo.append_message("s1", MessageRole.USER, "Constraint 2: Max 4096 tokens")
        self.m3 = self.repo.append_message("s1", MessageRole.USER, "Constraint 3: Dark mode UI")

        # Create individual memories
        self.mem1 = self.repo.create_memory("Use SQLite", MemoryTier.VERBATIM, [self.m1.id])
        self.mem2 = self.repo.create_memory("Max 4096 tokens", MemoryTier.VERBATIM, [self.m2.id])
        self.mem3 = self.repo.create_memory("Dark mode UI", MemoryTier.VERBATIM, [self.m3.id])

    def tearDown(self):
        self.repo.db.close()
        self.temp_dir.cleanup()

    def test_linear_commit_chain_reconstruction(self):
        """
        Verify historical reconstruction across a linear sequence:
        Root -> Commit A -> Commit B -> Commit C.
        
        State at Root: []
        State at A:    [mem1]
        State at B:    [mem1, mem2]
        State at C:    [mem2, mem3] (mem1 removed/archived)
        """
        root_head = self.repo.get_current_head("main")
        root_state = self.repo.reconstruct_memory_state(root_head.id)
        self.assertEqual(len(root_state), 0)

        # Commit A: adds mem1
        commit_a = self.repo.create_commit(
            message="Commit A: Add SQLite constraint",
            reason="User constraint",
            active_memory_ids=[self.mem1.id],
        )

        # Commit B: adds mem2, retains mem1
        commit_b = self.repo.create_commit(
            message="Commit B: Add token limit constraint",
            reason="User constraint",
            active_memory_ids=[self.mem1.id, self.mem2.id],
        )

        # Commit C: replaces mem1 with mem3, retains mem2
        commit_c = self.repo.create_commit(
            message="Commit C: Prune SQLite, add dark mode",
            reason="Scope shift",
            active_memory_ids=[self.mem2.id, self.mem3.id],
        )

        # 1. Reconstruct state at Commit A
        state_a = self.repo.reconstruct_memory_state(commit_a.id)
        self.assertEqual({m.id for m in state_a}, {self.mem1.id})
        self.assertEqual(state_a[0].content, "Use SQLite")
        self.assertEqual(state_a[0].source_message_ids, [self.m1.id])

        # 2. Reconstruct state at Commit B
        state_b = self.repo.reconstruct_memory_state(commit_b.id)
        self.assertEqual({m.id for m in state_b}, {self.mem1.id, self.mem2.id})

        # 3. Reconstruct state at Commit C
        state_c = self.repo.reconstruct_memory_state(commit_c.id)
        self.assertEqual({m.id for m in state_c}, {self.mem2.id, self.mem3.id})

        # 4. Re-verify Commit A is completely unaffected by Commit B or C
        state_a_again = self.repo.reconstruct_memory_state(commit_a.id)
        self.assertEqual({m.id for m in state_a_again}, {self.mem1.id})

    def test_branch_divergence_reconstruction(self):
        """
        Verify that divergent branches maintain completely independent memory states:
        main:       Root -> Commit A -> Commit B
        experiment:                     Commit A -> Commit C
        """
        # Commit A on main
        commit_a = self.repo.create_commit(
            message="Commit A",
            reason="Initial fact",
            active_memory_ids=[self.mem1.id],
        )

        # Commit B on main
        commit_b = self.repo.create_commit(
            message="Commit B",
            reason="Mainline addition",
            active_memory_ids=[self.mem1.id, self.mem2.id],
        )

        # Create experiment branch starting at Commit A
        self.repo.create_branch("experiment", source_commit_id=commit_a.id)
        self.repo.switch_branch("experiment")

        # Commit C on experiment
        commit_c = self.repo.create_commit(
            message="Commit C",
            reason="Alternative exploration",
            active_memory_ids=[self.mem1.id, self.mem3.id],
        )

        # Verify state on main at HEAD (commit B)
        main_head = self.repo.get_current_head("main")
        main_state = self.repo.reconstruct_memory_state(main_head.id)
        self.assertEqual({m.id for m in main_state}, {self.mem1.id, self.mem2.id})

        # Verify state on experiment at HEAD (commit C)
        exp_head = self.repo.get_current_head("experiment")
        exp_state = self.repo.reconstruct_memory_state(exp_head.id)
        self.assertEqual({m.id for m in exp_state}, {self.mem1.id, self.mem3.id})

    def test_database_persistence_across_restart(self):
        """
        Verify that database content persists after connection closure and re-instantiation.
        """
        c1 = self.repo.create_commit(
            message="Persistent commit",
            reason="Testing persistence",
            active_memory_ids=[self.mem1.id, self.mem2.id],
        )
        saved_commit_id = c1.id

        # Close existing repository connection
        self.repo.db.close()

        # Re-open repository on same file
        restarted_repo = ManiGitRepository(self.db_path)
        restarted_repo.initialize_repository()

        # Check commit can be retrieved
        fetched_commit = restarted_repo.get_commit(saved_commit_id)
        self.assertEqual(fetched_commit.id, saved_commit_id)
        self.assertEqual(fetched_commit.message, "Persistent commit")

        # Check state reconstruction works identically
        reconstructed = restarted_repo.reconstruct_memory_state(saved_commit_id)
        self.assertEqual({m.id for m in reconstructed}, {self.mem1.id, self.mem2.id})

        restarted_repo.db.close()


if __name__ == "__main__":
    unittest.main()
