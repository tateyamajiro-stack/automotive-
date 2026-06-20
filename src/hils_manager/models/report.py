from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Report:
    """Generated report domain entity."""

    id: Optional[int] = None
    project_id: Optional[int] = None
    report_type: str = ""
    format: str = ""
    title: str = ""
    generated_by: Optional[int] = None
    file_path: str = ""
    confluence_url: str = ""
    parameters_json: str = ""
    generated_at: Optional[datetime] = None
