"""Repository for team member persistence."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Optional

from hils_manager.models import TeamMember

from .base_repository import BaseRepository


class MemberRepository(BaseRepository):
    """CRUD operations for the ``team_members`` table."""

    # ------------------------------------------------------------------
    # Row mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_member(row: sqlite3.Row) -> TeamMember:
        """Convert a ``sqlite3.Row`` to a :class:`TeamMember`."""
        skills_raw = row["skills"]
        skills = json.loads(skills_raw) if skills_raw else []

        return TeamMember(
            id=row["id"],
            employee_id=row["employee_id"],
            name=row["name"],
            email=row["email"],
            is_outsourced=bool(row["is_outsourced"]),
            daily_rate=row["daily_rate"],
            skills=skills,
            is_active=bool(row["is_active"]),
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

    def get_all(self, active_only: bool = True) -> list[TeamMember]:
        """Return all team members, optionally filtered to active ones."""
        if active_only:
            sql = "SELECT * FROM team_members WHERE is_active = 1 ORDER BY name"
        else:
            sql = "SELECT * FROM team_members ORDER BY name"
        return [self._row_to_member(r) for r in self._fetchall(sql)]

    def get_by_id(self, member_id: int) -> Optional[TeamMember]:
        """Return a single member by primary key, or ``None``."""
        row = self._fetchone(
            "SELECT * FROM team_members WHERE id = ?", (member_id,)
        )
        return self._row_to_member(row) if row else None

    def create(self, member: TeamMember) -> int:
        """Insert a new member and return the generated id."""
        now = self._now()
        cursor = self._execute(
            """
            INSERT INTO team_members
                (employee_id, name, email, is_outsourced, daily_rate,
                 skills, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                member.employee_id,
                member.name,
                member.email,
                int(member.is_outsourced),
                member.daily_rate,
                json.dumps(member.skills),
                int(member.is_active),
                now,
                now,
            ),
        )
        return cursor.lastrowid  # type: ignore[return-value]

    def update(self, member: TeamMember) -> None:
        """Update an existing member row."""
        now = self._now()
        self._execute(
            """
            UPDATE team_members
            SET employee_id   = ?,
                name          = ?,
                email         = ?,
                is_outsourced = ?,
                daily_rate    = ?,
                skills        = ?,
                is_active     = ?,
                updated_at    = ?
            WHERE id = ?
            """,
            (
                member.employee_id,
                member.name,
                member.email,
                int(member.is_outsourced),
                member.daily_rate,
                json.dumps(member.skills),
                int(member.is_active),
                now,
                member.id,
            ),
        )

    def delete(self, member_id: int) -> None:
        """Soft-delete a member by setting ``is_active = 0``."""
        now = self._now()
        self._execute(
            "UPDATE team_members SET is_active = 0, updated_at = ? WHERE id = ?",
            (now, member_id),
        )

    def get_outsourced_members(self) -> list[TeamMember]:
        """Return all active outsourced members."""
        sql = (
            "SELECT * FROM team_members "
            "WHERE is_outsourced = 1 AND is_active = 1 "
            "ORDER BY name"
        )
        return [self._row_to_member(r) for r in self._fetchall(sql)]

    def get_unassigned_members(self) -> list[TeamMember]:
        """Return active members not assigned to any active project."""
        sql = """
            SELECT tm.*
            FROM team_members tm
            WHERE tm.is_active = 1
              AND tm.id NOT IN (
                  SELECT pa.member_id
                  FROM project_assignments pa
                  JOIN projects p ON p.id = pa.project_id
                  WHERE p.status IN ('planning', 'active')
              )
            ORDER BY tm.name
        """
        return [self._row_to_member(r) for r in self._fetchall(sql)]
