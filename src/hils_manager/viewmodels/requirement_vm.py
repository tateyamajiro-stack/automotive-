"""ViewModel for the requirement table."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

if TYPE_CHECKING:
    from hils_manager.models import Requirement
    from hils_manager.repositories.requirement_repo import RequirementRepository


class RequirementTableModel(QAbstractTableModel):
    """Qt table model that bridges :class:`RequirementRepository` to a ``QTableView``."""

    COLUMNS = [
        "req_number",
        "title",
        "priority",
        "status",
        "requested_by",
        "target_version",
    ]
    HEADERS = ["要望番号", "タイトル", "優先度", "ステータス", "要望元", "対象バージョン"]

    def __init__(
        self,
        requirement_repo: RequirementRepository,
        project_id: int,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._repo = requirement_repo
        self._project_id = project_id
        self._requirements: list[Requirement] = []

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Reload data from the repository and reset the model."""
        self.beginResetModel()
        self._requirements = self._repo.get_by_project(self._project_id)
        self.endResetModel()

    def get_requirement(self, row: int) -> Requirement | None:
        """Return the :class:`Requirement` at *row*, or ``None``."""
        if 0 <= row < len(self._requirements):
            return self._requirements[row]
        return None

    # ------------------------------------------------------------------
    # QAbstractTableModel interface
    # ------------------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._requirements)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None

        req = self._requirements[index.row()]
        col = self.COLUMNS[index.column()]

        if col == "priority":
            return req.priority.label
        if col == "status":
            return req.status.label

        value = getattr(req, col, None)
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
