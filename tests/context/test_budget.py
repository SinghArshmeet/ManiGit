"""
Unit tests for ContextBudget allocation and boundary management.
"""

import unittest

from manigit.context.budget import ContextBudget
from manigit.context.models import SelectedMemory


class TestContextBudget(unittest.TestCase):
    """Test suite for token budget tracking, boundary enforcement, and greedy packing."""

    def test_exact_budget_boundary(self):
        """Verify allocation on exact budget boundary."""
        budget = ContextBudget(max_tokens=100)
        m1 = SelectedMemory("m1", "Content 1", "VERBATIM", 1.0, 60, 0.9, 0.9, "high relevance")
        m2 = SelectedMemory("m2", "Content 2", "VERBATIM", 1.0, 40, 0.8, 0.8, "high relevance")

        self.assertTrue(budget.allocate(m1))
        self.assertEqual(budget.used_tokens, 60)
        self.assertEqual(budget.remaining_tokens, 40)

        # m2 fits exactly in remaining 40
        self.assertTrue(budget.allocate(m2))
        self.assertEqual(budget.used_tokens, 100)
        self.assertEqual(budget.remaining_tokens, 0)

        # m3 cannot fit in 0 remaining
        m3 = SelectedMemory("m3", "Content 3", "VERBATIM", 1.0, 10, 0.7, 0.7, "relevant")
        self.assertFalse(budget.allocate(m3))
        self.assertEqual(budget.used_tokens, 100)
        self.assertEqual(len(budget.excluded), 1)
        self.assertIn("outside budget", budget.excluded[0].exclusion_reason)

    def test_candidate_larger_than_total_budget(self):
        """Verify candidate larger than total budget is rejected safely."""
        budget = ContextBudget(max_tokens=50)
        huge = SelectedMemory("huge", "Huge chunk", "SUMMARY", 1.0, 120, 0.9, 0.9, "high relevance")

        self.assertFalse(budget.allocate(huge))
        self.assertEqual(budget.used_tokens, 0)
        self.assertEqual(budget.remaining_tokens, 50)
        self.assertEqual(len(budget.excluded), 1)

    def test_zero_budget_rejects_all(self):
        """Verify zero budget rejects every candidate."""
        budget = ContextBudget(max_tokens=0)
        m = SelectedMemory("m", "Content", "VERBATIM", 1.0, 10, 0.9, 0.9, "high relevance")

        self.assertFalse(budget.allocate(m))
        self.assertEqual(budget.used_tokens, 0)
        self.assertEqual(budget.remaining_tokens, 0)
        self.assertEqual(len(budget.excluded), 1)

    def test_candidate_competition_and_greedy_skip(self):
        """
        Verify greedy token-budget selection behavior:
        Budget = 1000
        A = 300 (fits, rem: 700)
        B = 250 (fits, rem: 450)
        C = 500 (too big for 450, rejected)
        D = 150 (fits in 450, rem: 300)
        Total used: 700 <= 1000.
        """
        budget = ContextBudget(max_tokens=1000)
        mA = SelectedMemory("mA", "A", "VERBATIM", 1.0, 300, 0.9, 0.9, "reason")
        mB = SelectedMemory("mB", "B", "VERBATIM", 1.0, 250, 0.8, 0.8, "reason")
        mC = SelectedMemory("mC", "C", "VERBATIM", 1.0, 500, 0.7, 0.7, "reason")
        mD = SelectedMemory("mD", "D", "VERBATIM", 1.0, 150, 0.6, 0.6, "reason")

        self.assertTrue(budget.allocate(mA))
        self.assertTrue(budget.allocate(mB))
        self.assertFalse(budget.allocate(mC))  # 500 > 450 remaining
        self.assertTrue(budget.allocate(mD))   # 150 <= 450 remaining

        self.assertEqual(budget.used_tokens, 700)
        self.assertEqual(budget.remaining_tokens, 300)
        self.assertEqual([m.memory_id for m in budget.selected], ["mA", "mB", "mD"])
        self.assertEqual([m.memory_id for m in budget.excluded], ["mC"])

    def test_duplicate_rejection(self):
        """Verify duplicate memory IDs are excluded."""
        budget = ContextBudget(max_tokens=500)
        m = SelectedMemory("m1", "Content", "VERBATIM", 1.0, 50, 0.9, 0.9, "reason")

        self.assertTrue(budget.allocate(m))
        self.assertFalse(budget.allocate(m))  # Duplicate attempt
        self.assertEqual(len(budget.selected), 1)
        self.assertEqual(len(budget.excluded), 1)
        self.assertEqual(budget.excluded[0].exclusion_reason, "duplicate")


    def test_candidate_exactly_equal_to_remaining_budget(self):
        """Verify candidate whose token cost exactly equals remaining tokens is admitted."""
        budget = ContextBudget(max_tokens=100)
        m1 = SelectedMemory("m1", "First", "VERBATIM", 1.0, 75, 0.9, 0.9, "reason")
        m2 = SelectedMemory("m2", "Exact", "VERBATIM", 1.0, 25, 0.8, 0.8, "reason")

        self.assertTrue(budget.allocate(m1))
        self.assertEqual(budget.remaining_tokens, 25)
        self.assertTrue(budget.allocate(m2))
        self.assertEqual(budget.remaining_tokens, 0)
        self.assertEqual(budget.used_tokens, 100)
        self.assertEqual(len(budget.selected), 2)
        self.assertEqual(len(budget.excluded), 0)

    def test_empty_candidates_list(self):
        """Verify allocating no candidates yields zero tokens and full remaining budget."""
        budget = ContextBudget(max_tokens=500)
        self.assertEqual(budget.used_tokens, 0)
        self.assertEqual(budget.remaining_tokens, 500)
        self.assertEqual(len(budget.selected), 0)
        self.assertEqual(len(budget.excluded), 0)


if __name__ == "__main__":
    unittest.main()

