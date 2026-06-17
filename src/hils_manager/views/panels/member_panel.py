"""メンバー管理パネル.

チームメンバーの一覧表示・追加・編集・無効化を行うCRUDパネル。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
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
    from hils_manager.services.resource_service import ResourceService


class MemberPanel(QWidget):
    """メンバー管理パネル."""

    member_add_requested = Signal()
    member_edit_requested = Signal(int)

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

        title = QLabel("メンバー管理")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self._btn_add = QPushButton("メンバー追加")
        self._btn_add.clicked.connect(self._on_add)
        header_layout.addWidget(self._btn_add)

        self._btn_edit = QPushButton("編集")
        self._btn_edit.setEnabled(False)
        self._btn_edit.clicked.connect(self._on_edit)
        header_layout.addWidget(self._btn_edit)

        self._btn_deactivate = QPushButton("無効化")
        self._btn_deactivate.setEnabled(False)
        self._btn_deactivate.clicked.connect(self._on_deactivate)
        header_layout.addWidget(self._btn_deactivate)

        layout.addLayout(header_layout)

        # --- 検索バー ---
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        search_label = QLabel("検索:")
        search_layout.addWidget(search_label)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("名前で絞り込み...")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.textChanged.connect(self._on_filter_changed)
        search_layout.addWidget(self._search_input)

        layout.addLayout(search_layout)

        # --- テーブルビュー ---
        self._table_view = QTableView()
        self._table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._table_view.setAlternatingRowColors(True)
        self._table_view.setSortingEnabled(True)
        self._table_view.horizontalHeader().setStretchLastSection(True)
        self._table_view.verticalHeader().setVisible(False)
        self._table_view.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self._table_view, 1)

        # --- ステータスバー ---
        self._status_label = QLabel("メンバー数: 0  |  OS数: 0")
        self._status_label.setStyleSheet("color: #666; font-size: 12px; padding: 4px;")
        layout.addWidget(self._status_label)

    # ------------------------------------------------------------------
    # サービス注入
    # ------------------------------------------------------------------

    def set_service(self, resource_service: ResourceService) -> None:
        """サービスを注入し、ViewModelを生成する."""
        from hils_manager.viewmodels import MemberTableModel

        self._resource_service = resource_service
        self._model = MemberTableModel(resource_service)

        self._proxy_model = QSortFilterProxyModel(self)
        self._proxy_model.setSourceModel(self._model)
        self._proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy_model.setFilterKeyColumn(1)  # 名前列でフィルタリング

        self._table_view.setModel(self._proxy_model)
        self._table_view.selectionModel().selectionChanged.connect(
            self._on_selection_changed
        )

        self._update_status()

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
        self._btn_deactivate.setEnabled(has_selection)

    def _on_double_click(self, index) -> None:
        """行ダブルクリック時に編集ダイアログを開く."""
        source_index = self._proxy_model.mapToSource(index) if self._proxy_model else index
        row = source_index.row()
        if self._model is not None:
            member = self._model.get_member(row)
            if member and member.id is not None:
                self.member_edit_requested.emit(member.id)
                self._on_edit()

    def _on_add(self) -> None:
        """メンバー追加ボタン押下."""
        self.member_add_requested.emit()

    def _on_edit(self) -> None:
        """編集ボタン押下."""
        pass

    def _on_deactivate(self) -> None:
        """無効化ボタン押下."""
        pass

    # ------------------------------------------------------------------
    # ステータス更新
    # ------------------------------------------------------------------

    def _update_status(self) -> None:
        """ステータスラベルを更新する."""
        if self._model is None:
            return
        total = self._model.rowCount()
        os_count = 0
        for row in range(total):
            member = self._model.get_member(row)
            if member and member.is_outsourced:
                os_count += 1
        self._status_label.setText(f"メンバー数: {total}  |  OS数: {os_count}")

    def refresh(self) -> None:
        """データを再読み込みする."""
        if self._model is not None:
            self._model.refresh()
            self._update_status()
