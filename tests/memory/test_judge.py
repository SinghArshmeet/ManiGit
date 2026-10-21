"""
Unit tests for MemoryJudge and MockModelAdapter.
"""

import unittest

from manigit.memory.judge import MemoryJudge
from manigit.models.mock import MockModelAdapter


class TestMemoryJudge(unittest.TestCase):
    """Test suite for semantic memory judge validation and fallback handling."""

    def test_structured_judgment_parsing(self):
        """Verify successful parsing of structured model response."""
        adapter = MockModelAdapter(
            default_judge_response={
                "tier": "SUMMARY",
                "confidence": 0.88,
                "reason": "Discussion synthesized across multiple turns.",
                "importance": "high",
                "needs_summary": True,
                "extracted_fact": "Team agreed to use React frontend.",
            }
        )
        judge = MemoryJudge(adapter)
        result = judge.judge("React discussion", ["msg_1", "msg_2"])

        self.assertEqual(result.tier, "SUMMARY")
        self.assertEqual(result.confidence, 0.88)
        self.assertEqual(result.reason, "Discussion synthesized across multiple turns.")
        self.assertEqual(result.importance, "high")
        self.assertTrue(result.needs_summary)
        self.assertEqual(result.extracted_fact, "Team agreed to use React frontend.")
        self.assertEqual(result.source_message_ids, ["msg_1", "msg_2"])

    def test_confidence_normalization_and_bounding(self):
        """Verify confidence values outside [0, 1] are clamped safely."""
        adapter = MockModelAdapter(
            default_judge_response={"tier": "VERBATIM", "confidence": 1.75}
        )
        judge = MemoryJudge(adapter)
        result = judge.judge("API key: abc", ["msg_1"])
        self.assertEqual(result.confidence, 1.0)

        adapter.default_judge_response = {"tier": "VERBATIM", "confidence": -0.5}
        result2 = judge.judge("API key: abc", ["msg_1"])
        self.assertEqual(result2.confidence, 0.0)

    def test_malformed_response_fallback(self):
        """Verify graceful fallback when model adapter returns invalid fields."""
        adapter = MockModelAdapter(default_judge_response={"tier": "INVALID_TIER", "confidence": "bad_num"})
        judge = MemoryJudge(adapter)
        result = judge.judge("Some random text", ["msg_1"])

        self.assertEqual(result.tier, "VERBATIM")  # Defaults conservatively to VERBATIM
        self.assertEqual(result.confidence, 0.65)
        self.assertEqual(result.importance, "medium")

    def test_offline_execution_records_call_history(self):
        """Verify mock adapter operates completely offline and records calls."""
        adapter = MockModelAdapter()
        judge = MemoryJudge(adapter)
        judge.judge("Testing offline call", ["msg_1"])

        self.assertEqual(len(adapter.call_history), 1)
        self.assertEqual(adapter.call_history[0]["method"], "judge_memory")
        self.assertEqual(adapter.call_history[0]["message_content"], "Testing offline call")


if __name__ == "__main__":
    unittest.main()
