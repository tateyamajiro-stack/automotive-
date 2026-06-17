from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class JiraSyncMapping:
    """Maps local entities to Jira issues for synchronization."""

    id: Optional[int] = None
    project_id: int = 0
    local_entity: str = ""
    local_id: int = 0
    jira_issue_key: str = ""
    jira_issue_id: str = ""
    last_sync_at: Optional[datetime] = None
    sync_direction: str = ""
    sync_status: str = ""


@dataclass
class JiraSyncLog:
    """Log entry for a Jira synchronization operation."""

    id: Optional[int] = None
    mapping_id: int = 0
    sync_type: str = ""
    status: str = ""
    details: str = ""
    synced_at: Optional[datetime] = None
