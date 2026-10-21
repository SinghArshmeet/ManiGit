"""
Unit tests for MemoryRetriever active state filtering and candidate retrieval.
"""

import os
import tempfile
import unittest

from manigit.context.retrieval import MemoryRetriever
from manigit.core.models import MemoryStatus, MemoryTier, MessageRole
from manigit.core.repository import ManiGitRepository


class TestMemoryRetriever(unittest.TestCase):
    """Test suite for MemoryRetriever filtering and candidate selection."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "retrieval_test.db")
        self.repo = ManiGitRepository(self.db_path)
        self.repo.initialize_repository()

        # Seed messages and memories
        self.msg = self.repo.append_message("s1", MessageRole.USER, "Initial requirements")
        self.mem_verb = self.repo.create_memory("Backend = SQLite", MemoryTier.VERBATIM, [self.msg.id])
        self.mem_summ = self.repo.create_memory("Summary of scaling discussion", MemoryTier.SUMMARY, [self.msg.id])
        self.mem_arch = self.repo.create_memory("Old temporary note", MemoryTier.ARCHIVED, [self.msg.id])

        # Commit active memories (mem_verb, mem_summ, mem_arch)
        self.commit = self.repo.create_commit(
            message="Initial memory commit",
            reason="Seeding test data",
            active_memory_ids=[self.mem_verb.id, self.mem_summ.id, self.mem_arch.id],
        )

        self.retriever = MemoryRetriever(self.repo)

    def tearDown(self):
        self.repo.db.close()
        self.temp_dir.cleanup()

    def test_eligible_tiers_and_archived_exclusion(self):
        """Verify VERBATIM and SUMMARY are eligible, while ARCHIVED is pre-excluded."""
        eligible, excluded = self.retriever.retrieve_candidates(self.commit.id, "backend sqlite")

        eligible_ids = [m[0].id for m in eligible]
        excluded_ids = [m.memory_id for m in excluded]

        self.assertIn(self.mem_verb.id, eligible_ids)
        self.assertIn(self.mem_summ.id, eligible_ids)
        self.assertIn(self.mem_arch.id, excluded_ids)

        arch_exclusion = next(e for e in excluded if e.memory_id == self.mem_arch.id)
        self.assertEqual(arch_exclusion.exclusion_reason, "archived")

    def test_duplicate_content_suppression(self):
        """Verify identical memory content in active state is deduplicated."""
        dup_mem = self.repo.create_memory("Backend = SQLite", MemoryTier.VERBATIM, [self.msg.id])
        commit_dup = self.repo.create_commit(
            message="Commit with duplicate",
            reason="Testing dedup",
            active_memory_ids=[self.mem_verb.id, dup_mem.id],
        )

        eligible, excluded = self.retriever.retrieve_candidates(commit_dup.id, "sqlite")
        self.assertEqual(len(eligible), 1)
        self.assertEqual(len(excluded), 1)
        self.assertEqual(excluded[0].exclusion_reason, "duplicate")


if __name__ == "__main__":
    unittest.main()
