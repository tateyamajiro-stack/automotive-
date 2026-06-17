"""プロセステーラリングダイアログ."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from hils_manager.models.process_definition import ProcessSelection


class ProcessSelectionDialog(QDialog):
    """プロセステーラリングダイアログ.

    プロジェクトに適用するプロセスの選択・省略理由を管理する。
    """

    def __init__(
        self,
        selections: list[ProcessSelection],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._selections = selections

        self.setWindowTitle("プロセステーラリング")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        self._setup_ui()
        self._populate()

    # ------------------------------------------------------------------
    # UI構築
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # テーブル
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["プロセス", "実施", "省略理由"])
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self._table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        layout.addWidget(self._table, 1)

        # ボタン
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)
        layout.addWidget(self._button_box)

    # ------------------------------------------------------------------
    # データ入出力
    # ------------------------------------------------------------------

    def _populate(self) -> None:
        """選択肢データをテーブルにセットする."""
        self._table.setRowCount(len(self._selections))
        self._checkboxes: list[QCheckBox] = []
        self._reason_edits: list[QLineEdit] = []

        for row, sel in enumerate(self._selections):
            # プロセス名 (読み取り専用)
            name_item = QTableWidgetItem(sel.process_name_ja or "")
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(row, 0, name_item)

            # 実施チェックボックス
            checkbox = QCheckBox()
            checkbox.setChecked(sel.is_selected)
            checkbox.toggled.connect(lambda checked, r=row: self._on_check_toggled(r, checked))
            self._checkboxes.append(checkbox)
            self._table.setCellWidget(row, 1, checkbox)

            # 省略理由
            reason_edit = QLineEdit()
            reason_edit.setText(sel.skip_reason)
            reason_edit.setPlaceholderText("省略する場合は理由を入力")
            reason_edit.setEnabled(not sel.is_selected)
            self._reason_edits.append(reason_edit)
            self._table.setCellWidget(row, 2, reason_edit)

    def _on_check_toggled(self, row: int, checked: bool) -> None:
        """実施チェック変更時に省略理由フィールドの有効/無効を切替."""
        self._reason_edits[row].setEnabled(not checked)
        if checked:
            self._reason_edits[row].clear()

    def get_selections(self) -> list[ProcessSelection]:
        """テーブルの現在の状態からProcessSelectionリストを返す."""
        result: list[ProcessSelection] = []
        for row, sel in enumerate(self._selections):
            updated = ProcessSelection(
                id=sel.id,
                project_id=sel.project_id,
                process_def_id=sel.process_def_id,
                is_selected=self._checkboxes[row].isChecked(),
                skip_reason=self._reason_edits[row].text().strip() if not self._checkboxes[row].isChecked() else "",
                process_name_ja=sel.process_name_ja,
            )
            result.append(updated)
        return result
