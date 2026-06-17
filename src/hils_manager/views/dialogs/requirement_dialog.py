"""要望追加・編集ダイアログ."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from hils_manager.constants import RequirementPriority, RequirementStatus
from hils_manager.models.requirement import Requirement


class RequirementDialog(QDialog):
    """要望の追加・編集ダイアログ."""

    def __init__(
        self,
        requirement: Optional[Requirement] = None,
        req_number: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._requirement = requirement
        self._is_edit = requirement is not None

        self.setWindowTitle("要望編集" if self._is_edit else "要望追加")
        self.setMinimumWidth(520)

        self._setup_ui()

        if self._is_edit and requirement is not None:
            self._populate(requirement)
        elif req_number:
            self._req_number_edit.setText(req_number)

    # ------------------------------------------------------------------
    # UI構築
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # 要望番号
        self._req_number_edit = QLineEdit()
        self._req_number_edit.setReadOnly(not self._is_edit)
        self._req_number_edit.setPlaceholderText("自動生成")
        form.addRow("要望番号:", self._req_number_edit)

        # タイトル
        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("要望のタイトルを入力")
        form.addRow("タイトル:", self._title_edit)

        # 説明
        self._description_edit = QTextEdit()
        self._description_edit.setFixedHeight(120)
        form.addRow("説明:", self._description_edit)

        # 優先度
        self._priority_combo = QComboBox()
        for priority in RequirementPriority:
            self._priority_combo.addItem(priority.label, priority)
        form.addRow("優先度:", self._priority_combo)

        # ステータス
        self._status_combo = QComboBox()
        for status in RequirementStatus:
            self._status_combo.addItem(status.label, status)
        form.addRow("ステータス:", self._status_combo)

        # 要望元
        self._requested_by_edit = QLineEdit()
        self._requested_by_edit.setPlaceholderText("例: 顧客名 / 社内部署")
        form.addRow("要望元:", self._requested_by_edit)

        # 対象バージョン
        self._target_version_edit = QLineEdit()
        self._target_version_edit.setPlaceholderText("例: v1.0")
        form.addRow("対象バージョン:", self._target_version_edit)

        layout.addLayout(form)

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

    def _populate(self, requirement: Requirement) -> None:
        """既存要望データをフォームにセットする."""
        self._req_number_edit.setText(requirement.req_number)
        self._title_edit.setText(requirement.title)
        self._description_edit.setPlainText(requirement.description)

        for i in range(self._priority_combo.count()):
            if self._priority_combo.itemData(i) == requirement.priority:
                self._priority_combo.setCurrentIndex(i)
                break

        for i in range(self._status_combo.count()):
            if self._status_combo.itemData(i) == requirement.status:
                self._status_combo.setCurrentIndex(i)
                break

        self._requested_by_edit.setText(requirement.requested_by)
        self._target_version_edit.setText(requirement.target_version)

    def get_requirement(self) -> Requirement:
        """フォーム値からRequirementオブジェクトを生成して返す."""
        return Requirement(
            id=self._requirement.id if self._requirement else None,
            project_id=self._requirement.project_id if self._requirement else 0,
            req_number=self._req_number_edit.text().strip(),
            title=self._title_edit.text().strip(),
            description=self._description_edit.toPlainText().strip(),
            priority=self._priority_combo.currentData(),
            status=self._status_combo.currentData(),
            requested_by=self._requested_by_edit.text().strip(),
            target_version=self._target_version_edit.text().strip(),
            created_at=self._requirement.created_at if self._requirement else None,
            updated_at=self._requirement.updated_at if self._requirement else None,
        )

    # ------------------------------------------------------------------
    # バリデーション
    # ------------------------------------------------------------------

    def accept(self) -> None:
        """OKボタン押下時のバリデーション."""
        if not self._title_edit.text().strip():
            QMessageBox.warning(self, "入力エラー", "タイトルは必須です。")
            self._title_edit.setFocus()
            return
        super().accept()
