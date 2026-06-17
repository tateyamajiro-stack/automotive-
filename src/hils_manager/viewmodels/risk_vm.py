"""ViewModel for the risk table."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from hils_manager.constants import RiskImpact, RiskProbability

if TYPE_CHECKING:
    from hils_manager.models import Risk
    from hils_manager.services.risk_service import RiskService

# Colour hints for probability / impact levels.
_LEVEL_COLORS: dict[str, QColor] = {
    "high": QColor(220, 53, 69),     # red
    "medium": QColor(255, 193, 7),   # amber
    "low": QColor(40, 167, 69),      # green
}

_PROBABILITY_LABELS: dict[RiskProbability, str] = {
    RiskProbability.HIGH: "高",
    RiskProbability.MEDIUM: "中",
    RiskProbability.LOW: "低",
}

_IMPACT_LABELS: dict[RiskImpact, str] = {
    RiskImpact.HIGH: "高",
    RiskImpact.MEDIUM: "中",
    RiskImpact.LOW: "低",
}


class RiskTableModel(QAbstractTableModel):
    """Qt table model that bridges :class:`RiskService` to a ``QTableView``."""

    COLUMNS = [
        "risk_number",
        "title",
        "probability",
        "impact",
        "status",
        "owner_name",
        "mitigation",
    ]
    HEADERS = ["リスク番号", "タイトル", "発生確率", "影響度", "ステータス", "担当", "対策"]

    def __init__(
        self,
        risk_service: RiskService,
        project_id: int,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._service = risk_service
        self._project_id = project_id
        self._risks: list[Risk] = []

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Reload data from the service and reset the model."""
        self.beginResetModel()
        self._risks = self._service.get_risks(self._project_id)
        self.endResetModel()

    def get_risk(self, row: int) -> Risk | None:
        """Return the :class:`Risk` at *row*, or ``None``."""
        if 0 <= row < len(self._risks):
            return self._risks[row]
        return None

    # ------------------------------------------------------------------
    # QAbstractTableModel interface
    # ------------------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._risks)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        risk = self._risks[index.row()]
        col = self.COLUMNS[index.column()]

        # -- ForegroundRole: colour hints for probability / impact ------
        if role == Qt.ItemDataRole.ForegroundRole:
            if col == "probability":
                return _LEVEL_COLORS.get(risk.probability.value)
            if col == "impact":
                return _LEVEL_COLORS.get(risk.impact.value)
            return None

        if role != Qt.ItemDataRole.DisplayRole:
            return None

        # -- DisplayRole -----------------------------------------------
        if col == "probability":
            return _PROBABILITY_LABELS.get(risk.probability, risk.probability.value)
        if col == "impact":
            return _IMPACT_LABELS.get(risk.impact, risk.impact.value)
        if col == "status":
            return risk.status.label
        if col == "owner_name":
            return risk.owner_name or ""
        if col == "mitigation":
            return risk.mitigation or ""

        value = getattr(risk, col, None)
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
