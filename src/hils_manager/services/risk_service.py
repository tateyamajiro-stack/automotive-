"""Business logic for project risk management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from hils_manager.constants import RiskStatus

if TYPE_CHECKING:
    from hils_manager.models import Risk
    from hils_manager.repositories.risk_repository import RiskRepository

# Phrases considered as placeholder / non-actionable mitigation text.
_PLACEHOLDER_PHRASES: set[str] = {
    "tbd",
    "未定",
    "後で決める",
    "要検討",
    "n/a",
    "na",
    "none",
    "todo",
    "to be determined",
    "to be decided",
}


class RiskService:
    """Orchestrates risk CRUD and mitigation validation.

    Pure business logic -- no Qt dependency.
    """

    def __init__(self, risk_repo: RiskRepository) -> None:
        self._risk_repo = risk_repo

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def get_risks(self, project_id: int) -> list[Risk]:
        """Return all risks for *project_id*."""
        return self._risk_repo.get_by_project(project_id)

    def get_risk(self, risk_id: int) -> Risk | None:
        """Return a single risk by id, or ``None``."""
        return self._risk_repo.get_by_id(risk_id)

    def create_risk(self, risk: Risk) -> int:
        """Validate and persist a new risk.

        Raises :pyclass:`ValueError` if the mitigation text is invalid.
        """
        is_valid, error = self.validate_mitigation(risk.mitigation)
        if not is_valid:
            raise ValueError(error)
        return self._risk_repo.create(risk)

    def update_risk(self, risk: Risk) -> None:
        """Validate and update an existing risk.

        Raises :pyclass:`ValueError` if the mitigation text is invalid.
        """
        is_valid, error = self.validate_mitigation(risk.mitigation)
        if not is_valid:
            raise ValueError(error)
        self._risk_repo.update(risk)

    def delete_risk(self, risk_id: int) -> None:
        """Delete a risk by id."""
        self._risk_repo.delete(risk_id)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_mitigation(text: str) -> tuple[bool, str]:
        """Check that *text* represents a meaningful mitigation plan.

        Returns ``(True, "")`` on success, or ``(False, error_message)``
        describing the problem.

        Rules:
        * Must not be empty or whitespace-only.
        * Must not consist solely of a placeholder phrase such as "TBD",
          "未定", "後で決める", "要検討", etc.
        """
        stripped = text.strip()
        if not stripped:
            return False, "対策内容を入力してください。"

        if stripped.lower() in _PLACEHOLDER_PHRASES:
            return False, (
                f"「{stripped}」は対策として不十分です。具体的な対策内容を記入してください。"
            )

        return True, ""

    # ------------------------------------------------------------------
    # Summaries
    # ------------------------------------------------------------------

    def get_risk_summary(self, project_id: int) -> dict[str, Any]:
        """Return an aggregate risk summary for *project_id*.

        Keys:

        * ``total``           -- total number of risks
        * ``open``            -- risks with status OPEN or MITIGATING
        * ``high_risk_count`` -- high-probability / high-impact risks
        * ``resolved``        -- risks with status RESOLVED or ACCEPTED
        """
        risks = self._risk_repo.get_by_project(project_id)
        total = len(risks)
        open_count = sum(
            1
            for r in risks
            if r.status in (RiskStatus.OPEN, RiskStatus.MITIGATING)
        )
        resolved = sum(
            1
            for r in risks
            if r.status in (RiskStatus.RESOLVED, RiskStatus.ACCEPTED)
        )
        high_risk_count = len(self._risk_repo.get_high_risks(project_id))

        return {
            "total": total,
            "open": open_count,
            "high_risk_count": high_risk_count,
            "resolved": resolved,
        }
