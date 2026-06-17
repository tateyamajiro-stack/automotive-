"""Repository for estimate and time-entry persistence."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from typing import Optional

from hils_manager.constants import EstimateType
from hils_manager.models import Estimate, TimeEntry

from .base_repository import BaseRepository


class EstimateRepository(BaseRepository):
    """CRUD operations for ``estimates`` and ``time_entries`` tables."""

    # ------------------------------------------------------------------
    # Row mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_estimate(row: sqlite3.Row) -> Estimate:
        return Estimate(
            id=row["id"],
            project_id=row["project_id"],
            wbs_item_id=row["wbs_item_id"],
            estimate_type=EstimateType(row["estimate_type"]),
            man_hours=row["man_hours"] or 0.0,
            lead_time_days=row["lead_time_days"],
            estimator_id=row["estimator_id"],
            assumptions=row["assumptions"] or "",
            created_at=(
                datetime.fromisoformat(row["created_at"])
                if row["created_at"]
                else None
            ),
            wbs_title=(
                row["wbs_title"] if "wbs_title" in row.keys() else None
            ),
        )

    @staticmethod
    def _row_to_time_entry(row: sqlite3.Row) -> TimeEntry:
        return TimeEntry(
            id=row["id"],
            project_id=row["project_id"],
            wbs_item_id=row["wbs_item_id"],
            member_id=row["member_id"],
            work_date=(
                date.fromisoformat(row["work_date"])
                if row["work_date"]
                else None
            ),
            hours=row["hours"] or 0.0,
            description=row["description"] or "",
            created_at=(
                datetime.fromisoformat(row["created_at"])
                if row["created_at"]
                else None
            ),
            member_name=(
                row["member_name"] if "member_name" in row.keys() else None
            ),
            wbs_title=(
                row["wbs_title"] if "wbs_title" in row.keys() else None
            ),
        )

    # ------------------------------------------------------------------
    # Estimate queries
    # ------------------------------------------------------------------

    def get_by_project(self, project_id: int) -> list[Estimate]:
        """Return all estimates for a project, with WBS item titles."""
        sql = """
            SELECT e.*, w.title AS wbs_title
            FROM estimates e
            LEFT JOIN wbs_items w ON w.id = e.wbs_item_id
            WHERE e.project_id = ?
            ORDER BY e.wbs_item_id, e.estimate_type
        """
        return [self._row_to_estimate(r) for r in self._fetchall(sql, (project_id,))]

    def get_by_wbs_item(self, wbs_item_id: int) -> list[Estimate]:
        """Return all estimates attached to a specific WBS item."""
        sql = """
            SELECT e.*, w.title AS wbs_title
            FROM estimates e
            LEFT JOIN wbs_items w ON w.id = e.wbs_item_id
            WHERE e.wbs_item_id = ?
            ORDER BY e.estimate_type
        """
        return [self._row_to_estimate(r) for r in self._fetchall(sql, (wbs_item_id,))]

    def create(self, estimate: Estimate) -> int:
        now = self._now()
        cursor = self._execute(
            """
            INSERT INTO estimates
                (project_id, wbs_item_id, estimate_type, man_hours,
                 lead_time_days, estimator_id, assumptions, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                estimate.project_id,
                estimate.wbs_item_id,
                estimate.estimate_type.value,
                estimate.man_hours,
                estimate.lead_time_days,
                estimate.estimator_id,
                estimate.assumptions,
                now,
            ),
        )
        return cursor.lastrowid  # type: ignore[return-value]

    def update(self, estimate: Estimate) -> None:
        self._execute(
            """
            UPDATE estimates
            SET wbs_item_id    = ?,
                estimate_type  = ?,
                man_hours      = ?,
                lead_time_days = ?,
                estimator_id   = ?,
                assumptions    = ?
            WHERE id = ?
            """,
            (
                estimate.wbs_item_id,
                estimate.estimate_type.value,
                estimate.man_hours,
                estimate.lead_time_days,
                estimate.estimator_id,
                estimate.assumptions,
                estimate.id,
            ),
        )

    def delete(self, estimate_id: int) -> None:
        self._execute("DELETE FROM estimates WHERE id = ?", (estimate_id,))

    # ------------------------------------------------------------------
    # Time entry queries
    # ------------------------------------------------------------------

    def get_time_entries(
        self,
        project_id: int,
        member_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> list[TimeEntry]:
        """Return time entries, with optional filters for member and date range."""
        sql = """
            SELECT te.*, tm.name AS member_name, w.title AS wbs_title
            FROM time_entries te
            LEFT JOIN team_members tm ON tm.id = te.member_id
            LEFT JOIN wbs_items w ON w.id = te.wbs_item_id
            WHERE te.project_id = ?
        """
        params: list = [project_id]

        if member_id is not None:
            sql += " AND te.member_id = ?"
            params.append(member_id)
        if date_from is not None:
            sql += " AND te.work_date >= ?"
            params.append(date_from.isoformat())
        if date_to is not None:
            sql += " AND te.work_date <= ?"
            params.append(date_to.isoformat())

        sql += " ORDER BY te.work_date DESC, tm.name"
        return [self._row_to_time_entry(r) for r in self._fetchall(sql, params)]

    def add_time_entry(self, entry: TimeEntry) -> int:
        now = self._now()
        cursor = self._execute(
            """
            INSERT INTO time_entries
                (project_id, wbs_item_id, member_id, work_date,
                 hours, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.project_id,
                entry.wbs_item_id,
                entry.member_id,
                entry.work_date.isoformat() if entry.work_date else None,
                entry.hours,
                entry.description,
                now,
            ),
        )
        return cursor.lastrowid  # type: ignore[return-value]

    def delete_time_entry(self, entry_id: int) -> None:
        self._execute("DELETE FROM time_entries WHERE id = ?", (entry_id,))

    # ------------------------------------------------------------------
    # Aggregation helpers
    # ------------------------------------------------------------------

    def get_actual_hours_by_project(self, project_id: int) -> float:
        """Return the total hours logged for a project."""
        row = self._fetchone(
            "SELECT COALESCE(SUM(hours), 0.0) AS total FROM time_entries WHERE project_id = ?",
            (project_id,),
        )
        return float(row["total"]) if row else 0.0

    def get_actual_hours_by_wbs(self, wbs_item_id: int) -> float:
        """Return the total hours logged for a specific WBS item."""
        row = self._fetchone(
            "SELECT COALESCE(SUM(hours), 0.0) AS total FROM time_entries WHERE wbs_item_id = ?",
            (wbs_item_id,),
        )
        return float(row["total"]) if row else 0.0
