from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from hils_manager.constants import ProjectRole, ProjectStatus


@dataclass
class Project:
    """Project domain entity."""

    id: Optional[int] = None
    project_code: str = ""
    name: str = ""
    description: str = ""
    status: ProjectStatus = ProjectStatus.PLANNING
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    jira_project_key: str = ""
    efficiency_jira_url: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class ProjectAssignment:
    """Assigns a team member to a project with a specific role."""

    id: Optional[int] = None
    project_id: int = 0
    member_id: int = 0
    role: ProjectRole = ProjectRole.PRIMARY_DEVELOPER
    allocation_pct: float = 100.0
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    member_name: Optional[str] = None
