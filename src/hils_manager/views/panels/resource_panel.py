"""リソース配置パネル.

クロスプロジェクトのリソース配置状況を表示し、
未アサインのOSメンバーをアラート表示するパネル。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QTableView,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QSortFilterProxyModel

if TYPE_CHECKING:
    from hils_manager.services.resource_service import ResourceService


class ResourcePanel(QWidget):
    """リソース配置パネル."""

    def __init__(self, resource_service: ResourceService | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._resource_service: ResourceService | None = None
        self._model = None
        self._proxy_model: QSortFilterProxyModel | None = None

        self._setup_ui()

        if resource_service is not None:
            self.set_service(resource_service)

    # ------------------------------------------------------------------
    # UI構築
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # --- ヘッダー行 ---
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        title = QLabel("リソース配置")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # --- アラートセクション ---
        self._alert_frame = QFrame()
        self._alert_frame.setObjectName("resourceAlertFrame")
        self._alert_frame.setVisible(False)

        alert_layout = QVBoxLayout(self._alert_frame)
        alert_layout.setContentsMargins(12, 8, 12, 8)
        alert_layout.setSpacing(4)

        self._alert_title = QLabel("未アサインOSメンバー")
        self._alert_title.setStyleSheet("font-weight: bold; font-size: 13px;")
        alert_layout.addWidget(self._alert_title)

        self._alert_detail = QLabel("")
        self._alert_detail.setWordWrap(True)
        self._alert_detail.setStyleSheet("font-size: 12px;")
        alert_layout.addWidget(self._alert_detail)

        layout.addWidget(self._alert_frame)

        # --- テーブルビュー ---
        self._table_view = QTableView()
        self._table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._table_view.setAlternatingRowColors(True)
        self._table_view.setSortingEnabled(True)
        self._table_view.horizontalHeader().setStretchLastSection(True)
        self._table_view.verticalHeader().setVisible(False)
        layout.addWidget(self._table_view, 1)

    # ------------------------------------------------------------------
    # サービス注入
    # ------------------------------------------------------------------

    def set_service(self, resource_service: ResourceService) -> None:
        """サービスを注入し、ViewModelを生成する."""
        from hils_manager.viewmodels import ResourceOverviewModel

        self._resource_service = resource_service
        self._model = ResourceOverviewModel(resource_service)

        self._proxy_model = QSortFilterProxyModel(self)
        self._proxy_model.setSourceModel(self._model)
        self._proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy_model.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self._table_view.setModel(self._proxy_model)

        self._update_alert()

    # ------------------------------------------------------------------
    # アラート更新
    # ------------------------------------------------------------------

    def _update_alert(self) -> None:
        """未アサインOSメンバーのアラートを更新する."""
        if self._resource_service is None:
            self._alert_frame.setVisible(False)
            return

        unassigned = self._resource_service.get_unassigned_outsourced_members()
        if not unassigned:
            self._alert_frame.setVisible(False)
            return

        self._alert_frame.setVisible(True)

        # メンバー数に応じて色を変更
        count = len(unassigned)
        if count >= 3:
            bg_color = "#ffcdd2"  # 赤系
            border_color = "#e57373"
        else:
            bg_color = "#fff9c4"  # 黄色系
            border_color = "#fff176"

        self._alert_frame.setStyleSheet(
            f"QFrame#resourceAlertFrame {{"
            f"  background-color: {bg_color};"
            f"  border: 1px solid {border_color};"
            f"  border-radius: 4px;"
            f"}}"
        )

        names = [m.name for m in unassigned]
        self._alert_title.setText(f"未アサインOSメンバー ({count}名)")
        self._alert_detail.setText("、".join(names))

    # ------------------------------------------------------------------
    # 公開メソッド
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """データを再読み込みする."""
        if self._model is not None:
            self._model.refresh()
        self._update_alert()
