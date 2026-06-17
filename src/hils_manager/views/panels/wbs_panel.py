"""WBSパネル.

WBS (Work Breakdown Structure) のツリー表示・追加・編集・削除を行うパネル。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from hils_manager.repositories.wbs_repo import WBSRepository


class WBSPanel(QWidget):
    """WBSパネル."""

    def __init__(self, wbs_repo: WBSRepository | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._wbs_repo: WBSRepository | None = wbs_repo
        self._model = None
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

        title = QLabel("WBS")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self._btn_add = QPushButton("追加")
        self._btn_add.clicked.connect(self._on_add)
        header_layout.addWidget(self._btn_add)

        self._btn_add_child = QPushButton("子項目追加")
        self._btn_add_child.setEnabled(False)
        self._btn_add_child.clicked.connect(self._on_add_child)
        header_layout.addWidget(self._btn_add_child)

        self._btn_edit = QPushButton("編集")
        self._btn_edit.setEnabled(False)
        self._btn_edit.clicked.connect(self._on_edit)
        header_layout.addWidget(self._btn_edit)

        self._btn_delete = QPushButton("削除")
        self._btn_delete.setEnabled(False)
        self._btn_delete.clicked.connect(self._on_delete)
        header_layout.addWidget(self._btn_delete)

        layout.addLayout(header_layout)

        # --- ツリービュー ---
        self._tree_view = QTreeView()
        self._tree_view.setAlternatingRowColors(True)
        self._tree_view.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self._tree_view.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self._tree_view.setUniformRowHeights(True)
        self._tree_view.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self._tree_view, 1)

    # ------------------------------------------------------------------
    # プロジェクト設定
    # ------------------------------------------------------------------

    def set_project(self, project_id: int) -> None:
        """プロジェクトIDを設定し、WBSツリーを読み込む."""
        from hils_manager.viewmodels import WBSTreeModel

        self._project_id = project_id
        if self._wbs_repo is None:
            return

        self._model = WBSTreeModel(self._wbs_repo, project_id)
        self._tree_view.setModel(self._model)

        # カラムヘッダーの表示名はモデル側で設定されている想定
        # WBSコード, タイトル, ステータス, 担当者, 開始予定, 終了予定, 予定工数
        self._tree_view.expandAll()

        # 列幅の調整
        for col in range(self._tree_view.model().columnCount()):
            self._tree_view.resizeColumnToContents(col)

        self._tree_view.selectionModel().selectionChanged.connect(
            self._on_selection_changed
        )

    # ------------------------------------------------------------------
    # スロット
    # ------------------------------------------------------------------

    def _on_selection_changed(self) -> None:
        """行選択変更時にボタンの有効/無効を切り替え."""
        has_selection = self._tree_view.selectionModel().hasSelection()
        self._btn_add_child.setEnabled(has_selection)
        self._btn_edit.setEnabled(has_selection)
        self._btn_delete.setEnabled(has_selection)

    def _on_double_click(self, index) -> None:
        """行ダブルクリック時に編集ダイアログを開く."""
        self._on_edit()

    def _on_add(self) -> None:
        """追加ボタン押下."""
        pass

    def _on_add_child(self) -> None:
        """子項目追加ボタン押下."""
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
            self._tree_view.expandAll()
