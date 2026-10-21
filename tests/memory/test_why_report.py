"""
Unit tests for WhyReport domain structure.
"""

import unittest

from manigit.memory.why import WhyReport


class TestWhyReport(unittest.TestCase):
    """Test suite for the WhyReport explainability structure."""

    def test_why_report_fields_and_serialization(self):
        """Verify WhyReport encapsulates complete explanation metadata."""
        report = WhyReport(
            decision="SUPERSEDE",
            tier="VERBATIM",
            confidence=0.96,
            reason="Backend database constraint updated from PostgreSQL to MongoDB.",
            source_message_ids=["msg_10", "msg_12"],
            matched_rules=["explicit_decision", "key_value_config"],
            predecessor_memory_id="mem_01",
            contradiction_info={
                "conflict_type": "EXPLICIT_REPLACEMENT",
                "historical_fact": "Database = PostgreSQL",
                "current_fact": "Database = MongoDB",
            },
            tokens_before=45,
            tokens_after=42,
        )

        data = report.to_dict()
        self.assertEqual(data["decision"], "SUPERSEDE")
        self.assertEqual(data["tier"], "VERBATIM")
        self.assertEqual(data["confidence"], 0.96)
        self.assertEqual(data["predecessor_memory_id"], "mem_01")
        self.assertEqual(data["source_message_ids"], ["msg_10", "msg_12"])
        self.assertEqual(data["matched_rules"], ["explicit_decision", "key_value_config"])
        self.assertIsNotNone(data["contradiction_info"])
        self.assertEqual(data["contradiction_info"]["conflict_type"], "EXPLICIT_REPLACEMENT")
        self.assertIn("timestamp", data)


if __name__ == "__main__":
    unittest.main()
