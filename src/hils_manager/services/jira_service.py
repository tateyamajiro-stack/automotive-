"""Business logic for Jira synchronization."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hils_manager.integrations.jira_client import JiraClient
    from hils_manager.models import JiraSyncMapping
    from hils_manager.repositories.jira_repo import JiraSyncRepository
    from hils_manager.repositories.requirement_repo import RequirementRepository
    from hils_manager.repositories.risk_repo import RiskRepository
    from hils_manager.repositories.wbs_repo import WBSRepository

logger = logging.getLogger(__name__)


class JiraService:
    """Orchestrates push/fetch synchronization with Jira.

    Pure business logic -- no Qt dependency.
    """

    def __init__(
        self,
        jira_client: JiraClient,
        jira_repo: JiraSyncRepository,
        wbs_repo: WBSRepository,
        requirement_repo: RequirementRepository,
        risk_repo: RiskRepository,
    ) -> None:
        self._jira_client = jira_client
        self._jira_repo = jira_repo
        self._wbs_repo = wbs_repo
        self._requirement_repo = requirement_repo
        self._risk_repo = risk_repo

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def test_connection(self) -> bool:
        """Delegate to the Jira client to verify connectivity."""
        return self._jira_client.test_connection()

    # ------------------------------------------------------------------
    # Push
    # ------------------------------------------------------------------

    def push(self, project_id: int, jira_project_key: str) -> dict[str, Any]:
        """Push local entities to Jira.

        Returns a summary dict with keys ``pushed`` (int) and
        ``errors`` (list of error message strings).
        """
        from hils_manager.integrations.jira_mappers import (
            requirement_to_jira,
            risk_to_jira,
            wbs_to_jira,
        )
        from hils_manager.models import JiraSyncMapping

        pushed = 0
        errors: list[str] = []

        # Collect all entities to push.
        entity_batches: list[tuple[str, str, list[Any], Any]] = [
            ("wbs_item", "Task", self._wbs_repo.get_by_project(project_id), wbs_to_jira),
            (
                "requirement",
                "Story",
                self._requirement_repo.get_by_project(project_id),
                requirement_to_jira,
            ),
            ("risk", "Bug", self._risk_repo.get_by_project(project_id), risk_to_jira),
        ]

        for entity_type, issue_type, items, to_jira_fn in entity_batches:
            for item in items:
                try:
                    pushed += self._push_single(
                        entity_type,
                        issue_type,
                        item,
                        to_jira_fn,
                        project_id,
                        jira_project_key,
                    )
                except Exception as exc:  # noqa: BLE001
                    msg = f"{entity_type} id={item.id}: {exc}"
                    logger.error("Push error — %s", msg)
                    errors.append(msg)

        return {"pushed": pushed, "errors": errors}

    def _push_single(
        self,
        entity_type: str,
        issue_type: str,
        item: Any,
        to_jira_fn: Any,
        project_id: int,
        jira_project_key: str,
    ) -> int:
        """Push a single entity. Returns 1 on success."""
        from hils_manager.models import JiraSyncMapping

        fields = to_jira_fn(item)
        mapping = self._jira_repo.get_mapping(entity_type, item.id)

        if mapping is None:
            result = self._jira_client.create_issue(
                jira_project_key, issue_type, fields
            )
            new_mapping = JiraSyncMapping(
                project_id=project_id,
                local_entity=entity_type,
                local_id=item.id,
                jira_issue_key=result["key"],
                jira_issue_id=result.get("id", ""),
                sync_direction="bidirectional",
                sync_status="synced",
            )
            mapping_id = self._jira_repo.upsert_mapping(new_mapping)
            self._jira_repo.add_log(mapping_id, "push", "success", "Created issue")
        else:
            # Update existing issue in Jira.
            self._jira_client.update_issue(mapping.jira_issue_key, fields)
            self._jira_repo.update_sync_status(mapping.id, "synced")  # type: ignore[arg-type]
            self._jira_repo.add_log(
                mapping.id, "push", "success", "Updated issue"  # type: ignore[arg-type]
            )

        return 1

    # ------------------------------------------------------------------
    # Fetch
    # ------------------------------------------------------------------

    def fetch(self, project_id: int, jira_project_key: str) -> dict[str, Any]:
        """Fetch Jira issues and reconcile with local entities.

        Returns a summary dict with keys ``fetched`` (int),
        ``conflicts`` (int), and ``errors`` (list of error strings).
        """
        from hils_manager.integrations.jira_mappers import (
            jira_to_requirement_fields,
            jira_to_risk_fields,
            jira_to_wbs_fields,
        )

        fetched = 0
        conflicts = 0
        errors: list[str] = []

        try:
            issues = self._jira_client.search_issues(
                f"project = {jira_project_key}"
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Jira search failed: %s", exc)
            return {"fetched": 0, "conflicts": 0, "errors": [str(exc)]}

        for issue in issues:
            try:
                result = self._fetch_single(issue, project_id)
                if result == "fetched":
                    fetched += 1
                elif result == "conflict":
                    conflicts += 1
            except Exception as exc:  # noqa: BLE001
                msg = f"issue {issue.get('key', '?')}: {exc}"
                logger.error("Fetch error — %s", msg)
                errors.append(msg)

        return {"fetched": fetched, "conflicts": conflicts, "errors": errors}

    def _fetch_single(self, issue: dict[str, Any], project_id: int) -> str:
        """Process a single Jira issue during fetch.

        Returns ``"fetched"``, ``"conflict"``, or ``"skipped"``.
        """
        issue_key: str = issue["key"]
        mapping = self._jira_repo.get_by_jira_key(issue_key)

        if mapping is None:
            # No local mapping -- skip for safety (do not auto-create).
            return "skipped"

        if mapping.sync_status == "local_modified":
            # Local changes exist -- mark as conflict.
            self._jira_repo.update_sync_status(mapping.id, "conflict")  # type: ignore[arg-type]
            self._jira_repo.add_log(
                mapping.id,  # type: ignore[arg-type]
                "pull",
                "conflict",
                "Local entity modified — conflict detected",
            )
            return "conflict"

        # Safe to update local entity from Jira data.
        self._update_local_entity(mapping, issue)
        self._jira_repo.update_sync_status(mapping.id, "synced")  # type: ignore[arg-type]
        self._jira_repo.add_log(
            mapping.id, "pull", "success", "Updated from Jira"  # type: ignore[arg-type]
        )
        return "fetched"

    def _update_local_entity(
        self, mapping: JiraSyncMapping, issue: dict[str, Any]
    ) -> None:
        """Apply Jira issue data to the corresponding local entity."""
        from hils_manager.integrations.jira_mappers import (
            jira_to_requirement_fields,
            jira_to_risk_fields,
            jira_to_wbs_fields,
        )

        entity_type = mapping.local_entity
        entity_id = mapping.local_id

        if entity_type == "wbs":
            fields = jira_to_wbs_fields(issue)
            item = self._wbs_repo.get_by_id(entity_id)
            if item is not None:
                for key, value in fields.items():
                    if hasattr(item, key):
                        setattr(item, key, value)
                self._wbs_repo.update(item)

        elif entity_type == "requirement":
            fields = jira_to_requirement_fields(issue)
            item = self._requirement_repo.get_by_id(entity_id)
            if item is not None:
                for key, value in fields.items():
                    if hasattr(item, key):
                        setattr(item, key, value)
                self._requirement_repo.update(item)

        elif entity_type == "risk":
            fields = jira_to_risk_fields(issue)
            item = self._risk_repo.get_by_id(entity_id)
            if item is not None:
                for key, value in fields.items():
                    if hasattr(item, key):
                        setattr(item, key, value)
                self._risk_repo.update(item)

    # ------------------------------------------------------------------
    # Sync status overview
    # ------------------------------------------------------------------

    def get_sync_status(self, project_id: int) -> list[dict[str, Any]]:
        """Return sync status information for all mappings in a project.

        Each entry contains the mapping fields plus recent log summary.
        """
        mappings = self._jira_repo.get_by_project(project_id)
        result: list[dict[str, Any]] = []

        for m in mappings:
            logs = self._jira_repo.get_logs(m.id) if m.id else []  # type: ignore[arg-type]
            last_log = logs[0] if logs else None
            result.append(
                {
                    "mapping_id": m.id,
                    "local_entity": m.local_entity,
                    "local_id": m.local_id,
                    "jira_issue_key": m.jira_issue_key,
                    "sync_status": m.sync_status,
                    "sync_direction": m.sync_direction,
                    "last_sync_at": (
                        m.last_sync_at.isoformat() if m.last_sync_at else None
                    ),
                    "last_log_status": last_log.status if last_log else None,
                    "last_log_details": last_log.details if last_log else None,
                }
            )

        return result
