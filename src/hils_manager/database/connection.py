"""Database connection management for HILS Manager.

Provides a singleton DatabaseConnection class that wraps SQLite connections
with WAL journaling, foreign key enforcement, and a generous busy timeout
suitable for a small-team (~15 people) desktop application.
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Optional


class DatabaseConnection:
    """Singleton SQLite connection manager.

    Usage::

        db = DatabaseConnection(Path("hils_manager.db"))
        with db as conn:
            conn.execute("SELECT ...")

        # Or manually:
        conn = db.get_connection()
        ...
        db.close()
    """

    _instance: Optional["DatabaseConnection"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, db_path: Optional[Path] = None) -> "DatabaseConnection":
        with cls._lock:
            if cls._instance is None:
                if db_path is None:
                    raise ValueError(
                        "db_path is required when creating the first DatabaseConnection instance"
                    )
                instance = super().__new__(cls)
                instance._db_path = db_path
                instance._connection: Optional[sqlite3.Connection] = None
                cls._instance = instance
            return cls._instance

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_connection(self) -> sqlite3.Connection:
        """Return the current connection, creating it if necessary.

        The connection is configured with:
        - WAL journal mode for better concurrent read performance
        - Foreign key enforcement enabled
        - 30-second busy timeout to handle brief lock contention
        - ``sqlite3.Row`` row factory for dict-like access
        """
        if self._connection is None:
            self._connection = sqlite3.connect(
                str(self._db_path),
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA journal_mode = WAL")
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.execute("PRAGMA busy_timeout = 30000")
        return self._connection

    def close(self) -> None:
        """Close the underlying SQLite connection if open."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.close()
                cls._instance = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> sqlite3.Connection:
        return self.get_connection()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        if self._connection is not None:
            if exc_type is None:
                self._connection.commit()
            else:
                self._connection.rollback()
