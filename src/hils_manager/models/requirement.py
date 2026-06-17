from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from hils_manager.constants import RequirementPriority, RequirementStatus


@dataclass
class Requirement:
    """Project requirement domain entity."""

    id: Optional[int] = None
    project_id: int = 0
    req_number: str = ""
    title: str = ""
    description: str = ""
    priority: RequirementPriority = RequirementPriority.MEDIUM
    status: RequirementStatus = RequirementStatus.NEW
    requested_by: str = ""
    requested_date: Optional[date] = None
    target_version: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
