"""
Smoke tests for ManiGit project initialization and structure.
Compatible with both pytest and standard library unittest.
"""

import unittest
import manigit
from manigit.config import settings


class TestSmoke(unittest.TestCase):
    """Smoke test cases for package importability and configuration."""

    def test_package_import(self):
        """Verify that manigit imports cleanly and exposes version."""
        self.assertEqual(manigit.__version__, "0.1.0")

    def test_settings_initialization(self):
        """Verify that settings resolve default configurations correctly."""
        self.assertEqual(settings.model_provider, "mock")
        self.assertEqual(settings.default_token_budget, 4096)
        self.assertEqual(settings.verbatim_window_size, 10)
        self.assertTrue(str(settings.db_path).endswith("manigit.db"))


if __name__ == "__main__":
    unittest.main()

