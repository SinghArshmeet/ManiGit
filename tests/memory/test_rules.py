"""
Unit tests for the deterministic Rule Engine.
"""

import unittest

from manigit.memory.rules import RuleEngine


class TestRuleEngine(unittest.TestCase):
    """Test suite for deterministic pattern matching in RuleEngine."""

    def setUp(self):
        self.engine = RuleEngine()

    def test_detect_url(self):
        """Verify URL pattern matches as VERBATIM."""
        signal = self.engine.evaluate("Documentation available at https://api.manigit.io/v1/docs")
        self.assertEqual(signal.suggested_tier, "VERBATIM")
        self.assertIn("url", signal.matched_rules)
        self.assertGreaterEqual(signal.confidence, 0.85)

    def test_detect_file_path(self):
        """Verify file path matches as VERBATIM."""
        signal = self.engine.evaluate("Configuration stored in data/database/manigit.db")
        self.assertEqual(signal.suggested_tier, "VERBATIM")
        self.assertIn("file_path", signal.matched_rules)

    def test_detect_identifier_and_hash(self):
        """Verify UUIDs and entity IDs match as VERBATIM."""
        signal = self.engine.evaluate("User ID is usr_83921af7b01c and tx is tx_992100412")
        self.assertEqual(signal.suggested_tier, "VERBATIM")
        self.assertIn("identifier_or_hash", signal.matched_rules)
        self.assertTrue(signal.is_definitive)

    def test_detect_exact_numeric_quantity(self):
        """Verify exact numbers, currency, percentages match as VERBATIM."""
        signal = self.engine.evaluate("The project budget is capped at $5,000 with 99.9% uptime SLA.")
        self.assertEqual(signal.suggested_tier, "VERBATIM")
        self.assertIn("exact_numeric_quantity", signal.matched_rules)

    def test_detect_date_or_deadline(self):
        """Verify calendar dates match as VERBATIM."""
        signal = self.engine.evaluate("Final submission deadline is 2026-10-25.")
        self.assertEqual(signal.suggested_tier, "VERBATIM")
        self.assertIn("date_or_deadline", signal.matched_rules)

    def test_detect_code_and_stacktrace(self):
        """Verify code blocks and python functions match as definitive VERBATIM."""
        code_snippet = "```python\ndef compute_hash(data):\n    return sha256(data)\n```"
        signal = self.engine.evaluate(code_snippet)
        self.assertEqual(signal.suggested_tier, "VERBATIM")
        self.assertIn("code_or_stacktrace", signal.matched_rules)
        self.assertTrue(signal.is_definitive)

    def test_detect_errors_and_exceptions(self):
        """Verify error messages and stack traces match as VERBATIM."""
        err_text = "Encountered HTTP 500: DatabaseError connection timeout"
        signal = self.engine.evaluate(err_text)
        self.assertEqual(signal.suggested_tier, "VERBATIM")
        self.assertIn("error_or_exception", signal.matched_rules)
        self.assertTrue(signal.is_definitive)

    def test_detect_explicit_constraints(self):
        """Verify explicit constraint keywords match as definitive VERBATIM."""
        constraint = "You must never delete raw messages from the archive."
        signal = self.engine.evaluate(constraint)
        self.assertEqual(signal.suggested_tier, "VERBATIM")
        self.assertIn("explicit_constraint", signal.matched_rules)
        self.assertTrue(signal.is_definitive)

    def test_detect_explicit_decisions(self):
        """Verify decision statements match as definitive VERBATIM."""
        decision = "We've decided on SQLite for local zero-dependency storage."
        signal = self.engine.evaluate(decision)
        self.assertEqual(signal.suggested_tier, "VERBATIM")
        self.assertIn("explicit_decision", signal.matched_rules)
        self.assertTrue(signal.is_definitive)

    def test_detect_greetings(self):
        """Verify greetings match as ARCHIVED."""
        signal = self.engine.evaluate("Hello there!")
        self.assertEqual(signal.suggested_tier, "ARCHIVED")
        self.assertIn("greeting", signal.matched_rules)
        self.assertTrue(signal.is_definitive)

    def test_detect_acknowledgements(self):
        """Verify acknowledgements match as ARCHIVED."""
        signal = self.engine.evaluate("Sounds good, thanks!")
        self.assertEqual(signal.suggested_tier, "ARCHIVED")
        self.assertTrue(any(r in signal.matched_rules for r in ["acknowledgement", "greeting"]))
        self.assertTrue(signal.is_definitive)

    def test_detect_small_talk(self):
        """Verify small talk matches as ARCHIVED."""
        signal = self.engine.evaluate("How's it going?")
        self.assertEqual(signal.suggested_tier, "ARCHIVED")
        self.assertIn("small_talk", signal.matched_rules)
        self.assertTrue(signal.is_definitive)

    def test_detect_duplicates(self):
        """Verify statement identical to an active memory is marked as duplicate ARCHIVED."""
        existing = ["Backend database = SQLite", "Budget limit = $5000"]
        signal = self.engine.evaluate("Backend database = SQLite", existing_memories=existing)
        self.assertEqual(signal.suggested_tier, "ARCHIVED")
        self.assertIn("duplicate_statement", signal.matched_rules)
        self.assertTrue(signal.is_definitive)

    def test_ambiguous_text_passes_to_judge(self):
        """Verify conversational text without deterministic patterns is marked non-definitive."""
        ambiguous = "I was thinking about whether we might explore a different architecture next week."
        signal = self.engine.evaluate(ambiguous)
        self.assertIsNone(signal.suggested_tier)
        self.assertFalse(signal.is_definitive)
        self.assertEqual(signal.confidence, 0.50)


if __name__ == "__main__":
    unittest.main()
