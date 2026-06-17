from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from hils_manager.constants import ProcessPhase


@dataclass
class ProcessDefinition:
    """Definition of a development process step."""

    id: Optional[int] = None
    code: str = ""
    name_ja: str = ""
    name_en: str = ""
    phase: ProcessPhase = ProcessPhase.PLANNING
    sort_order: int = 0
    is_default: bool = True


@dataclass
class ProcessSelection:
    """Records which processes are selected for a project."""

    id: Optional[int] = None
    project_id: int = 0
    process_def_id: int = 0
    is_selected: bool = True
    skip_reason: str = ""
    process_name_ja: Optional[str] = None
