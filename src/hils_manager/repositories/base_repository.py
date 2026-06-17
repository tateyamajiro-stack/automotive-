"""Base repository providing common database helpers."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional, Sequence

from hils_manager.database.connection import DatabaseConnection


class BaseRepository:
    """Thin wrapper around a :class:`DatabaseConnection`.

    Subclasses inherit convenience helpers for executing queries and
    converting rows to domain objects.
    """

    def __init__(self, db: DatabaseConnection) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Connection access
    # ------------------------------------------------------------------

    @property
    def _conn(self) -> sqlite3.Connection:
        """Return the underlying SQLite connection."""
        return self._db.get_connection()

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def _execute(
        self, sql: str, params: Sequence[Any] = ()
    ) -> sqlite3.Cursor:
        """Execute *sql* with *params* and return the cursor."""
        return self._conn.execute(sql, params)

    def _fetchone(
        self, sql: str, params: Sequence[Any] = ()
    ) -> Optional[sqlite3.Row]:
        """Execute *sql* and return the first row, or ``None``."""
        return self._conn.execute(sql, params).fetchone()

    def _fetchall(
        self, sql: str, params: Sequence[Any] = ()
    ) -> list[sqlite3.Row]:
        """Execute *sql* and return all rows."""
        return self._conn.execute(sql, params).fetchall()

    # ------------------------------------------------------------------
    # Timestamp helper
    # ------------------------------------------------------------------

    @staticmethod
    def _now() -> str:
        """Return the current UTC time as an ISO-8601 string."""
        return datetime.now(timezone.utc).isoformat()
