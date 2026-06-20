"""Repository for application settings persistence."""

from __future__ import annotations

from typing import Optional

from .base_repository import BaseRepository


class SettingsRepository(BaseRepository):
    """CRUD operations for the ``app_settings`` key-value table.

    The table schema is::

        CREATE TABLE IF NOT EXISTS app_settings (
            key         TEXT PRIMARY KEY,
            value       TEXT NOT NULL,
            description TEXT
        );
    """

    # ------------------------------------------------------------------
    # Schema bootstrap
    # ------------------------------------------------------------------

    def ensure_table(self) -> None:
        """Create the ``app_settings`` table if it does not exist."""
        self._execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key         TEXT PRIMARY KEY,
                value       TEXT NOT NULL,
                description TEXT
            )
            """
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[str]:
        """Return the value for *key*, or ``None`` if not present."""
        row = self._fetchone(
            "SELECT value FROM app_settings WHERE key = ?", (key,)
        )
        return row["value"] if row else None

    def get_all(self) -> dict[str, str]:
        """Return every setting as a ``{key: value}`` mapping."""
        rows = self._fetchall("SELECT key, value FROM app_settings")
        return {row["key"]: row["value"] for row in rows}

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def set(self, key: str, value: str, description: str | None = None) -> None:
        """Insert or update a setting.

        If *description* is ``None`` and the key already exists the
        existing description is preserved.
        """
        if description is None:
            # Preserve any existing description on upsert.
            existing = self._fetchone(
                "SELECT description FROM app_settings WHERE key = ?", (key,)
            )
            description = existing["description"] if existing else None

        self._execute(
            """
            INSERT OR REPLACE INTO app_settings (key, value, description)
            VALUES (?, ?, ?)
            """,
            (key, value, description),
        )

    def delete(self, key: str) -> None:
        """Remove a setting by *key*."""
        self._execute("DELETE FROM app_settings WHERE key = ?", (key,))
