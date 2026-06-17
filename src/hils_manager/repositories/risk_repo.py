"""Repository for risk persistence."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from typing import Optional

from hils_manager.constants import RiskImpact, RiskProbability, RiskStatus
from hils_manager.models import Risk

from .base_repository import BaseRepository


class RiskRepository(BaseRepository):
    """CRUD operations for the ``risks`` table."""

    # ------------------------------------------------------------------
    # Row mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_risk(row: sqlite3.Row) -> Risk:
        return Risk(
            id=row["id"],
            project_id=row["project_id"],
            risk_number=row["risk_number"],
            title=row["title"],
            description=row["description"] or "",
            probability=RiskProbability(row["probability"]),
            impact=RiskImpact(row["impact"]),
            mitigation=row["mitigation"] or "",
            status=RiskStatus(row["status"]),
            owner_id=row["owner_id"],
            identified_date=(
                date.fromisoformat(row["identified_date"])
                if row["identified_date"]
                else None
            ),
            target_date=(
                date.fromisoformat(row["target_date"])
                if row["target_date"]
                else None
            ),
            resolution_date=(
                date.fromisoformat(row["resolution_date"])
                if row["resolution_date"]
                else None
            ),
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
            owner_name=(
                row["owner_name"] if "owner_name" in row.keys() else None
            ),
        )

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_by_project(self, project_id: int) -> list[Risk]:
        """Return all risks for a project, with owner names."""
        sql = """
            SELECT r.*, tm.name AS owner_name
            FROM risks r
            LEFT JOIN team_members tm ON tm.id = r.owner_id
            WHERE r.project_id = ?
            ORDER BY r.risk_number
        """
        return [self._row_to_risk(r) for r in self._fetchall(sql, (project_id,))]

    def get_by_id(self, risk_id: int) -> Optional[Risk]:
        sql = """
            SELECT r.*, tm.name AS owner_name
            FROM risks r
            LEFT JOIN team_members tm ON tm.id = r.owner_id
            WHERE r.id = ?
        """
        row = self._fetchone(sql, (risk_id,))
        return self._row_to_risk(row) if row else None

    def create(self, risk: Risk) -> int:
        now = self._now()
        cursor = self._execute(
            """
            INSERT INTO risks
                (project_id, risk_number, title, description, probability,
                 impact, mitigation, status, owner_id, identified_date,
                 target_date, resolution_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                risk.project_id,
                risk.risk_number,
                risk.title,
                risk.description,
                risk.probability.value,
                risk.impact.value,
                risk.mitigation,
                risk.status.value,
                risk.owner_id,
                risk.identified_date.isoformat() if risk.identified_date else None,
                risk.target_date.isoformat() if risk.target_date else None,
                risk.resolution_date.isoformat() if risk.resolution_date else None,
                now,
                now,
            ),
        )
        return cursor.lastrowid  # type: ignore[return-value]

    def update(self, risk: Risk) -> None:
        now = self._now()
        self._execute(
            """
            UPDATE risks
            SET risk_number     = ?,
                title           = ?,
                description     = ?,
                probability     = ?,
                impact          = ?,
                mitigation      = ?,
                status          = ?,
                owner_id        = ?,
                identified_date = ?,
                target_date     = ?,
                resolution_date = ?,
                updated_at      = ?
            WHERE id = ?
            """,
            (
                risk.risk_number,
                risk.title,
                risk.description,
                risk.probability.value,
                risk.impact.value,
                risk.mitigation,
                risk.status.value,
                risk.owner_id,
                risk.identified_date.isoformat() if risk.identified_date else None,
                risk.target_date.isoformat() if risk.target_date else None,
                risk.resolution_date.isoformat() if risk.resolution_date else None,
                now,
                risk.id,
            ),
        )

    def delete(self, risk_id: int) -> None:
        self._execute("DELETE FROM risks WHERE id = ?", (risk_id,))

    def get_next_risk_number(self, project_id: int) -> str:
        """Return the next risk number for the project (e.g. ``RISK-001``)."""
        row = self._fetchone(
            """
            SELECT risk_number FROM risks
            WHERE project_id = ?
            ORDER BY risk_number DESC
            LIMIT 1
            """,
            (project_id,),
        )
        if row and row["risk_number"]:
            try:
                num = int(row["risk_number"].split("-")[1])
                return f"RISK-{num + 1:03d}"
            except (IndexError, ValueError):
                pass
        return "RISK-001"

    def get_open_risks_count(self, project_id: int) -> int:
        """Return the count of non-resolved risks for a project."""
        row = self._fetchone(
            """
            SELECT COUNT(*) AS cnt FROM risks
            WHERE project_id = ?
              AND status NOT IN ('resolved', 'accepted')
            """,
            (project_id,),
        )
        return row["cnt"] if row else 0

    def get_high_risks(self, project_id: int) -> list[Risk]:
        """Return risks with high probability or high impact that are still open."""
        sql = """
            SELECT r.*, tm.name AS owner_name
            FROM risks r
            LEFT JOIN team_members tm ON tm.id = r.owner_id
            WHERE r.project_id = ?
              AND (r.probability = 'high' OR r.impact = 'high')
              AND r.status NOT IN ('resolved', 'accepted')
            ORDER BY r.risk_number
        """
        return [self._row_to_risk(r) for r in self._fetchall(sql, (project_id,))]
