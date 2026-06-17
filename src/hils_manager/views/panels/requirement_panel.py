"""要望リストパネル.

プロジェクト要望の一覧表示・追加・編集・削除を行うCRUDパネル。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
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
    from hils_manager.repositories.requirement_repo import RequirementRepository


class RequirementPanel(QWidget):
    """要望リストパネル."""

    def __init__(self, requirement_repo: RequirementRepository | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._requirement_repo: RequirementRepository | None = requirement_repo
        self._model = None
        self._proxy_model: QSortFilterProxyModel | None = None
        self._project_id: int | None = None

        self._setup_ui()

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

        title = QLabel("要望リスト")
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

        layout.addLayout(header_layout)

        # --- 検索バー ---
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        search_label = QLabel("検索:")
        search_layout.addWidget(search_label)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("タイトルで絞り込み...")
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

    # ------------------------------------------------------------------
    # プロジェクト設定
    # ------------------------------------------------------------------

    def set_project(self, project_id: int) -> None:
        """プロジェクトIDを設定し、要望リストを読み込む."""
        from hils_manager.viewmodels import RequirementTableModel

        self._project_id = project_id
        if self._requirement_repo is None:
            return

        self._model = RequirementTableModel(self._requirement_repo, project_id)

        self._proxy_model = QSortFilterProxyModel(self)
        self._proxy_model.setSourceModel(self._model)
        self._proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy_model.setFilterKeyColumn(2)  # タイトル列でフィルタリング

        self._table_view.setModel(self._proxy_model)
        self._table_view.selectionModel().selectionChanged.connect(
            self._on_selection_changed
        )

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
