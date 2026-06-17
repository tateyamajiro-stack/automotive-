from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from hils_manager.constants import (
    DeliverableStatus,
    ReviewStatus,
    ReviewType,
)


@dataclass
class Deliverable:
    """Project deliverable domain entity."""

    id: Optional[int] = None
    project_id: int = 0
    process_def_id: Optional[int] = None
    title: str = ""
    status: DeliverableStatus = DeliverableStatus.NOT_STARTED
    assigned_to: Optional[int] = None
    due_date: Optional[date] = None
    completed_date: Optional[date] = None
    file_path: str = ""
    content_json: str = ""
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class DeliverableReview:
    """Review record for a deliverable."""

    id: Optional[int] = None
    deliverable_id: int = 0
    review_type: ReviewType = ReviewType.PEER_REVIEW
    reviewer_id: Optional[int] = None
    status: ReviewStatus = ReviewStatus.PENDING
    comments: str = ""
    review_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    reviewer_name: Optional[str] = None
