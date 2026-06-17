from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from hils_manager.constants import RiskImpact, RiskProbability, RiskStatus


@dataclass
class Risk:
    """Project risk domain entity."""

    id: Optional[int] = None
    project_id: int = 0
    risk_number: str = ""
    title: str = ""
    description: str = ""
    probability: RiskProbability = RiskProbability.MEDIUM
    impact: RiskImpact = RiskImpact.MEDIUM
    mitigation: str = ""
    status: RiskStatus = RiskStatus.OPEN
    owner_id: Optional[int] = None
    identified_date: Optional[date] = None
    target_date: Optional[date] = None
    resolution_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    owner_name: Optional[str] = None
