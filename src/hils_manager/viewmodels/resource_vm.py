"""ViewModel for the cross-project resource overview."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

if TYPE_CHECKING:
    from hils_manager.models import TeamMember
    from hils_manager.services.resource_service import ResourceService


class _AllocationRow:
    """Flat representation of one member-project allocation for display."""

    __slots__ = ("name", "is_outsourced", "project_name", "role_label", "allocation_pct")

    def __init__(
        self,
        name: str,
        is_outsourced: bool,
        project_name: str,
        role_label: str,
        allocation_pct: float,
    ) -> None:
        self.name = name
        self.is_outsourced = is_outsourced
        self.project_name = project_name
        self.role_label = role_label
        self.allocation_pct = allocation_pct


class ResourceOverviewModel(QAbstractTableModel):
    """Qt table model showing cross-project resource allocation."""

    COLUMNS = ["name", "is_outsourced", "project_name", "role", "allocation_pct"]
    HEADERS = ["氏名", "区分", "案件名", "役割", "アサイン率(%)"]

    def __init__(self, resource_service: ResourceService, parent: Any = None) -> None:
        super().__init__(parent)
        self._service = resource_service
        self._rows: list[_AllocationRow] = []

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Reload data from the service and rebuild the flat row list."""
        self.beginResetModel()
        overview = self._service.get_resource_overview()
        members_by_id: dict[int, TeamMember] = {}
        for m in self._service.get_all_members():
            if m.id is not None:
                members_by_id[m.id] = m

        rows: list[_AllocationRow] = []
        for member_id, allocations in overview.items():
            member = members_by_id.get(member_id)
            if member is None:
                continue
            for alloc in allocations:
                rows.append(
                    _AllocationRow(
                        name=member.name,
                        is_outsourced=member.is_outsourced,
                        project_name=alloc.project.name,
                        role_label=alloc.role.label,
                        allocation_pct=alloc.allocation_pct,
                    )
                )

        self._rows = rows
        self.endResetModel()

    def get_unassigned_alert(self) -> list[TeamMember]:
        """Return outsourced members not currently assigned to any active project.

        This is an alert condition -- outsourced members without work still
        incur cost.
        """
        return self._service.get_unassigned_outsourced_members()

    # ------------------------------------------------------------------
    # QAbstractTableModel interface
    # ------------------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None

        row = self._rows[index.row()]
        col = self.COLUMNS[index.column()]

        if col == "name":
            return row.name
        if col == "is_outsourced":
            return "OS" if row.is_outsourced else "プロパー"
        if col == "project_name":
            return row.project_name
        if col == "role":
            return row.role_label
        if col == "allocation_pct":
            return f"{row.allocation_pct:.0f}"

        return ""

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
