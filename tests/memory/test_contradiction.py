"""
Unit tests for Contradiction and Supersession detection.
"""

import unittest

from manigit.core.models import Memory, MemoryStatus, MemoryTier
from manigit.memory.contradiction import ContradictionDetector


class TestContradictionDetector(unittest.TestCase):
    """Test suite for detecting conflicts and supersessions in active memory."""

    def setUp(self):
        self.detector = ContradictionDetector()
        self.mem_postgres = Memory(
            id="mem_pg_01",
            content="Backend database = PostgreSQL",
            tier=MemoryTier.VERBATIM.value,
            status=MemoryStatus.ACTIVE.value,
            confidence=1.0,
            token_count=10,
            source_message_ids=["msg_1"],
        )
        self.mem_budget = Memory(
            id="mem_bg_02",
            content="Project budget limit: $5,000",
            tier=MemoryTier.VERBATIM.value,
            status=MemoryStatus.ACTIVE.value,
            confidence=1.0,
            token_count=8,
            source_message_ids=["msg_2"],
        )

    def test_explicit_replacement_detection(self):
        """Verify explicit replacement phrasing is detected as supersession."""
        new_text = "We decided to change the database from PostgreSQL to MongoDB."
        result = self.detector.detect(new_text, [self.mem_postgres, self.mem_budget])

        self.assertTrue(result.has_contradiction)
        self.assertEqual(result.superseded_memory_id, "mem_pg_01")
        self.assertEqual(result.conflict_type, "EXPLICIT_REPLACEMENT")
        self.assertEqual(result.historical_fact, "Backend database = PostgreSQL")
        self.assertEqual(result.current_fact, new_text)

    def test_key_value_overwrite_detection(self):
        """Verify key-value updates to the same attribute trigger supersession."""
        new_text = "Backend database = MongoDB"
        result = self.detector.detect(new_text, [self.mem_postgres, self.mem_budget])

        self.assertTrue(result.has_contradiction)
        self.assertEqual(result.superseded_memory_id, "mem_pg_01")
        self.assertIn(result.conflict_type, ("KEY_OVERWRITE", "TOPICAL_MUTATION"))

    def test_topic_mutation_detection(self):
        """Verify topical shift in same domain triggers supersession."""
        new_text = "Budget updated: New budget is $12,000"
        result = self.detector.detect(new_text, [self.mem_postgres, self.mem_budget])

        self.assertTrue(result.has_contradiction)
        self.assertEqual(result.superseded_memory_id, "mem_bg_02")
        self.assertIn("budget", result.explanation.lower())

    def test_no_contradiction_for_unrelated_facts(self):
        """Verify orthogonal, non-conflicting facts do not trigger contradiction."""
        new_text = "Frontend framework will be Next.js with TypeScript."
        result = self.detector.detect(new_text, [self.mem_postgres, self.mem_budget])

        self.assertFalse(result.has_contradiction)
        self.assertIsNone(result.superseded_memory_id)
        self.assertEqual(result.conflict_type, "NONE")


if __name__ == "__main__":
    unittest.main()
