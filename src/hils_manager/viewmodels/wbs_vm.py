"""ViewModel for the WBS tree."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt

if TYPE_CHECKING:
    from hils_manager.models import WBSItem
    from hils_manager.repositories.wbs_repo import WBSRepository


def _format_date(d: date | None) -> str:
    """Format a date as ``YYYY/MM/DD`` or return ``""``."""
    return d.strftime("%Y/%m/%d") if d is not None else ""


@dataclass
class _TreeNode:
    """Internal node wrapping a :class:`WBSItem` for tree navigation."""

    item: WBSItem | None = None
    parent_node: _TreeNode | None = None
    children: list[_TreeNode] = field(default_factory=list)
    row_in_parent: int = 0


class WBSTreeModel(QAbstractItemModel):
    """Qt tree model that bridges :class:`WBSRepository` to a ``QTreeView``."""

    COLUMNS = [
        "wbs_code",
        "title",
        "status",
        "assigned_to_name",
        "planned_start",
        "planned_end",
        "planned_hours",
    ]
    HEADERS = ["WBSコード", "タイトル", "ステータス", "担当者", "開始予定", "終了予定", "予定工数"]

    def __init__(
        self,
        wbs_repo: WBSRepository,
        project_id: int,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._repo = wbs_repo
        self._project_id = project_id
        self._root = _TreeNode()

    # ------------------------------------------------------------------
    # Tree building
    # ------------------------------------------------------------------

    @staticmethod
    def _build_nodes(items: list[WBSItem], parent_node: _TreeNode) -> None:
        """Recursively convert a list of :class:`WBSItem` into ``_TreeNode`` children."""
        for idx, item in enumerate(items):
            node = _TreeNode(item=item, parent_node=parent_node, row_in_parent=idx)
            parent_node.children.append(node)
            if item.children:
                WBSTreeModel._build_nodes(item.children, node)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Reload data from the repository and rebuild the tree."""
        self.beginResetModel()
        tree = self._repo.get_tree(self._project_id)
        self._root = _TreeNode()
        self._build_nodes(tree, self._root)
        self.endResetModel()

    def get_wbs_item(self, index: QModelIndex) -> WBSItem | None:
        """Return the :class:`WBSItem` at *index*, or ``None``."""
        if not index.isValid():
            return None
        node: _TreeNode = index.internalPointer()  # type: ignore[assignment]
        return node.item

    # ------------------------------------------------------------------
    # QAbstractItemModel interface
    # ------------------------------------------------------------------

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parent_node: _TreeNode
        if not parent.isValid():
            parent_node = self._root
        else:
            parent_node = parent.internalPointer()  # type: ignore[assignment]

        if 0 <= row < len(parent_node.children):
            return self.createIndex(row, column, parent_node.children[row])
        return QModelIndex()

    def parent(self, index: QModelIndex = QModelIndex()) -> QModelIndex:  # type: ignore[override]
        if not index.isValid():
            return QModelIndex()

        node: _TreeNode = index.internalPointer()  # type: ignore[assignment]
        parent_node = node.parent_node

        if parent_node is None or parent_node is self._root:
            return QModelIndex()

        return self.createIndex(parent_node.row_in_parent, 0, parent_node)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.column() > 0:
            return 0

        parent_node: _TreeNode
        if not parent.isValid():
            parent_node = self._root
        else:
            parent_node = parent.internalPointer()  # type: ignore[assignment]

        return len(parent_node.children)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None

        node: _TreeNode = index.internalPointer()  # type: ignore[assignment]
        item = node.item
        if item is None:
            return None

        col = self.COLUMNS[index.column()]

        if col == "status":
            return item.status.label
        if col in ("planned_start", "planned_end"):
            return _format_date(getattr(item, col, None))
        if col == "planned_hours":
            if item.planned_hours is None:
                return "-"
            return f"{item.planned_hours:.1f}"
        if col == "assigned_to_name":
            return item.assigned_to_name or ""

        value = getattr(item, col, None)
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
        return None
