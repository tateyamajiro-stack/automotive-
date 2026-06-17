"""リスク管理パネル.

プロジェクトリスクの一覧表示・追加・編集・削除・サマリ表示を行うパネル。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QSortFilterProxyModel

if TYPE_CHECKING:
    from hils_manager.services.risk_service import RiskService


class RiskPanel(QWidget):
    """リスク管理パネル."""

    def __init__(self, risk_service: RiskService | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._risk_service: RiskService | None = risk_service
        self._model = None
        self._proxy_model: QSortFilterProxyModel | None = None
        self._project_id: int | None = None

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI構築
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # --- 左側: リスク一覧 ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # ヘッダー行
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        title = QLabel("リスク管理")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self._btn_add = QPushButton("追加")
        self._btn_add.clicked.connect(self._on_add)
        header_layout.addWidget(self._btn_add)

        self._btn_edit = QPushButton("編集")
        self._btn_edit.setEnabled(False)
        self._btn_edit.clicked.connect(self._on_edit)
        header_layout.addWidget(self._btn_edit)

        self._btn_delete = QPushButton("削除")
        self._btn_delete.setEnabled(False)
        self._btn_delete.clicked.connect(self._on_delete)
        header_layout.addWidget(self._btn_delete)

        left_layout.addLayout(header_layout)

        # 検索バー
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        search_label = QLabel("検索:")
        search_layout.addWidget(search_label)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("タイトルで絞り込み...")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.textChanged.connect(self._on_filter_changed)
        search_layout.addWidget(self._search_input)

        left_layout.addLayout(search_layout)

        # テーブルビュー
        self._table_view = QTableView()
        self._table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._table_view.setAlternatingRowColors(True)
        self._table_view.setSortingEnabled(True)
        self._table_view.horizontalHeader().setStretchLastSection(True)
        self._table_view.verticalHeader().setVisible(False)
        self._table_view.doubleClicked.connect(self._on_double_click)
        left_layout.addWidget(self._table_view, 1)

        main_layout.addWidget(left_widget, 3)

        # --- 右側: リスクサマリ ---
        self._summary_group = QGroupBox("リスクサマリ")
        summary_layout = QVBoxLayout(self._summary_group)
        summary_layout.setSpacing(12)

        self._lbl_total = QLabel("合計: —")
        self._lbl_total.setStyleSheet("font-size: 14px;")
        summary_layout.addWidget(self._lbl_total)

        self._lbl_open = QLabel("未対応: —")
        self._lbl_open.setStyleSheet("font-size: 14px;")
        summary_layout.addWidget(self._lbl_open)

        self._lbl_high = QLabel("高リスク: —")
        self._lbl_high.setStyleSheet("font-size: 14px; color: #d32f2f; font-weight: bold;")
        summary_layout.addWidget(self._lbl_high)

        self._lbl_resolved = QLabel("解決済: —")
        self._lbl_resolved.setStyleSheet("font-size: 14px; color: #388e3c;")
        summary_layout.addWidget(self._lbl_resolved)

        summary_layout.addStretch()

        main_layout.addWidget(self._summary_group, 1)

    # ------------------------------------------------------------------
    # プロジェクト設定
    # ------------------------------------------------------------------

    def set_project(self, project_id: int) -> None:
        """プロジェクトIDを設定し、リスクデータを読み込む."""
        from hils_manager.viewmodels import RiskTableModel

        self._project_id = project_id
        if self._risk_service is None:
            return

        self._model = RiskTableModel(self._risk_service, project_id)

        self._proxy_model = QSortFilterProxyModel(self)
        self._proxy_model.setSourceModel(self._model)
        self._proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy_model.setFilterKeyColumn(2)  # タイトル列でフィルタリング

        self._table_view.setModel(self._proxy_model)
        self._table_view.selectionModel().selectionChanged.connect(
            self._on_selection_changed
        )

        self._update_summary()

    # ------------------------------------------------------------------
    # サマリ更新
    # ------------------------------------------------------------------

    def _update_summary(self) -> None:
        """リスクサマリを更新する."""
        if self._risk_service is None or self._project_id is None:
            return

        summary = self._risk_service.get_risk_summary(self._project_id)
        self._lbl_total.setText(f"合計: {summary.get('total', 0)}")
        self._lbl_open.setText(f"未対応: {summary.get('open', 0)}")
        self._lbl_high.setText(f"高リスク: {summary.get('high_risk_count', 0)}")
        self._lbl_resolved.setText(f"解決済: {summary.get('resolved', 0)}")

    # ------------------------------------------------------------------
    # スロット
    # ------------------------------------------------------------------

    def _on_filter_changed(self, text: str) -> None:
        """検索テキスト変更時のフィルタリング."""
        if self._proxy_model is not None:
            self._proxy_model.setFilterFixedString(text)

    def _on_selection_changed(self) -> None:
        """行選択変更時にボタンの有効/無効を切り替え."""
        has_selection = self._table_view.selectionModel().hasSelection()
        self._btn_edit.setEnabled(has_selection)
        self._btn_delete.setEnabled(has_selection)

    def _on_double_click(self, index) -> None:
        """行ダブルクリック時に編集ダイアログを開く."""
        self._on_edit()

    def _on_add(self) -> None:
        """追加ボタン押下."""
        pass

    def _on_edit(self) -> None:
        """編集ボタン押下."""
        pass

    def _on_delete(self) -> None:
        """削除ボタン押下."""
        pass

    def refresh(self) -> None:
        """データを再読み込みする."""
        if self._model is not None:
            self._model.refresh()
        self._update_summary()
