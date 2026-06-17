"""メンバー追加・編集ダイアログ."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from hils_manager.models.team_member import TeamMember


class MemberDialog(QDialog):
    """チームメンバーの追加・編集ダイアログ."""

    def __init__(
        self,
        member: Optional[TeamMember] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._member = member
        self._is_edit = member is not None

        self.setWindowTitle("メンバー編集" if self._is_edit else "メンバー追加")
        self.setMinimumWidth(480)

        self._setup_ui()

        if self._is_edit and member is not None:
            self._populate(member)

    # ------------------------------------------------------------------
    # UI構築
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # 社員番号
        self._employee_id_edit = QLineEdit()
        self._employee_id_edit.setPlaceholderText("例: E001")
        form.addRow("社員番号:", self._employee_id_edit)

        # 氏名
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("例: 山田 太郎")
        form.addRow("氏名:", self._name_edit)

        # メール
        self._email_edit = QLineEdit()
        self._email_edit.setPlaceholderText("例: yamada@example.com")
        form.addRow("メール:", self._email_edit)

        # OS区分
        self._os_check = QCheckBox("外部委託(OS)メンバー")
        self._os_check.toggled.connect(self._on_os_toggled)
        form.addRow("OS区分:", self._os_check)

        # 日単価
        self._daily_rate_spin = QDoubleSpinBox()
        self._daily_rate_spin.setRange(0, 999999)
        self._daily_rate_spin.setDecimals(0)
        self._daily_rate_spin.setSuffix(" 円")
        self._daily_rate_spin.setEnabled(False)
        form.addRow("日単価:", self._daily_rate_spin)

        # スキル
        self._skills_edit = QLineEdit()
        self._skills_edit.setPlaceholderText("例: C, Python, MATLAB (カンマ区切り)")
        form.addRow("スキル:", self._skills_edit)

        layout.addLayout(form)

        # ボタン
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)
        layout.addWidget(self._button_box)

    # ------------------------------------------------------------------
    # スロット
    # ------------------------------------------------------------------

    def _on_os_toggled(self, checked: bool) -> None:
        """OS区分チェック変更時に日単価フィールドの有効/無効を切替."""
        self._daily_rate_spin.setEnabled(checked)
        if not checked:
            self._daily_rate_spin.setValue(0)

    # ------------------------------------------------------------------
    # データ入出力
    # ------------------------------------------------------------------

    def _populate(self, member: TeamMember) -> None:
        """既存メンバーデータをフォームにセットする."""
        self._employee_id_edit.setText(member.employee_id)
        self._name_edit.setText(member.name)
        self._email_edit.setText(member.email)
        self._os_check.setChecked(member.is_outsourced)
        if member.daily_rate is not None:
            self._daily_rate_spin.setValue(member.daily_rate)
        self._skills_edit.setText(", ".join(member.skills))

    def get_member(self) -> TeamMember:
        """フォーム値からTeamMemberオブジェクトを生成して返す."""
        skills_text = self._skills_edit.text().strip()
        skills = [s.strip() for s in skills_text.split(",") if s.strip()] if skills_text else []

        daily_rate: float | None = None
        if self._os_check.isChecked():
            daily_rate = self._daily_rate_spin.value()

        member = TeamMember(
            id=self._member.id if self._member else None,
            employee_id=self._employee_id_edit.text().strip(),
            name=self._name_edit.text().strip(),
            email=self._email_edit.text().strip(),
            is_outsourced=self._os_check.isChecked(),
            daily_rate=daily_rate,
            skills=skills,
            is_active=self._member.is_active if self._member else True,
            created_at=self._member.created_at if self._member else None,
            updated_at=self._member.updated_at if self._member else None,
        )
        return member

    # ------------------------------------------------------------------
    # バリデーション
    # ------------------------------------------------------------------

    def accept(self) -> None:
        """OKボタン押下時のバリデーション."""
        if not self._employee_id_edit.text().strip():
            QMessageBox.warning(self, "入力エラー", "社員番号は必須です。")
            self._employee_id_edit.setFocus()
            return
        if not self._name_edit.text().strip():
            QMessageBox.warning(self, "入力エラー", "氏名は必須です。")
            self._name_edit.setFocus()
            return
        super().accept()
