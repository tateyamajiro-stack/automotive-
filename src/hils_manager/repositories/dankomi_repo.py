"""Repository for dankomi (meeting record) persistence."""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from typing import Optional

from hils_manager.models import DankomiRecord

from .base_repository import BaseRepository


class DankomiRepository(BaseRepository):
    """CRUD operations for the ``dankomi_records`` table."""

    # ------------------------------------------------------------------
    # Row mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_dankomi(row: sqlite3.Row) -> DankomiRecord:
        attendees_raw = row["attendees"]
        attendees = json.loads(attendees_raw) if attendees_raw else []

        action_items_raw = row["action_items"]
        action_items = json.loads(action_items_raw) if action_items_raw else []

        return DankomiRecord(
            id=row["id"],
            project_id=row["project_id"],
            meeting_date=(
                date.fromisoformat(row["meeting_date"])
                if row["meeting_date"]
                else None
            ),
            attendees=attendees,
            goal_state=row["goal_state"] or "",
            goal_deliverables=row["goal_deliverables"] or "",
            agenda=row["agenda"] or "",
            decisions=row["decisions"] or "",
            action_items=action_items,
            notes=row["notes"] or "",
            created_at=(
                datetime.fromisoformat(row["created_at"])
                if row["created_at"]
                else None
            ),
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_by_project(self, project_id: int) -> list[DankomiRecord]:
        """Return all dankomi records for a project, newest first."""
        sql = (
            "SELECT * FROM dankomi_records WHERE project_id = ? "
            "ORDER BY meeting_date DESC"
        )
        return [
            self._row_to_dankomi(r)
            for r in self._fetchall(sql, (project_id,))
        ]

    def get_by_id(self, dankomi_id: int) -> Optional[DankomiRecord]:
        row = self._fetchone(
            "SELECT * FROM dankomi_records WHERE id = ?", (dankomi_id,)
        )
        return self._row_to_dankomi(row) if row else None

    def create(self, record: DankomiRecord) -> int:
        now = self._now()
        cursor = self._execute(
            """
            INSERT INTO dankomi_records
                (project_id, meeting_date, attendees, goal_state,
                 goal_deliverables, agenda, decisions, action_items,
                 notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.project_id,
                record.meeting_date.isoformat() if record.meeting_date else None,
                json.dumps(record.attendees),
                record.goal_state,
                record.goal_deliverables,
                record.agenda,
                record.decisions,
                json.dumps(record.action_items),
                record.notes,
                now,
            ),
        )
        return cursor.lastrowid  # type: ignore[return-value]

    def update(self, record: DankomiRecord) -> None:
        self._execute(
            """
            UPDATE dankomi_records
            SET meeting_date      = ?,
                attendees         = ?,
                goal_state        = ?,
                goal_deliverables = ?,
                agenda            = ?,
                decisions         = ?,
                action_items      = ?,
                notes             = ?
            WHERE id = ?
            """,
            (
                record.meeting_date.isoformat() if record.meeting_date else None,
                json.dumps(record.attendees),
                record.goal_state,
                record.goal_deliverables,
                record.agenda,
                record.decisions,
                json.dumps(record.action_items),
                record.notes,
                record.id,
            ),
        )

    def delete(self, dankomi_id: int) -> None:
        self._execute(
            "DELETE FROM dankomi_records WHERE id = ?", (dankomi_id,)
        )
