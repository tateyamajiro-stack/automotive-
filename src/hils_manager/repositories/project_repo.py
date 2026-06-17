"""Repository for project and project-assignment persistence."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from typing import Optional

from hils_manager.constants import ProjectRole, ProjectStatus
from hils_manager.models import Project, ProjectAssignment

from .base_repository import BaseRepository


class ProjectRepository(BaseRepository):
    """CRUD operations for the ``projects`` and ``project_assignments`` tables."""

    # ------------------------------------------------------------------
    # Row mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_project(row: sqlite3.Row) -> Project:
        return Project(
            id=row["id"],
            project_code=row["project_code"],
            name=row["name"],
            description=row["description"] or "",
            status=ProjectStatus(row["status"]),
            start_date=(
                date.fromisoformat(row["start_date"])
                if row["start_date"]
                else None
            ),
            end_date=(
                date.fromisoformat(row["end_date"])
                if row["end_date"]
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
            jira_project_key=row["jira_project_key"] or "",
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

    @staticmethod
    def _row_to_assignment(row: sqlite3.Row) -> ProjectAssignment:
        return ProjectAssignment(
            id=row["id"],
            project_id=row["project_id"],
            member_id=row["member_id"],
            role=ProjectRole(row["role"]),
            allocation_pct=row["allocation_pct"],
            start_date=(
                date.fromisoformat(row["start_date"])
                if row["start_date"]
                else None
            ),
            end_date=(
                date.fromisoformat(row["end_date"])
                if row["end_date"]
                else None
            ),
            member_name=row["member_name"] if "member_name" in row.keys() else None,
        )

    # ------------------------------------------------------------------
    # Project queries
    # ------------------------------------------------------------------

    def get_all(self, status_filter: Optional[ProjectStatus] = None) -> list[Project]:
        """Return all projects, optionally filtered by status."""
        if status_filter is not None:
            sql = "SELECT * FROM projects WHERE status = ? ORDER BY project_code"
            rows = self._fetchall(sql, (status_filter.value,))
        else:
            sql = "SELECT * FROM projects ORDER BY project_code"
            rows = self._fetchall(sql)
        return [self._row_to_project(r) for r in rows]

    def get_by_id(self, project_id: int) -> Optional[Project]:
        row = self._fetchone("SELECT * FROM projects WHERE id = ?", (project_id,))
        return self._row_to_project(row) if row else None

    def create(self, project: Project) -> int:
        now = self._now()
        cursor = self._execute(
            """
            INSERT INTO projects
                (project_code, name, description, status, start_date, end_date,
                 actual_start, actual_end, jira_project_key, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project.project_code,
                project.name,
                project.description,
                project.status.value,
                project.start_date.isoformat() if project.start_date else None,
                project.end_date.isoformat() if project.end_date else None,
                project.actual_start.isoformat() if project.actual_start else None,
                project.actual_end.isoformat() if project.actual_end else None,
                project.jira_project_key,
                now,
                now,
            ),
        )
        return cursor.lastrowid  # type: ignore[return-value]

    def update(self, project: Project) -> None:
        now = self._now()
        self._execute(
            """
            UPDATE projects
            SET project_code     = ?,
                name             = ?,
                description      = ?,
                status           = ?,
                start_date       = ?,
                end_date         = ?,
                actual_start     = ?,
                actual_end       = ?,
                jira_project_key = ?,
                updated_at       = ?
            WHERE id = ?
            """,
            (
                project.project_code,
                project.name,
                project.description,
                project.status.value,
                project.start_date.isoformat() if project.start_date else None,
                project.end_date.isoformat() if project.end_date else None,
                project.actual_start.isoformat() if project.actual_start else None,
                project.actual_end.isoformat() if project.actual_end else None,
                project.jira_project_key,
                now,
                project.id,
            ),
        )

    def delete(self, project_id: int) -> None:
        """Delete a project by primary key."""
        self._execute("DELETE FROM projects WHERE id = ?", (project_id,))

    # ------------------------------------------------------------------
    # Assignment queries
    # ------------------------------------------------------------------

    def get_assignments(self, project_id: int) -> list[ProjectAssignment]:
        """Return all assignments for a project, with member names."""
        sql = """
            SELECT pa.*, tm.name AS member_name
            FROM project_assignments pa
            JOIN team_members tm ON tm.id = pa.member_id
            WHERE pa.project_id = ?
            ORDER BY pa.role, tm.name
        """
        return [self._row_to_assignment(r) for r in self._fetchall(sql, (project_id,))]

    def add_assignment(self, assignment: ProjectAssignment) -> int:
        cursor = self._execute(
            """
            INSERT INTO project_assignments
                (project_id, member_id, role, allocation_pct, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                assignment.project_id,
                assignment.member_id,
                assignment.role.value,
                assignment.allocation_pct,
                assignment.start_date.isoformat() if assignment.start_date else None,
                assignment.end_date.isoformat() if assignment.end_date else None,
            ),
        )
        return cursor.lastrowid  # type: ignore[return-value]

    def remove_assignment(self, assignment_id: int) -> None:
        self._execute(
            "DELETE FROM project_assignments WHERE id = ?", (assignment_id,)
        )

    def get_active_projects_for_member(
        self, member_id: int
    ) -> list[tuple[Project, ProjectRole]]:
        """Return active projects a member is assigned to, with their role."""
        sql = """
            SELECT p.*, pa.role AS assignment_role
            FROM projects p
            JOIN project_assignments pa ON pa.project_id = p.id
            WHERE pa.member_id = ?
              AND p.status IN ('planning', 'active')
            ORDER BY p.project_code
        """
        results: list[tuple[Project, ProjectRole]] = []
        for row in self._fetchall(sql, (member_id,)):
            project = self._row_to_project(row)
            role = ProjectRole(row["assignment_role"])
            results.append((project, role))
        return results
