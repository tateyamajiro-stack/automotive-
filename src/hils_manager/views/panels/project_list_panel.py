"""案件一覧パネル.

プロジェクトの一覧表示・新規作成・ステータスフィルタリングを行うパネル。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QSortFilterProxyModel

if TYPE_CHECKING:
    from hils_manager.services.project_service import ProjectService


# ステータスフィルタの選択肢
_STATUS_FILTERS: list[tuple[str, str]] = [
    ("全て", ""),
    ("計画中", "計画中"),
    ("実行中", "実行中"),
    ("保留", "保留"),
    ("完了", "完了"),
    ("中止", "中止"),
]


class ProjectListPanel(QWidget):
    """案件一覧パネル."""

    project_selected = Signal(int)

    def __init__(self, project_service: ProjectService | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project_service: ProjectService | None = None
        self._model = None
        self._proxy_model: QSortFilterProxyModel | None = None

        self._setup_ui()

        if project_service is not None:
            self.set_service(project_service)

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

        title = QLabel("案件一覧")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # ステータスフィルタ
        filter_label = QLabel("ステータス:")
        header_layout.addWidget(filter_label)

        self._status_combo = QComboBox()
        for display_text, _value in _STATUS_FILTERS:
            self._status_combo.addItem(display_text)
        self._status_combo.currentIndexChanged.connect(self._on_status_filter_changed)
        header_layout.addWidget(self._status_combo)

        self._btn_new = QPushButton("新規案件")
        self._btn_new.clicked.connect(self._on_add)
        header_layout.addWidget(self._btn_new)

        layout.addLayout(header_layout)

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
    # サービス注入
    # ------------------------------------------------------------------

    def set_service(self, project_service: ProjectService) -> None:
        """サービスを注入し、ViewModelを生成する."""
        from hils_manager.viewmodels import ProjectListModel

        self._project_service = project_service
        self._model = ProjectListModel(project_service)

        self._proxy_model = QSortFilterProxyModel(self)
        self._proxy_model.setSourceModel(self._model)
        self._proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self._table_view.setModel(self._proxy_model)
        self._table_view.selectionModel().selectionChanged.connect(
            self._on_selection_changed
        )

    # ------------------------------------------------------------------
    # スロット
    # ------------------------------------------------------------------

    def _on_status_filter_changed(self, index: int) -> None:
        """ステータスフィルタ変更時."""
        if self._proxy_model is None:
            return
        _display, filter_value = _STATUS_FILTERS[index]
        if filter_value:
            self._proxy_model.setFilterFixedString(filter_value)
        else:
            self._proxy_model.setFilterFixedString("")

    def _on_selection_changed(self) -> None:
        """行選択変更時."""
        pass

    def _on_double_click(self, index) -> None:
        """行ダブルクリック時にプロジェクト詳細画面へ遷移."""
        source_index = self._proxy_model.mapToSource(index) if self._proxy_model else index
        row = source_index.row()
        if self._model is not None:
            project = self._model.get_project(row)
            if project and project.id is not None:
                self.project_selected.emit(project.id)

    def _on_add(self) -> None:
        """新規案件ボタン押下."""
        pass

    def refresh(self) -> None:
        """データを再読み込みする."""
        if self._model is not None:
            self._model.refresh()
