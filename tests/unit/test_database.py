"""
Unit tests for database initialization, schema creation, foreign key enforcement, and migrations.
"""

import os
import sqlite3
import tempfile
import unittest

from manigit.core.database import Database
from manigit.core.exceptions import DatabaseError
from manigit.core.schema import CURRENT_SCHEMA_VERSION


class TestDatabase(unittest.TestCase):
    """Test suite for SQLite Database layer."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_manigit.db")
        self.db = Database(self.db_path)

    def tearDown(self):
        self.db.close()
        self.temp_dir.cleanup()

    def test_database_initialization_and_schema_creation(self):
        """Verify schema creation and migration version recording."""
        self.db.initialize_schema()
        conn = self.db.connect()
        cursor = conn.cursor()

        # Check schema_version table
        cursor.execute("SELECT version FROM schema_version;")
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], CURRENT_SCHEMA_VERSION)

        # Check required tables exist
        required_tables = {
            "schema_version",
            "messages",
            "memories",
            "memory_sources",
            "commits",
            "commit_memories",
            "branches",
        }
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {r[0] for r in cursor.fetchall()}
        self.assertTrue(required_tables.issubset(tables))

    def test_foreign_key_enforcement(self):
        """Verify that foreign keys are strictly enforced by SQLite."""
        self.db.initialize_schema()
        conn = self.db.connect()

        # Attempt to insert a memory_sources record with non-existent memory and message
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO memory_sources (memory_id, message_id) VALUES ('fake_mem', 'fake_msg');"
            )

    def test_idempotent_schema_initialization(self):
        """Verify that running initialize_schema repeatedly causes no errors."""
        self.db.initialize_schema()
        self.db.initialize_schema()

        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM schema_version;")
        self.assertEqual(cursor.fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
