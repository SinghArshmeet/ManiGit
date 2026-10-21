"""
Unit tests for Context ScoringEngine.
"""

import unittest

from manigit.context.scoring import ScoringEngine
from manigit.core.models import Memory, MemoryStatus, MemoryTier


class TestScoringEngine(unittest.TestCase):
    """Test suite for textual relevance calculation and priority scoring."""

    def setUp(self):
        self.engine = ScoringEngine()

    def test_relevance_token_overlap_and_phrase_match(self):
        """Verify token overlap and phrase matching calculate accurate relevance."""
        query = "database postgresql"
        match_text = "The backend database is PostgreSQL with high availability."
        irrelevant_text = "Frontend user interface uses React and Tailwind CSS."

        rel_match = self.engine.compute_relevance(query, match_text)
        rel_irrel = self.engine.compute_relevance(query, irrelevant_text)

        self.assertGreater(rel_match, 0.70)
        self.assertEqual(rel_irrel, 0.0)

    def test_empty_or_whitespace_query_returns_zero_relevance(self):
        """Verify empty and whitespace queries return 0.0 relevance."""
        self.assertEqual(self.engine.compute_relevance("", "Some memory text"), 0.0)
        self.assertEqual(self.engine.compute_relevance("   ", "Some memory text"), 0.0)

    def test_relevance_outranks_blind_verbatim_tier(self):
        """
        Verify that a relevant SUMMARY memory outranks an unrelated VERBATIM constraint.
        """
        query = "database options"

        relevant_summary = Memory(
            id="mem_summary_1",
            content="Summary of database options: PostgreSQL was selected over MongoDB due to relational consistency.",
            tier=MemoryTier.SUMMARY.value,
            status=MemoryStatus.ACTIVE.value,
            confidence=0.90,
            token_count=18,
            source_message_ids=["msg_1"],
        )

        unrelated_verbatim = Memory(
            id="mem_verbatim_2",
            content="UI color palette must strictly use dark mode (#121212) with neon accents.",
            tier=MemoryTier.VERBATIM.value,
            status=MemoryStatus.ACTIVE.value,
            confidence=1.0,
            token_count=15,
            source_message_ids=["msg_2"],
        )

        rel_summary = self.engine.compute_relevance(query, relevant_summary.content)
        rel_verbatim = self.engine.compute_relevance(query, unrelated_verbatim.content)

        prio_summary, reason_summary = self.engine.compute_priority(relevant_summary, rel_summary)
        prio_verbatim, reason_verbatim = self.engine.compute_priority(unrelated_verbatim, rel_verbatim)

        self.assertGreater(rel_summary, 0.50)
        self.assertEqual(rel_verbatim, 0.0)
        self.assertGreater(prio_summary, prio_verbatim)
        self.assertIn(reason_summary, ("important decision", "summary relevant", "high relevance", "relevant memory"))


    def test_constraint_boost_when_relevant(self):
        """Verify explicit constraints receive boost when relevant to query."""
        query = "database"
        constraint_mem = Memory(
            id="mem_c1",
            content="Backend database must strictly be PostgreSQL.",
            tier=MemoryTier.VERBATIM.value,
            status=MemoryStatus.ACTIVE.value,
            confidence=1.0,
            token_count=10,
        )
        non_constraint_mem = Memory(
            id="mem_nc2",
            content="Backend database is PostgreSQL.",
            tier=MemoryTier.VERBATIM.value,
            status=MemoryStatus.ACTIVE.value,
            confidence=1.0,
            token_count=8,
        )

        rel_c = self.engine.compute_relevance(query, constraint_mem.content)
        rel_nc = self.engine.compute_relevance(query, non_constraint_mem.content)

        prio_c, reason_c = self.engine.compute_priority(constraint_mem, rel_c)
        prio_nc, reason_nc = self.engine.compute_priority(non_constraint_mem, rel_nc)

        self.assertGreater(prio_c, prio_nc)
        self.assertEqual(reason_c, "explicit constraint")


    def test_case_a_zero_relevance_verbatim_vs_very_low_relevance_summary(self):
        """
        CASE A: Zero-relevance VERBATIM with constraints & decisions
        vs. Very-low-relevance SUMMARY.
        Relevance MUST dominate: the SUMMARY must outrank the unrelated VERBATIM.
        """
        unrelated_verbatim = Memory(
            id="mem_unrel",
            content="Color scheme must strictly use dark theme and decision was agreed.",
            tier=MemoryTier.VERBATIM.value,
            status=MemoryStatus.ACTIVE.value,
            confidence=1.0,
            token_count=12,
        )
        low_rel_summary = Memory(
            id="mem_low_rel",
            content="Historical summary mentions python libraries and general context.",
            tier=MemoryTier.SUMMARY.value,
            status=MemoryStatus.ACTIVE.value,
            confidence=0.5,
            token_count=10,
        )

        query = "python"
        rel_unrel = self.engine.compute_relevance(query, unrelated_verbatim.content)
        rel_low = self.engine.compute_relevance(query, low_rel_summary.content)

        self.assertEqual(rel_unrel, 0.0)
        self.assertGreater(rel_low, 0.0)

        prio_unrel, _ = self.engine.compute_priority(unrelated_verbatim, rel_unrel)
        prio_low, _ = self.engine.compute_priority(low_rel_summary, rel_low)

        # Relevance dominance guarantee
        self.assertGreater(prio_low, prio_unrel)

    def test_case_b_zero_relevance_verbatim_high_conf_vs_relevant_summary_low_conf(self):
        """
        CASE B: Zero-relevance VERBATIM with confidence = 1.0
        vs. Relevant SUMMARY with confidence = 0.1.
        Relevance MUST dominate: the low-confidence relevant summary must outrank the confident unrelated verbatim.
        """
        unrelated_verbatim = Memory(
            id="mem_unrel_conf1",
            content="AWS account credentials must never be committed to repository.",
            tier=MemoryTier.VERBATIM.value,
            status=MemoryStatus.ACTIVE.value,
            confidence=1.0,
            token_count=10,
        )
        relevant_summary = Memory(
            id="mem_rel_conf01",
            content="Discussion summary: PostgreSQL database setup was completed.",
            tier=MemoryTier.SUMMARY.value,
            status=MemoryStatus.ACTIVE.value,
            confidence=0.1,
            token_count=8,
        )

        query = "PostgreSQL database"
        rel_unrel = self.engine.compute_relevance(query, unrelated_verbatim.content)
        rel_summary = self.engine.compute_relevance(query, relevant_summary.content)

        self.assertEqual(rel_unrel, 0.0)
        self.assertGreater(rel_summary, 0.5)

        prio_unrel, _ = self.engine.compute_priority(unrelated_verbatim, rel_unrel)
        prio_summary, _ = self.engine.compute_priority(relevant_summary, rel_summary)

        self.assertGreater(prio_summary, prio_unrel)

    def test_case_c_different_token_counts(self):
        """
        CASE C: Multiple candidates with different token counts competing for budget.
        Lower token count breaks ties when priority scores are identical.
        """
        mem_small = Memory(
            id="mem_small",
            content="PostgreSQL database.",
            tier=MemoryTier.VERBATIM.value,
            status=MemoryStatus.ACTIVE.value,
            confidence=1.0,
            token_count=4,
        )
        mem_large = Memory(
            id="mem_large",
            content="PostgreSQL database.",
            tier=MemoryTier.VERBATIM.value,
            status=MemoryStatus.ACTIVE.value,
            confidence=1.0,
            token_count=20,
        )
        query = "PostgreSQL"
        prio_s, _ = self.engine.compute_priority(mem_small, self.engine.compute_relevance(query, mem_small.content))
        prio_l, _ = self.engine.compute_priority(mem_large, self.engine.compute_relevance(query, mem_large.content))

        self.assertEqual(prio_s, prio_l)
        # Downstream tie-breaking key: (-priority, token_count, id)
        sort_key_s = (-prio_s, mem_small.token_count, mem_small.id)
        sort_key_l = (-prio_l, mem_large.token_count, mem_large.id)
        self.assertLess(sort_key_s, sort_key_l)

    def test_case_d_constraint_and_decision_boosts(self):
        """
        CASE D: Constraint and decision boosts when relevance is equal.
        """
        mem_constraint = Memory(
            id="m_c",
            content="Database must strictly use PostgreSQL.",
            tier=MemoryTier.VERBATIM.value,
            status=MemoryStatus.ACTIVE.value,
            confidence=0.9,
            token_count=10,
        )
        mem_plain = Memory(
            id="m_p",
            content="Database runs on PostgreSQL.",
            tier=MemoryTier.VERBATIM.value,
            status=MemoryStatus.ACTIVE.value,
            confidence=0.9,
            token_count=10,
        )
        query = "database postgresql"
        rel_c = self.engine.compute_relevance(query, mem_constraint.content)
        rel_p = self.engine.compute_relevance(query, mem_plain.content)

        prio_c, reason_c = self.engine.compute_priority(mem_constraint, rel_c)
        prio_p, reason_p = self.engine.compute_priority(mem_plain, rel_p)

        self.assertGreater(prio_c, prio_p)
        self.assertEqual(reason_c, "explicit constraint")

    def test_case_e_equal_relevance_different_tiers(self):
        """
        CASE E: Equal relevance and confidence with different tiers.
        VERBATIM should receive a higher quaternary tier boost than SUMMARY.
        """
        mem_verb = Memory(
            id="m_v",
            content="The backend database is PostgreSQL.",
            tier=MemoryTier.VERBATIM.value,
            status=MemoryStatus.ACTIVE.value,
            confidence=0.9,
            token_count=6,
        )
        mem_summ = Memory(
            id="m_s",
            content="The backend database is PostgreSQL.",
            tier=MemoryTier.SUMMARY.value,
            status=MemoryStatus.ACTIVE.value,
            confidence=0.9,
            token_count=6,
        )
        query = "backend database"
        rel_v = self.engine.compute_relevance(query, mem_verb.content)
        rel_s = self.engine.compute_relevance(query, mem_summ.content)
        self.assertEqual(rel_v, rel_s)

        prio_v, _ = self.engine.compute_priority(mem_verb, rel_v)
        prio_s, _ = self.engine.compute_priority(mem_summ, rel_s)

        self.assertGreater(prio_v, prio_s)

    def test_case_f_equal_scores_deterministic_tie_breaking(self):
        """
        CASE F: Exactly equal scores, confidence, tier, and token count.
        Deterministic tie breaking by memory_id ASC.
        """
        mem_a = Memory(
            id="mem_001",
            content="Backend database is PostgreSQL.",
            tier=MemoryTier.VERBATIM.value,
            status=MemoryStatus.ACTIVE.value,
            confidence=1.0,
            token_count=5,
        )
        mem_b = Memory(
            id="mem_002",
            content="Backend database is PostgreSQL.",
            tier=MemoryTier.VERBATIM.value,
            status=MemoryStatus.ACTIVE.value,
            confidence=1.0,
            token_count=5,
        )
        query = "database"
        prio_a, _ = self.engine.compute_priority(mem_a, self.engine.compute_relevance(query, mem_a.content))
        prio_b, _ = self.engine.compute_priority(mem_b, self.engine.compute_relevance(query, mem_b.content))

        self.assertEqual(prio_a, prio_b)
        sort_key_a = (-prio_a, mem_a.token_count, mem_a.id)
        sort_key_b = (-prio_b, mem_b.token_count, mem_b.id)
        # mem_001 comes before mem_002 deterministically
        self.assertLess(sort_key_a, sort_key_b)


if __name__ == "__main__":
    unittest.main()

