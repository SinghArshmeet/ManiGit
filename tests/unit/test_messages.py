"""
Unit tests for immutable raw message persistence and retrieval.
"""

import os
import sqlite3
import tempfile
import unittest

from manigit.core.exceptions import MessageNotFoundError
from manigit.core.models import MessageRole
from manigit.core.repository import ManiGitRepository


class TestMessages(unittest.TestCase):
    """Test suite for message appending, sequencing, and immutability."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_repo.db")
        self.repo = ManiGitRepository(self.db_path)
        self.repo.initialize_repository()

    def tearDown(self):
        self.repo.db.close()
        self.temp_dir.cleanup()

    def test_append_and_get_message(self):
        """Verify message appending and retrieval by ID."""
        msg = self.repo.append_message(
            session_id="session_alpha",
            role=MessageRole.USER,
            content="Hello agent! Remember my budget is $5,000.",
            metadata={"source": "slack"},
        )
        self.assertIsNotNone(msg.id)
        self.assertEqual(msg.session_id, "session_alpha")
        self.assertEqual(msg.role, "user")
        self.assertEqual(msg.sequence_num, 1)
        self.assertTrue(msg.token_count > 0)
        self.assertEqual(msg.metadata["source"], "slack")

        fetched = self.repo.get_message(msg.id)
        self.assertEqual(fetched.id, msg.id)
        self.assertEqual(fetched.content, msg.content)
        self.assertEqual(fetched.sequence_num, 1)

    def test_non_existent_message_raises_error(self):
        """Verify retrieving non-existent message raises MessageNotFoundError."""
        with self.assertRaises(MessageNotFoundError):
            self.repo.get_message("msg_non_existent")

    def test_message_ordering_and_sequence_numbering(self):
        """Verify messages maintain monotonic sequence numbers within a session."""
        m1 = self.repo.append_message("sess_1", MessageRole.USER, "Turn 1")
        m2 = self.repo.append_message("sess_1", MessageRole.ASSISTANT, "Turn 2")
        m3 = self.repo.append_message("sess_1", MessageRole.USER, "Turn 3")

        self.assertEqual(m1.sequence_num, 1)
        self.assertEqual(m2.sequence_num, 2)
        self.assertEqual(m3.sequence_num, 3)

        messages = self.repo.get_messages(session_id="sess_1")
        self.assertEqual(len(messages), 3)
        self.assertEqual([m.sequence_num for m in messages], [1, 2, 3])

    def test_multiple_sessions_isolated_sequence_numbers(self):
        """Verify sequence numbers are tracked per session independently."""
        m_s1_1 = self.repo.append_message("sess_A", MessageRole.USER, "A1")
        m_s2_1 = self.repo.append_message("sess_B", MessageRole.USER, "B1")
        m_s1_2 = self.repo.append_message("sess_A", MessageRole.ASSISTANT, "A2")

        self.assertEqual(m_s1_1.sequence_num, 1)
        self.assertEqual(m_s2_1.sequence_num, 1)
        self.assertEqual(m_s1_2.sequence_num, 2)

        s_a = self.repo.get_messages(session_id="sess_A")
        s_b = self.repo.get_messages(session_id="sess_B")
        self.assertEqual(len(s_a), 2)
        self.assertEqual(len(s_b), 1)

    def test_messages_immutability_trigger(self):
        """Verify SQLite triggers prevent UPDATE and DELETE on raw messages."""
        msg = self.repo.append_message("sess_lock", MessageRole.USER, "Immutable fact")
        conn = self.repo.db.connect()

        # Direct SQL UPDATE attempt
        with self.assertRaises(sqlite3.DatabaseError) as ctx:
            conn.execute("UPDATE messages SET content = 'Tampered' WHERE id = ?;", (msg.id,))
        self.assertIn("ManiGit immutability violation", str(ctx.exception))

        # Direct SQL DELETE attempt
        with self.assertRaises(sqlite3.DatabaseError) as ctx:
            conn.execute("DELETE FROM messages WHERE id = ?;", (msg.id,))
        self.assertIn("ManiGit immutability violation", str(ctx.exception))

        # Verify content remained unchanged
        refetched = self.repo.get_message(msg.id)
        self.assertEqual(refetched.content, "Immutable fact")


if __name__ == "__main__":
    unittest.main()
