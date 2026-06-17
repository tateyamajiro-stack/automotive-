from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from hils_manager.constants import EstimateType


@dataclass
class Estimate:
    """Work effort estimate."""

    id: Optional[int] = None
    project_id: int = 0
    wbs_item_id: Optional[int] = None
    estimate_type: EstimateType = EstimateType.INITIAL
    man_hours: float = 0.0
    lead_time_days: Optional[int] = None
    estimator_id: Optional[int] = None
    assumptions: str = ""
    created_at: Optional[datetime] = None
    wbs_title: Optional[str] = None


@dataclass
class TimeEntry:
    """Time tracking entry for work performed."""

    id: Optional[int] = None
    project_id: int = 0
    wbs_item_id: Optional[int] = None
    member_id: int = 0
    work_date: Optional[date] = None
    hours: float = 0.0
    description: str = ""
    created_at: Optional[datetime] = None
    member_name: Optional[str] = None
    wbs_title: Optional[str] = None
