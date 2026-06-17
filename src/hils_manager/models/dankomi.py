from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class DankomiRecord:
    """Dankomi (段組) meeting record."""

    id: Optional[int] = None
    project_id: int = 0
    meeting_date: Optional[date] = None
    attendees: list[int] = field(default_factory=list)
    goal_state: str = ""
    goal_deliverables: str = ""
    agenda: str = ""
    decisions: str = ""
    action_items: list[dict] = field(default_factory=list)
    notes: str = ""
    created_at: Optional[datetime] = None
