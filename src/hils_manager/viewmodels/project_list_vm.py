"""ViewModel for the project list table."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

if TYPE_CHECKING:
    from hils_manager.models import Project
    from hils_manager.services.project_service import ProjectService


def _format_date(d: date | None) -> str:
    """Format a date as ``YYYY/MM/DD`` or return ``""``."""
    return d.strftime("%Y/%m/%d") if d is not None else ""


class ProjectListModel(QAbstractTableModel):
    """Qt table model that bridges :class:`ProjectService` to a ``QTableView``."""

    COLUMNS = ["project_code", "name", "status", "start_date", "end_date"]
    HEADERS = ["案件コード", "案件名", "ステータス", "開始日", "終了日"]

    def __init__(self, project_service: ProjectService, parent: Any = None) -> None:
        super().__init__(parent)
        self._service = project_service
        self._projects: list[Project] = []

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Reload data from the service and reset the model."""
        self.beginResetModel()
        self._projects = self._service.get_all_projects()
        self.endResetModel()

    def get_project(self, row: int) -> Project | None:
        """Return the :class:`Project` at *row*, or ``None``."""
        if 0 <= row < len(self._projects):
            return self._projects[row]
        return None

    # ------------------------------------------------------------------
    # QAbstractTableModel interface
    # ------------------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._projects)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None

        project = self._projects[index.row()]
        col = self.COLUMNS[index.column()]

        if col == "status":
            return project.status.label
        if col in ("start_date", "end_date"):
            return _format_date(getattr(project, col, None))

        value = getattr(project, col, None)
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
