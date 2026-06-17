"""ViewModels for estimate and time-entry tables."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

if TYPE_CHECKING:
    from hils_manager.models import Estimate, TimeEntry
    from hils_manager.services.estimate_service import EstimateService


def _format_date(d: date | None) -> str:
    """Format a date as ``YYYY/MM/DD`` or return ``""``."""
    return d.strftime("%Y/%m/%d") if d is not None else ""


class EstimateTableModel(QAbstractTableModel):
    """Qt table model for project estimates."""

    COLUMNS = ["wbs_title", "estimate_type", "man_hours", "lead_time_days", "assumptions"]
    HEADERS = ["WBS", "見積種別", "工数(人時)", "リードタイム(日)", "前提条件"]

    def __init__(
        self,
        estimate_service: EstimateService,
        project_id: int,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._service = estimate_service
        self._project_id = project_id
        self._estimates: list[Estimate] = []

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Reload data from the service and reset the model."""
        self.beginResetModel()
        self._estimates = self._service._estimate_repo.get_by_project(self._project_id)
        self.endResetModel()

    def get_estimate(self, row: int) -> Estimate | None:
        """Return the :class:`Estimate` at *row*, or ``None``."""
        if 0 <= row < len(self._estimates):
            return self._estimates[row]
        return None

    # ------------------------------------------------------------------
    # QAbstractTableModel interface
    # ------------------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._estimates)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None

        est = self._estimates[index.row()]
        col = self.COLUMNS[index.column()]

        if col == "estimate_type":
            return est.estimate_type.label
        if col == "man_hours":
            return f"{est.man_hours:.1f}"
        if col == "lead_time_days":
            if est.lead_time_days is None:
                return "-"
            return str(est.lead_time_days)
        if col == "wbs_title":
            return est.wbs_title or ""
        if col == "assumptions":
            return est.assumptions or ""

        value = getattr(est, col, None)
        return str(value) if value is not None else ""

    def headerData(  # noqa: N802
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal and 0 <= section < len(self.HEADERS):
            return self.HEADERS[section]
        if orientation == Qt.Orientation.Vertical:
            return section + 1
        return None


class TimeEntryTableModel(QAbstractTableModel):
    """Qt table model for time-tracking entries."""

    COLUMNS = ["work_date", "member_name", "wbs_title", "hours", "description"]
    HEADERS = ["作業日", "担当者", "WBS", "工数(h)", "内容"]

    def __init__(
        self,
        estimate_service: EstimateService,
        project_id: int,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._service = estimate_service
        self._project_id = project_id
        self._entries: list[TimeEntry] = []

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Reload data from the service and reset the model."""
        self.beginResetModel()
        self._entries = self._service.get_time_entries(self._project_id)
        self.endResetModel()

    # ------------------------------------------------------------------
    # QAbstractTableModel interface
    # ------------------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._entries)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None

        entry = self._entries[index.row()]
        col = self.COLUMNS[index.column()]

        if col == "work_date":
            return _format_date(entry.work_date)
        if col == "member_name":
            return entry.member_name or ""
        if col == "wbs_title":
            return entry.wbs_title or ""
        if col == "hours":
            return f"{entry.hours:.1f}"
        if col == "description":
            return entry.description or ""

        value = getattr(entry, col, None)
        return str(value) if value is not None else ""

    def headerData(  # noqa: N802
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal and 0 <= section < len(self.HEADERS):
            return self.HEADERS[section]
        if orientation == Qt.Orientation.Vertical:
            return section + 1
        return None
