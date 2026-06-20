"""Field mapping between local domain models and Jira issue representations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from hils_manager.constants import (
    RequirementPriority,
    RequirementStatus,
    RiskImpact,
    RiskProbability,
    RiskStatus,
    WBSStatus,
)

if TYPE_CHECKING:
    from hils_manager.models import Requirement, Risk, WBSItem

# ------------------------------------------------------------------
# Default mappings
# ------------------------------------------------------------------

DEFAULT_STATUS_MAPPING: dict[str, str] = {
    # WBSStatus
    WBSStatus.NOT_STARTED.value: "To Do",
    WBSStatus.IN_PROGRESS.value: "In Progress",
    WBSStatus.COMPLETED.value: "Done",
    WBSStatus.BLOCKED.value: "Blocked",
    WBSStatus.CANCELLED.value: "Cancelled",
    # RequirementStatus
    RequirementStatus.NEW.value: "To Do",
    RequirementStatus.ACCEPTED.value: "To Do",
    RequirementStatus.IN_PROGRESS.value: "In Progress",
    RequirementStatus.IMPLEMENTED.value: "Done",
    RequirementStatus.VERIFIED.value: "Done",
    RequirementStatus.DEFERRED.value: "On Hold",
    RequirementStatus.REJECTED.value: "Cancelled",
    # RiskStatus
    RiskStatus.OPEN.value: "To Do",
    RiskStatus.MITIGATING.value: "In Progress",
    RiskStatus.RESOLVED.value: "Done",
    RiskStatus.ACCEPTED.value: "Done",
}

DEFAULT_PRIORITY_MAPPING: dict[str, str] = {
    RequirementPriority.CRITICAL.value: "Highest",
    RequirementPriority.HIGH.value: "High",
    RequirementPriority.MEDIUM.value: "Medium",
    RequirementPriority.LOW.value: "Low",
    # Risk probability / impact share the same value strings.
    RiskProbability.HIGH.value: "High",
    RiskProbability.MEDIUM.value: "Medium",
    RiskProbability.LOW.value: "Low",
}

# ------------------------------------------------------------------
# Local -> Jira
# ------------------------------------------------------------------


def wbs_to_jira(wbs: WBSItem) -> dict[str, Any]:
    """Convert a :class:`WBSItem` to a Jira-compatible fields dict.

    The returned dict is suitable for passing as *fields* to
    :pymeth:`JiraClient.create_issue` or :pymeth:`JiraClient.update_issue`.
    """
    fields: dict[str, Any] = {
        "summary": wbs.title,
        "description": wbs.description or "",
    }

    priority_name = DEFAULT_PRIORITY_MAPPING.get("medium", "Medium")
    fields["priority"] = {"name": priority_name}

    status_label = DEFAULT_STATUS_MAPPING.get(
        wbs.status.value, "To Do"
    )
    fields["labels"] = [f"wbs:{wbs.wbs_code}", f"status:{status_label}"]

    if wbs.planned_start:
        fields["customfield_start_date"] = wbs.planned_start.isoformat()
    if wbs.planned_end:
        fields["duedate"] = wbs.planned_end.isoformat()
    if wbs.assigned_to_name:
        fields["description"] += f"\n\nAssigned to: {wbs.assigned_to_name}"

    return fields


def requirement_to_jira(req: Requirement) -> dict[str, Any]:
    """Convert a :class:`Requirement` to a Jira-compatible fields dict."""
    fields: dict[str, Any] = {
        "summary": req.title,
        "description": req.description or "",
    }

    priority_name = DEFAULT_PRIORITY_MAPPING.get(
        req.priority.value, "Medium"
    )
    fields["priority"] = {"name": priority_name}

    status_label = DEFAULT_STATUS_MAPPING.get(
        req.status.value, "To Do"
    )
    fields["labels"] = [
        f"req:{req.req_number}",
        f"status:{status_label}",
    ]

    if req.requested_by:
        fields["description"] += f"\n\nRequested by: {req.requested_by}"

    return fields


def risk_to_jira(risk: Risk) -> dict[str, Any]:
    """Convert a :class:`Risk` to a Jira-compatible fields dict.

    The mitigation plan is appended to the description body.
    """
    description_parts = [risk.description or ""]

    if risk.mitigation:
        description_parts.append(f"\n\n*Mitigation:*\n{risk.mitigation}")

    description_parts.append(
        f"\n\nProbability: {risk.probability.value.upper()} | "
        f"Impact: {risk.impact.value.upper()}"
    )

    fields: dict[str, Any] = {
        "summary": risk.title,
        "description": "".join(description_parts),
    }

    priority_name = DEFAULT_PRIORITY_MAPPING.get(
        risk.probability.value, "Medium"
    )
    fields["priority"] = {"name": priority_name}

    status_label = DEFAULT_STATUS_MAPPING.get(
        risk.status.value, "To Do"
    )
    fields["labels"] = [
        f"risk:{risk.risk_number}",
        f"status:{status_label}",
    ]

    return fields


# ------------------------------------------------------------------
# Jira -> Local
# ------------------------------------------------------------------


def _safe_get(data: dict[str, Any], *keys: str) -> Any:
    """Traverse nested dicts safely, returning ``None`` on missing keys."""
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def jira_to_wbs_fields(jira_issue: dict[str, Any]) -> dict[str, Any]:
    """Extract WBS-relevant fields from a Jira issue response.

    Returns a plain dict whose keys correspond to :class:`WBSItem`
    field names.
    """
    fields = jira_issue.get("fields", {})
    return {
        "title": fields.get("summary", ""),
        "description": fields.get("description", "") or "",
        "status": _resolve_status(fields, WBSStatus, WBSStatus.NOT_STARTED),
        "planned_end": fields.get("duedate"),
        "jira_issue_key": jira_issue.get("key", ""),
    }


def jira_to_requirement_fields(
    jira_issue: dict[str, Any],
) -> dict[str, Any]:
    """Extract requirement-relevant fields from a Jira issue response."""
    fields = jira_issue.get("fields", {})
    priority_name = _safe_get(fields, "priority", "name") or "Medium"
    return {
        "title": fields.get("summary", ""),
        "description": fields.get("description", "") or "",
        "priority": _resolve_priority(priority_name),
        "status": _resolve_status(
            fields, RequirementStatus, RequirementStatus.NEW
        ),
    }


def jira_to_risk_fields(jira_issue: dict[str, Any]) -> dict[str, Any]:
    """Extract risk-relevant fields from a Jira issue response."""
    fields = jira_issue.get("fields", {})
    priority_name = _safe_get(fields, "priority", "name") or "Medium"
    return {
        "title": fields.get("summary", ""),
        "description": fields.get("description", "") or "",
        "probability": _resolve_risk_level(priority_name, RiskProbability),
        "impact": RiskImpact.MEDIUM,
        "status": _resolve_status(fields, RiskStatus, RiskStatus.OPEN),
    }


# ------------------------------------------------------------------
# Internal resolution helpers
# ------------------------------------------------------------------

# Reverse mapping: Jira status name -> local enum value
_REVERSE_STATUS: dict[str, str] = {}
for _local_val, _jira_name in DEFAULT_STATUS_MAPPING.items():
    _REVERSE_STATUS.setdefault(_jira_name.lower(), _local_val)


def _resolve_status(
    fields: dict[str, Any],
    enum_cls: type,
    default: Any,
) -> Any:
    """Map a Jira status name back to a local enum member."""
    jira_status = _safe_get(fields, "status", "name")
    if not jira_status:
        return default
    local_val = _REVERSE_STATUS.get(jira_status.lower())
    if local_val is None:
        return default
    try:
        return enum_cls(local_val)
    except ValueError:
        return default


# Reverse mapping: Jira priority name -> RequirementPriority
_REVERSE_PRIORITY: dict[str, RequirementPriority] = {
    "highest": RequirementPriority.CRITICAL,
    "high": RequirementPriority.HIGH,
    "medium": RequirementPriority.MEDIUM,
    "low": RequirementPriority.LOW,
    "lowest": RequirementPriority.LOW,
}


def _resolve_priority(jira_priority_name: str) -> RequirementPriority:
    """Map a Jira priority name to :class:`RequirementPriority`."""
    return _REVERSE_PRIORITY.get(
        jira_priority_name.lower(), RequirementPriority.MEDIUM
    )


def _resolve_risk_level(
    jira_priority_name: str,
    enum_cls: type[RiskProbability] | type[RiskImpact],
) -> RiskProbability | RiskImpact:
    """Map a Jira priority name to a risk probability or impact level."""
    mapping: dict[str, str] = {
        "highest": "high",
        "high": "high",
        "medium": "medium",
        "low": "low",
        "lowest": "low",
    }
    value = mapping.get(jira_priority_name.lower(), "medium")
    return enum_cls(value)
