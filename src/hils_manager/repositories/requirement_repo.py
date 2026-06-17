"""Repository for requirement persistence."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from typing import Optional

from hils_manager.constants import RequirementPriority, RequirementStatus
from hils_manager.models import Requirement

from .base_repository import BaseRepository


class RequirementRepository(BaseRepository):
    """CRUD operations for the ``requirements`` table."""

    # ------------------------------------------------------------------
    # Row mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_requirement(row: sqlite3.Row) -> Requirement:
        return Requirement(
            id=row["id"],
            project_id=row["project_id"],
            req_number=row["req_number"],
            title=row["title"],
            description=row["description"] or "",
            priority=RequirementPriority(row["priority"]),
            status=RequirementStatus(row["status"]),
            requested_by=row["requested_by"] or "",
            requested_date=(
                date.fromisoformat(row["requested_date"])
                if row["requested_date"]
                else None
            ),
            target_version=row["target_version"] or "",
            created_at=(
                datetime.fromisoformat(row["created_at"])
                if row["created_at"]
                else None
            ),
            updated_at=(
                datetime.fromisoformat(row["updated_at"])
                if row["updated_at"]
                else None
            ),
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_by_project(self, project_id: int) -> list[Requirement]:
        sql = (
            "SELECT * FROM requirements WHERE project_id = ? "
            "ORDER BY req_number"
        )
        return [
            self._row_to_requirement(r)
            for r in self._fetchall(sql, (project_id,))
        ]

    def get_by_id(self, req_id: int) -> Optional[Requirement]:
        row = self._fetchone("SELECT * FROM requirements WHERE id = ?", (req_id,))
        return self._row_to_requirement(row) if row else None

    def create(self, req: Requirement) -> int:
        now = self._now()
        cursor = self._execute(
            """
            INSERT INTO requirements
                (project_id, req_number, title, description, priority, status,
                 requested_by, requested_date, target_version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                req.project_id,
                req.req_number,
                req.title,
                req.description,
                req.priority.value,
                req.status.value,
                req.requested_by,
                req.requested_date.isoformat() if req.requested_date else None,
                req.target_version,
                now,
                now,
            ),
        )
        return cursor.lastrowid  # type: ignore[return-value]

    def update(self, req: Requirement) -> None:
        now = self._now()
        self._execute(
            """
            UPDATE requirements
            SET req_number     = ?,
                title          = ?,
                description    = ?,
                priority       = ?,
                status         = ?,
                requested_by   = ?,
                requested_date = ?,
                target_version = ?,
                updated_at     = ?
            WHERE id = ?
            """,
            (
                req.req_number,
                req.title,
                req.description,
                req.priority.value,
                req.status.value,
                req.requested_by,
                req.requested_date.isoformat() if req.requested_date else None,
                req.target_version,
                now,
                req.id,
            ),
        )

    def delete(self, req_id: int) -> None:
        self._execute("DELETE FROM requirements WHERE id = ?", (req_id,))

    def get_next_req_number(self, project_id: int) -> str:
        """Return the next requirement number for the project (e.g. ``REQ-001``)."""
        row = self._fetchone(
            """
            SELECT req_number FROM requirements
            WHERE project_id = ?
            ORDER BY req_number DESC
            LIMIT 1
            """,
            (project_id,),
        )
        if row and row["req_number"]:
            # Parse "REQ-NNN" and increment
            try:
                num = int(row["req_number"].split("-")[1])
                return f"REQ-{num + 1:03d}"
            except (IndexError, ValueError):
                pass
        return "REQ-001"
