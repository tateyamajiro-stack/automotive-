"""ViewModel for the team-member table."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

if TYPE_CHECKING:
    from hils_manager.models import TeamMember
    from hils_manager.services.resource_service import ResourceService


class MemberTableModel(QAbstractTableModel):
    """Qt table model that bridges :class:`ResourceService` to a ``QTableView``."""

    COLUMNS = ["employee_id", "name", "email", "is_outsourced", "daily_rate", "is_active"]
    HEADERS = ["社員番号", "氏名", "メール", "OS区分", "日単価", "有効"]

    def __init__(self, resource_service: ResourceService, parent: Any = None) -> None:
        super().__init__(parent)
        self._service = resource_service
        self._members: list[TeamMember] = []

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Reload data from the service and reset the model."""
        self.beginResetModel()
        self._members = self._service.get_all_members()
        self.endResetModel()

    def get_member(self, row: int) -> TeamMember | None:
        """Return the :class:`TeamMember` at *row*, or ``None``."""
        if 0 <= row < len(self._members):
            return self._members[row]
        return None

    # ------------------------------------------------------------------
    # QAbstractTableModel interface
    # ------------------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._members)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None

        member = self._members[index.row()]
        col = self.COLUMNS[index.column()]

        if col == "is_outsourced":
            return "OS" if member.is_outsourced else "プロパー"
        if col == "is_active":
            return "有効" if member.is_active else "無効"
        if col == "daily_rate":
            if member.daily_rate is None:
                return "-"
            return f"{member.daily_rate:,.0f}"

        value = getattr(member, col, None)
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
