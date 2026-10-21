"""
Unit tests for MemorySummarizer.
"""

import unittest

from manigit.core.models import Message, MessageRole
from manigit.memory.summarizer import MemorySummarizer
from manigit.models.mock import MockModelAdapter


class TestMemorySummarizer(unittest.TestCase):
    """Test suite for Tier 2 summarization of multi-turn dialogues."""

    def test_multi_turn_dialogue_condensation_preserves_provenance(self):
        """
        Verify multi-turn discussion is synthesized into a concise factual summary
        retaining all source message IDs and numbers.
        """
        m1 = Message("m1", "sess_1", MessageRole.USER.value, "We originally planned PostgreSQL.", 1, 10)
        m2 = Message("m2", "sess_1", MessageRole.ASSISTANT.value, "Yes, PostgreSQL would work well.", 2, 10)
        m3 = Message("m3", "sess_1", MessageRole.USER.value, "Actually, after discussing scaling to 50k users, we decided to use MongoDB.", 3, 20)
        m4 = Message("m4", "sess_1", MessageRole.ASSISTANT.value, "Understood. We'll use MongoDB for scaling to 50k users.", 4, 15)

        adapter = MockModelAdapter(
            default_summary_response="Project database decision changed from PostgreSQL to MongoDB due to 50k user scaling requirements."
        )
        summarizer = MemorySummarizer(adapter)
        result = summarizer.summarize_messages([m1, m2, m3, m4], topic="Database Decision")

        # 1. Summary content preserves key facts and numbers
        self.assertIn("MongoDB", result.summary_content)
        self.assertIn("50k", result.summary_content)
        self.assertIn("PostgreSQL", result.summary_content)

        # 2. Provenance contains all 4 source message IDs
        self.assertEqual(result.source_message_ids, ["m1", "m2", "m3", "m4"])

        # 3. Token savings are properly tracked
        self.assertEqual(result.original_token_count, 55)
        self.assertGreater(result.summary_token_count, 0)
        self.assertGreater(result.tokens_saved, 0)

        # 4. Original messages remain completely unchanged
        self.assertEqual(m1.content, "We originally planned PostgreSQL.")
        self.assertEqual(m3.content, "Actually, after discussing scaling to 50k users, we decided to use MongoDB.")


if __name__ == "__main__":
    unittest.main()
