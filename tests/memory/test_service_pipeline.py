"""
End-to-end integration tests for the MemoryService workflow.
"""

import os
import tempfile
import unittest

from manigit.core.models import MessageRole
from manigit.core.repository import ManiGitRepository
from manigit.memory.service import MemoryService
from manigit.models.mock import MockModelAdapter


class TestMemoryServicePipeline(unittest.TestCase):
    """Integration test suite for the complete Memory Intelligence service workflow."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "service_test.db")
        self.repo = ManiGitRepository(self.db_path)
        self.repo.initialize_repository()

        self.adapter = MockModelAdapter()
        self.service = MemoryService(self.repo, self.adapter)

    def tearDown(self):
        self.repo.db.close()
        self.temp_dir.cleanup()

    def test_full_flow_with_contradiction_and_supersession(self):
        """
        End-to-end test verifying:
        1. Fact 1 (PostgreSQL) is ingested, classified, and committed.
        2. Fact 2 (Switch to MongoDB) is ingested, contradiction detected, PostgreSQL superseded.
        3. Commit 2 active state has MongoDB only.
        4. Reconstructing Commit 1 returns PostgreSQL intact.
        5. Raw messages archive preserves both messages unchanged.
        6. Provenance correctly maps each memory to its source message.
        """
        # Step 1: Ingest Message 1
        msg1 = self.repo.append_message(
            session_id="session_db",
            role=MessageRole.USER,
            content="We decided that our backend database must be PostgreSQL.",
        )
        result1 = self.service.process_message(msg1)
        self.assertEqual(result1.classification.tier, "VERBATIM")
        self.assertFalse(result1.contradiction.has_contradiction)
        self.assertIsNotNone(result1.new_memory)
        self.assertEqual(result1.new_memory.source_message_ids, [msg1.id])

        # Commit Step 1
        commit1 = self.service.commit_memory_update(result1, "Add PostgreSQL database decision")
        state1 = self.repo.reconstruct_memory_state(commit1.id)
        self.assertEqual(len(state1), 1)
        self.assertIn("PostgreSQL", state1[0].content)

        # Step 2: Ingest Message 2 (Contradiction / Revision)
        msg2 = self.repo.append_message(
            session_id="session_db",
            role=MessageRole.USER,
            content="We decided to change the database from PostgreSQL to MongoDB.",
        )
        result2 = self.service.process_message(msg2)

        # Verify contradiction was detected
        self.assertTrue(result2.contradiction.has_contradiction)
        self.assertEqual(result2.superseded_memory_id, state1[0].id)
        self.assertEqual(result2.why_report.decision, "SUPERSEDE")
        self.assertEqual(result2.why_report.predecessor_memory_id, state1[0].id)
        self.assertIsNotNone(result2.new_memory)
        self.assertIn("MongoDB", result2.new_memory.content)

        # Commit Step 2
        commit2 = self.service.commit_memory_update(result2, "Switch database decision to MongoDB")
        state2 = self.repo.reconstruct_memory_state(commit2.id)

        # 3. State 2 only contains MongoDB as active memory
        self.assertEqual(len(state2), 1)
        self.assertIn("MongoDB", state2[0].content)
        self.assertEqual(state2[0].source_message_ids, [msg2.id])

        # 4. State 1 remains 100% reconstructable with PostgreSQL intact
        reconstructed_state1 = self.repo.reconstruct_memory_state(commit1.id)
        self.assertEqual(len(reconstructed_state1), 1)
        self.assertIn("PostgreSQL", reconstructed_state1[0].content)
        self.assertEqual(reconstructed_state1[0].id, state1[0].id)

        # 5. Raw messages archive preserves both messages untouched
        all_messages = self.repo.get_messages(session_id="session_db")
        self.assertEqual(len(all_messages), 2)
        self.assertEqual(all_messages[0].id, msg1.id)
        self.assertEqual(all_messages[1].id, msg2.id)

        # 6. Commit Why Reports are stored in commit metadata
        c2_fetched = self.repo.get_commit(commit2.id)
        self.assertIn("why_report", c2_fetched.metadata)
        self.assertEqual(c2_fetched.metadata["why_report"]["decision"], "SUPERSEDE")

    def test_archiving_conversational_filler(self):
        """
        Verify that greetings/small talk are classified as ARCHIVED,
        produce a Why Report explaining the archive decision,
        and do not add any active memory records.
        """
        msg = self.repo.append_message("s2", MessageRole.USER, "Hey there, good morning!")
        result = self.service.process_message(msg)

        self.assertEqual(result.classification.tier, "ARCHIVED")
        self.assertEqual(result.why_report.decision, "ARCHIVE")
        self.assertIsNone(result.new_memory)
        self.assertEqual(len(result.active_memory_ids_for_commit), 0)


if __name__ == "__main__":
    unittest.main()
