"""Business logic for estimates and time-tracking."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hils_manager.models import Estimate, TimeEntry
    from hils_manager.repositories.estimate_repository import EstimateRepository


class EstimateService:
    """Orchestrates estimate CRUD, time entry tracking and variance analysis.

    Pure business logic -- no Qt dependency.
    """

    def __init__(self, estimate_repo: EstimateRepository) -> None:
        self._estimate_repo = estimate_repo

    # ------------------------------------------------------------------
    # Estimate CRUD
    # ------------------------------------------------------------------

    def create_estimate(self, estimate: Estimate) -> int:
        """Persist a new estimate and return its id."""
        return self._estimate_repo.create(estimate)

    def update_estimate(self, estimate: Estimate) -> None:
        """Update an existing estimate."""
        self._estimate_repo.update(estimate)

    def delete_estimate(self, estimate_id: int) -> None:
        """Delete an estimate by id."""
        self._estimate_repo.delete(estimate_id)

    # ------------------------------------------------------------------
    # Time entries
    # ------------------------------------------------------------------

    def add_time_entry(self, entry: TimeEntry) -> int:
        """Record a new time entry and return its id."""
        return self._estimate_repo.add_time_entry(entry)

    def get_time_entries(self, project_id: int) -> list[TimeEntry]:
        """Return all time entries for *project_id*."""
        return self._estimate_repo.get_time_entries(project_id)

    # ------------------------------------------------------------------
    # Estimate vs. actual analysis
    # ------------------------------------------------------------------

    def get_estimate_vs_actual(self, project_id: int) -> dict[str, Any]:
        """Compute project-level estimate-vs-actual comparison.

        Returns a dict with keys:

        * ``planned_hours``   -- total estimated man-hours
        * ``actual_hours``    -- total logged hours
        * ``variance_pct``    -- ``(actual - planned) / planned * 100`` (0 if no plan)
        * ``planned_lead_days`` -- total estimated lead-time days
        * ``actual_lead_days``  -- total actual calendar days from time entries
        """
        estimates: list[Estimate] = self._estimate_repo.get_by_project(project_id)

        planned_hours = sum(e.man_hours for e in estimates)
        planned_lead_days = sum(
            e.lead_time_days for e in estimates if e.lead_time_days is not None
        )

        actual_hours: float = self._estimate_repo.get_actual_hours_by_project(
            project_id
        )

        # Derive actual lead days from the span of time entries.
        entries: list[TimeEntry] = self._estimate_repo.get_time_entries(project_id)
        if entries:
            dates = [e.work_date for e in entries if e.work_date is not None]
            if dates:
                actual_lead_days = (max(dates) - min(dates)).days + 1
            else:
                actual_lead_days = 0
        else:
            actual_lead_days = 0

        if planned_hours > 0:
            variance_pct = (actual_hours - planned_hours) / planned_hours * 100.0
        else:
            variance_pct = 0.0

        return {
            "planned_hours": planned_hours,
            "actual_hours": actual_hours,
            "variance_pct": round(variance_pct, 1),
            "planned_lead_days": planned_lead_days,
            "actual_lead_days": actual_lead_days,
        }

    def get_estimate_vs_actual_by_wbs(
        self, project_id: int
    ) -> list[dict[str, Any]]:
        """Compute per-WBS estimate-vs-actual comparisons.

        Returns a list of dicts, each with:

        * ``wbs_item_id``
        * ``wbs_title``
        * ``planned_hours``
        * ``actual_hours``
        * ``variance_pct``
        """
        estimates: list[Estimate] = self._estimate_repo.get_by_project(project_id)
        actual_by_wbs: dict[int, float] = self._estimate_repo.get_actual_hours_by_wbs(
            project_id
        )

        # Group estimates by WBS item.
        planned_by_wbs: dict[int, float] = {}
        title_by_wbs: dict[int, str] = {}
        for est in estimates:
            wbs_id = est.wbs_item_id
            if wbs_id is None:
                continue
            planned_by_wbs[wbs_id] = planned_by_wbs.get(wbs_id, 0.0) + est.man_hours
            if est.wbs_title:
                title_by_wbs[wbs_id] = est.wbs_title

        all_wbs_ids = set(planned_by_wbs) | set(actual_by_wbs)
        results: list[dict[str, Any]] = []
        for wbs_id in sorted(all_wbs_ids):
            planned = planned_by_wbs.get(wbs_id, 0.0)
            actual = actual_by_wbs.get(wbs_id, 0.0)
            if planned > 0:
                variance = (actual - planned) / planned * 100.0
            else:
                variance = 0.0
            results.append(
                {
                    "wbs_item_id": wbs_id,
                    "wbs_title": title_by_wbs.get(wbs_id, ""),
                    "planned_hours": planned,
                    "actual_hours": actual,
                    "variance_pct": round(variance, 1),
                }
            )

        return results
