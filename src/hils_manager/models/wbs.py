from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from hils_manager.constants import WBSStatus


@dataclass
class WBSItem:
    """Work Breakdown Structure item."""

    id: Optional[int] = None
    project_id: int = 0
    parent_id: Optional[int] = None
    wbs_code: str = ""
    title: str = ""
    description: str = ""
    assigned_to: Optional[int] = None
    status: WBSStatus = WBSStatus.NOT_STARTED
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    planned_hours: Optional[float] = None
    dependency_ids: list[int] = field(default_factory=list)
    sort_order: int = 0
    jira_issue_key: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    children: list[WBSItem] = field(default_factory=list)
    assigned_to_name: Optional[str] = None
