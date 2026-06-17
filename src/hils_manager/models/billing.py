from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class OutsourceBilling:
    """Billing record for outsourced team members."""

    id: Optional[int] = None
    member_id: int = 0
    project_id: int = 0
    billing_month: str = ""
    man_days: float = 0.0
    daily_rate: float = 0.0
    total_amount: float = 0.0
    notes: str = ""
    created_at: Optional[datetime] = None
    member_name: Optional[str] = None
    project_name: Optional[str] = None
