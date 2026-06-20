"""Repository for report persistence."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional

from hils_manager.models import Report

from .base_repository import BaseRepository


class ReportRepository(BaseRepository):
    """CRUD operations for the ``reports`` table."""

    # ------------------------------------------------------------------
    # Row mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_report(row: sqlite3.Row) -> Report:
        return Report(
            id=row["id"],
            project_id=row["project_id"],
            report_type=row["report_type"],
            format=row["format"],
            title=row["title"],
            generated_by=row["generated_by"],
            file_path=row["file_path"] or "",
            confluence_url=row["confluence_url"] or "",
            parameters_json=row["parameters_json"] or "",
            generated_at=(
                datetime.fromisoformat(row["generated_at"])
                if row["generated_at"]
                else None
            ),
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def create(self, report: Report) -> int:
        """Persist a new report and return its id."""
        cursor = self._execute(
            """
            INSERT INTO reports
                (project_id, report_type, format, title, generated_by,
                 file_path, confluence_url, parameters_json, generated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report.project_id,
                report.report_type,
                report.format,
                report.title,
                report.generated_by,
                report.file_path,
                report.confluence_url,
                report.parameters_json,
                self._now(),
            ),
        )
        return cursor.lastrowid  # type: ignore[return-value]

    def get_by_id(self, report_id: int) -> Optional[Report]:
        """Return a single report by id, or ``None``."""
        row = self._fetchone(
            "SELECT * FROM reports WHERE id = ?",
            (report_id,),
        )
        return self._row_to_report(row) if row else None

    def get_by_project(self, project_id: int) -> list[Report]:
        """Return all reports for a project, newest first."""
        rows = self._fetchall(
            "SELECT * FROM reports WHERE project_id = ? ORDER BY generated_at DESC",
            (project_id,),
        )
        return [self._row_to_report(r) for r in rows]

    def get_recent(self, limit: int = 20) -> list[Report]:
        """Return the most recent reports across all projects."""
        rows = self._fetchall(
            "SELECT * FROM reports ORDER BY generated_at DESC LIMIT ?",
            (limit,),
        )
        return [self._row_to_report(r) for r in rows]

    def delete(self, report_id: int) -> None:
        """Delete a report by id."""
        self._execute("DELETE FROM reports WHERE id = ?", (report_id,))
