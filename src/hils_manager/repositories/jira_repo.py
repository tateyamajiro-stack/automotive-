"""Repository for Jira sync mapping and log persistence."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional

from hils_manager.models import JiraSyncLog, JiraSyncMapping

from .base_repository import BaseRepository


class JiraSyncRepository(BaseRepository):
    """CRUD operations for ``jira_sync_mappings`` and ``jira_sync_log`` tables."""

    # ------------------------------------------------------------------
    # Row mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_mapping(row: sqlite3.Row) -> JiraSyncMapping:
        return JiraSyncMapping(
            id=row["id"],
            project_id=row["project_id"],
            local_entity=row["local_entity"],
            local_id=row["local_id"],
            jira_issue_key=row["jira_issue_key"],
            jira_issue_id=row["jira_issue_id"] or "",
            last_sync_at=(
                datetime.fromisoformat(row["last_sync_at"])
                if row["last_sync_at"]
                else None
            ),
            sync_direction=row["sync_direction"] or "",
            sync_status=row["sync_status"] or "",
        )

    @staticmethod
    def _row_to_log(row: sqlite3.Row) -> JiraSyncLog:
        return JiraSyncLog(
            id=row["id"],
            mapping_id=row["mapping_id"],
            sync_type=row["sync_type"],
            status=row["status"],
            details=row["details"] or "",
            synced_at=(
                datetime.fromisoformat(row["synced_at"])
                if row["synced_at"]
                else None
            ),
        )

    # ------------------------------------------------------------------
    # Mapping queries
    # ------------------------------------------------------------------

    def get_mapping(
        self, local_entity: str, local_id: int
    ) -> Optional[JiraSyncMapping]:
        """Return the mapping for a local entity, or ``None``."""
        row = self._fetchone(
            "SELECT * FROM jira_sync_mappings WHERE local_entity = ? AND local_id = ?",
            (local_entity, local_id),
        )
        return self._row_to_mapping(row) if row else None

    def get_by_project(self, project_id: int) -> list[JiraSyncMapping]:
        """Return all mappings for a project."""
        rows = self._fetchall(
            "SELECT * FROM jira_sync_mappings WHERE project_id = ? ORDER BY id",
            (project_id,),
        )
        return [self._row_to_mapping(r) for r in rows]

    def get_by_jira_key(self, jira_issue_key: str) -> Optional[JiraSyncMapping]:
        """Return the mapping for a Jira issue key, or ``None``."""
        row = self._fetchone(
            "SELECT * FROM jira_sync_mappings WHERE jira_issue_key = ?",
            (jira_issue_key,),
        )
        return self._row_to_mapping(row) if row else None

    def upsert_mapping(self, mapping: JiraSyncMapping) -> int:
        """Insert or replace a mapping and return its id."""
        now = self._now()
        cursor = self._execute(
            """
            INSERT OR REPLACE INTO jira_sync_mappings
                (project_id, local_entity, local_id, jira_issue_key,
                 jira_issue_id, last_sync_at, sync_direction, sync_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mapping.project_id,
                mapping.local_entity,
                mapping.local_id,
                mapping.jira_issue_key,
                mapping.jira_issue_id,
                now,
                mapping.sync_direction or "bidirectional",
                mapping.sync_status or "synced",
            ),
        )
        return cursor.lastrowid  # type: ignore[return-value]

    def update_sync_status(self, mapping_id: int, status: str) -> None:
        """Update the sync status of a mapping."""
        self._execute(
            "UPDATE jira_sync_mappings SET sync_status = ? WHERE id = ?",
            (status, mapping_id),
        )

    def delete_mapping(self, mapping_id: int) -> None:
        """Delete a mapping by id."""
        self._execute(
            "DELETE FROM jira_sync_mappings WHERE id = ?",
            (mapping_id,),
        )

    # ------------------------------------------------------------------
    # Sync log
    # ------------------------------------------------------------------

    def add_log(
        self, mapping_id: int, sync_type: str, status: str, details: str
    ) -> int:
        """Record a sync log entry and return its id."""
        cursor = self._execute(
            """
            INSERT INTO jira_sync_log (mapping_id, sync_type, status, details, synced_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (mapping_id, sync_type, status, details, self._now()),
        )
        return cursor.lastrowid  # type: ignore[return-value]

    def get_logs(self, mapping_id: int) -> list[JiraSyncLog]:
        """Return all log entries for a mapping, newest first."""
        rows = self._fetchall(
            "SELECT * FROM jira_sync_log WHERE mapping_id = ? ORDER BY synced_at DESC",
            (mapping_id,),
        )
        return [self._row_to_log(r) for r in rows]
