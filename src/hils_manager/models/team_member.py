from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class TeamMember:
    """Team member domain entity."""

    id: Optional[int] = None
    employee_id: str = ""
    name: str = ""
    email: str = ""
    is_outsourced: bool = False
    daily_rate: Optional[float] = None
    skills: list[str] = field(default_factory=list)
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
