"""Repository for WBS item persistence."""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from typing import Optional

from hils_manager.constants import WBSStatus
from hils_manager.models import WBSItem

from .base_repository import BaseRepository


class WBSRepository(BaseRepository):
    """CRUD operations for the ``wbs_items`` table."""

    # ------------------------------------------------------------------
    # Row mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_wbs(row: sqlite3.Row) -> WBSItem:
        dep_raw = row["dependency_ids"]
        dependency_ids = json.loads(dep_raw) if dep_raw else []

        return WBSItem(
            id=row["id"],
            project_id=row["project_id"],
            parent_id=row["parent_id"],
            wbs_code=row["wbs_code"],
            title=row["title"],
            description=row["description"] or "",
            assigned_to=row["assigned_to"],
            status=WBSStatus(row["status"]),
            planned_start=(
                date.fromisoformat(row["planned_start"])
                if row["planned_start"]
                else None
            ),
            planned_end=(
                date.fromisoformat(row["planned_end"])
                if row["planned_end"]
                else None
            ),
            actual_start=(
                date.fromisoformat(row["actual_start"])
                if row["actual_start"]
                else None
            ),
            actual_end=(
                date.fromisoformat(row["actual_end"])
                if row["actual_end"]
                else None
            ),
            planned_hours=row["planned_hours"],
            dependency_ids=dependency_ids,
            sort_order=row["sort_order"],
            jira_issue_key=row["jira_issue_key"],
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
            assigned_to_name=(
                row["assigned_to_name"]
                if "assigned_to_name" in row.keys()
                else None
            ),
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_by_project(self, project_id: int) -> list[WBSItem]:
        """Return a flat list of WBS items for a project (with assignee names)."""
        sql = """
            SELECT w.*, tm.name AS assigned_to_name
            FROM wbs_items w
            LEFT JOIN team_members tm ON tm.id = w.assigned_to
            WHERE w.project_id = ?
            ORDER BY w.sort_order, w.wbs_code
        """
        return [self._row_to_wbs(r) for r in self._fetchall(sql, (project_id,))]

    def get_tree(self, project_id: int) -> list[WBSItem]:
        """Return WBS items organized as a tree (top-level items with nested children)."""
        flat = self.get_by_project(project_id)

        by_id: dict[int, WBSItem] = {}
        for item in flat:
            item.children = []
            if item.id is not None:
                by_id[item.id] = item

        roots: list[WBSItem] = []
        for item in flat:
            if item.parent_id is not None and item.parent_id in by_id:
                by_id[item.parent_id].children.append(item)
            else:
                roots.append(item)

        return roots

    def get_by_id(self, wbs_id: int) -> Optional[WBSItem]:
        sql = """
            SELECT w.*, tm.name AS assigned_to_name
            FROM wbs_items w
            LEFT JOIN team_members tm ON tm.id = w.assigned_to
            WHERE w.id = ?
        """
        row = self._fetchone(sql, (wbs_id,))
        return self._row_to_wbs(row) if row else None

    def create(self, item: WBSItem) -> int:
        now = self._now()
        cursor = self._execute(
            """
            INSERT INTO wbs_items
                (project_id, parent_id, wbs_code, title, description,
                 assigned_to, status, planned_start, planned_end,
                 actual_start, actual_end, planned_hours, dependency_ids,
                 sort_order, jira_issue_key, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.project_id,
                item.parent_id,
                item.wbs_code,
                item.title,
                item.description,
                item.assigned_to,
                item.status.value,
                item.planned_start.isoformat() if item.planned_start else None,
                item.planned_end.isoformat() if item.planned_end else None,
                item.actual_start.isoformat() if item.actual_start else None,
                item.actual_end.isoformat() if item.actual_end else None,
                item.planned_hours,
                json.dumps(item.dependency_ids),
                item.sort_order,
                item.jira_issue_key,
                now,
                now,
            ),
        )
        return cursor.lastrowid  # type: ignore[return-value]

    def update(self, item: WBSItem) -> None:
        now = self._now()
        self._execute(
            """
            UPDATE wbs_items
            SET parent_id      = ?,
                wbs_code       = ?,
                title          = ?,
                description    = ?,
                assigned_to    = ?,
                status         = ?,
                planned_start  = ?,
                planned_end    = ?,
                actual_start   = ?,
                actual_end     = ?,
                planned_hours  = ?,
                dependency_ids = ?,
                sort_order     = ?,
                jira_issue_key = ?,
                updated_at     = ?
            WHERE id = ?
            """,
            (
                item.parent_id,
                item.wbs_code,
                item.title,
                item.description,
                item.assigned_to,
                item.status.value,
                item.planned_start.isoformat() if item.planned_start else None,
                item.planned_end.isoformat() if item.planned_end else None,
                item.actual_start.isoformat() if item.actual_start else None,
                item.actual_end.isoformat() if item.actual_end else None,
                item.planned_hours,
                json.dumps(item.dependency_ids),
                item.sort_order,
                item.jira_issue_key,
                now,
                item.id,
            ),
        )

    def delete(self, wbs_id: int) -> None:
        self._execute("DELETE FROM wbs_items WHERE id = ?", (wbs_id,))

    def get_next_wbs_code(
        self, project_id: int, parent_id: Optional[int] = None
    ) -> str:
        """Generate the next WBS code under a given parent.

        - Top-level (no parent): ``"1"``, ``"2"``, ...
        - Under parent ``"1"``: ``"1.1"``, ``"1.2"``, ...
        - Under parent ``"1.1"``: ``"1.1.1"``, ``"1.1.2"``, ...
        """
        if parent_id is None:
            # Count top-level items
            row = self._fetchone(
                """
                SELECT COUNT(*) AS cnt FROM wbs_items
                WHERE project_id = ? AND parent_id IS NULL
                """,
                (project_id,),
            )
            count = row["cnt"] if row else 0
            return str(count + 1)

        # Get the parent's code to build upon
        parent_row = self._fetchone(
            "SELECT wbs_code FROM wbs_items WHERE id = ?", (parent_id,)
        )
        parent_code = parent_row["wbs_code"] if parent_row else ""

        # Count existing children of this parent
        row = self._fetchone(
            """
            SELECT COUNT(*) AS cnt FROM wbs_items
            WHERE project_id = ? AND parent_id = ?
            """,
            (project_id, parent_id),
        )
        count = row["cnt"] if row else 0

        return f"{parent_code}.{count + 1}"
