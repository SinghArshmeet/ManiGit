"""
Unit tests for the hybrid MemoryClassifier.
"""

import unittest

from manigit.memory.classifier import MemoryClassifier
from manigit.memory.judge import MemoryJudge
from manigit.memory.rules import RuleEngine
from manigit.models.mock import MockModelAdapter


class TestMemoryClassifier(unittest.TestCase):
    """Test suite for hybrid memory classification logic and confidence handling."""

    def setUp(self):
        self.rule_engine = RuleEngine()
        self.adapter = MockModelAdapter()
        self.judge = MemoryJudge(self.adapter)
        self.classifier = MemoryClassifier(self.rule_engine, self.judge)

    def test_clear_tier1_fast_path_bypasses_llm(self):
        """Verify explicit constraint matches Tier 1 without calling LLM."""
        text = "You must always retain raw messages in SQLite."
        result = self.classifier.classify(text, ["msg_1"])

        self.assertEqual(result.tier, "VERBATIM")
        self.assertEqual(result.decision, "KEEP_VERBATIM")
        self.assertFalse(result.used_llm_judge)
        self.assertIn("explicit_constraint", result.matched_rules)
        self.assertEqual(len(self.adapter.call_history), 0)

    def test_clear_tier3_fast_path_bypasses_llm(self):
        """Verify greeting matches Tier 3 without calling LLM."""
        text = "Hello!"
        result = self.classifier.classify(text, ["msg_1"])

        self.assertEqual(result.tier, "ARCHIVED")
        self.assertEqual(result.decision, "ARCHIVE")
        self.assertFalse(result.used_llm_judge)
        self.assertIn("greeting", result.matched_rules)
        self.assertEqual(len(self.adapter.call_history), 0)

    def test_ambiguous_case_invokes_llm_judge(self):
        """Verify ambiguous text invokes the semantic LLM judge."""
        text = "We spent considerable time discussing performance bottlenecks in the event loop."
        self.adapter.default_judge_response = {
            "tier": "SUMMARY",
            "confidence": 0.85,
            "reason": "Identified complex technical discussion suitable for Tier 2 summary.",
            "importance": "medium",
            "needs_summary": True,
        }

        result = self.classifier.classify(text, ["msg_1"])
        self.assertEqual(result.tier, "SUMMARY")
        self.assertEqual(result.decision, "SUMMARIZE")
        self.assertTrue(result.used_llm_judge)
        self.assertEqual(len(self.adapter.call_history), 1)

    def test_low_confidence_archive_escalated_to_verbatim(self):
        """
        Verify conservative preservation:
        If LLM proposes ARCHIVE with low confidence (<0.75), escalate to VERBATIM.
        """
        text = "Not sure if this matters, but customer mentioned they might scale to 10k users."
        self.adapter.default_judge_response = {
            "tier": "ARCHIVED",
            "confidence": 0.55,  # Low confidence (< 0.75)
            "reason": "Sounds tentative, might not be important.",
            "importance": "low",
        }

        result = self.classifier.classify(text, ["msg_1"])
        # Should be preserved conservatively
        self.assertEqual(result.tier, "VERBATIM")
        self.assertEqual(result.decision, "KEEP_VERBATIM")
        self.assertIn("escalated to VERBATIM", result.reason)

    def test_rule_verbatim_signal_overrides_llm_archive(self):
        """
        Verify that if deterministic rules find verbatim indicators (like an ID),
        it overrides an LLM recommendation to archive.
        """
        text = "Check this ref: tx_884910321a"
        self.adapter.default_judge_response = {
            "tier": "ARCHIVED",
            "confidence": 0.90,
            "reason": "Brief non-conversational fragment.",
        }

        result = self.classifier.classify(text, ["msg_1"])
        self.assertEqual(result.tier, "VERBATIM")
        self.assertEqual(result.decision, "KEEP_VERBATIM")


if __name__ == "__main__":
    unittest.main()
