"""
Unit tests for GeminiModelAdapter.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from manigit.models.gemini import GeminiModelAdapter


class TestGeminiModelAdapter(unittest.TestCase):
    """Test suite for optional GeminiModelAdapter initialization, validation, and error scrubbing."""

    def test_missing_api_key_raises_informative_value_error(self):
        """Verify that attempting to invoke without API key raises clean ValueError."""
        # Ensure environment variable is not set
        with patch.dict(os.environ, {}, clear=True):
            adapter = GeminiModelAdapter(api_key=None)
            with self.assertRaises(ValueError) as ctx:
                adapter.generate("Hello")

            self.assertIn("GEMINI_API_KEY", str(ctx.exception))

    def test_token_counting_fallback(self):
        """Verify count_tokens uses estimate_tokens correctly."""
        adapter = GeminiModelAdapter(api_key="mock_key")
        count = adapter.count_tokens("This is a four-word test sentence.")
        self.assertGreater(count, 0)

    @patch("urllib.request.urlopen")
    def test_successful_generate_with_mocked_http(self, mock_urlopen):
        """Verify successful parsing of Gemini API response format."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"candidates": [{"content": {"parts": [{"text": "Gemini response text"}]}}]}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        adapter = GeminiModelAdapter(api_key="mock_test_key")
        result = adapter.generate("Test prompt")
        self.assertEqual(result, "Gemini response text")

    @patch("urllib.request.urlopen")
    def test_judge_memory_parsing(self, mock_urlopen):
        """Verify structured JSON judgment parsing from Gemini response."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"candidates": [{"content": {"parts": [{"text": "```json\\n{\\"tier\\": \\"VERBATIM\\", \\"confidence\\": 0.95, \\"reason\\": \\"Database specification\\", \\"importance\\": \\"high\\", \\"needs_summary\\": false, \\"extracted_fact\\": \\"PostgreSQL\\"}\\n```"}]}}]}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        adapter = GeminiModelAdapter(api_key="mock_test_key")
        judgment = adapter.judge_memory("We use PostgreSQL")
        self.assertEqual(judgment["tier"], "VERBATIM")
        self.assertEqual(judgment["confidence"], 0.95)
        self.assertEqual(judgment["extracted_fact"], "PostgreSQL")


if __name__ == "__main__":
    unittest.main()
