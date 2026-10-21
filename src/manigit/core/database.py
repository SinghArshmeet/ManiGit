"""
Database connection, transaction management, and migration execution for SQLite.
"""

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Generator, Optional, Union
import os

from manigit.core.exceptions import DatabaseError
from manigit.core.schema import CURRENT_SCHEMA_VERSION, SCHEMA_V1_SQL


class Database:
    """
    SQLite database wrapper providing transaction safety, foreign key enforcement,
    and schema migration execution.
    """

    def __init__(self, db_path: Union[str, Path] = "data/database/manigit.db"):
        self.db_path = str(db_path)
        self._is_memory = self.db_path in (":memory:", "")
        if not self._is_memory:
            # Ensure parent directories exist
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._connection: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Create or return an open SQLite connection with required pragmas."""
        if self._connection is None:
            try:
                self._connection = sqlite3.connect(
                    self.db_path,
                    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                    check_same_thread=False,
                )
                self._connection.row_factory = sqlite3.Row
                # Mandatory: enforce foreign keys
                self._connection.execute("PRAGMA foreign_keys = ON;")
                if not self._is_memory:
                    self._connection.execute("PRAGMA journal_mode = WAL;")
            except sqlite3.Error as e:
                raise DatabaseError(f"Failed to connect to database at {self.db_path}: {e}") from e
        return self._connection

    def close(self) -> None:
        """Close connection if open."""
        if self._connection is not None:
            try:
                self._connection.close()
            except sqlite3.Error:
                pass
            finally:
                self._connection = None

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Transactional context manager.
        Automatically commits on successful exit or rolls back on failure.
        """
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(f"Transaction failed and was rolled back: {e}") from e

    def initialize_schema(self) -> None:
        """Apply schema DDL and record migration version if not already applied."""
        conn = self.connect()
        try:
            # Check current schema version
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version';"
            )
            table_exists = cursor.fetchone() is not None

            current_version = 0
            if table_exists:
                cursor.execute("SELECT MAX(version) FROM schema_version;")
                row = cursor.fetchone()
                if row and row[0] is not None:
                    current_version = row[0]

            if current_version < CURRENT_SCHEMA_VERSION:
                # Apply migration
                conn.executescript(SCHEMA_V1_SQL)
                now_iso = datetime.now(timezone.utc).isoformat()
                conn.execute(
                    "INSERT INTO schema_version (version, applied_at) VALUES (?, ?);",
                    (CURRENT_SCHEMA_VERSION, now_iso),
                )
                conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(f"Failed to initialize database schema: {e}") from e
