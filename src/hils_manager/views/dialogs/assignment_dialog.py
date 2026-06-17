"""メンバーアサインダイアログ."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from hils_manager.constants import ProjectRole
from hils_manager.models.team_member import TeamMember


class AssignmentDialog(QDialog):
    """プロジェクトへのメンバーアサインダイアログ."""

    def __init__(
        self,
        members: list[TeamMember],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._members = members

        self.setWindowTitle("メンバーアサイン")
        self.setMinimumWidth(420)

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI構築
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # メンバー
        self._member_combo = QComboBox()
        for member in self._members:
            display = f"{member.employee_id} - {member.name}"
            self._member_combo.addItem(display, member.id)
        form.addRow("メンバー:", self._member_combo)

        # 役割
        self._role_combo = QComboBox()
        for role in ProjectRole:
            self._role_combo.addItem(role.label, role)
        form.addRow("役割:", self._role_combo)

        # アサイン率
        self._allocation_spin = QSpinBox()
        self._allocation_spin.setRange(0, 100)
        self._allocation_spin.setValue(100)
        self._allocation_spin.setSuffix(" %")
        form.addRow("アサイン率(%):", self._allocation_spin)

        layout.addLayout(form)

        # ボタン
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)
        layout.addWidget(self._button_box)

    # ------------------------------------------------------------------
    # データ取得
    # ------------------------------------------------------------------

    def get_assignment(self) -> tuple[int, ProjectRole, float]:
        """選択内容を返す: (member_id, role, allocation_pct)."""
        member_id: int = self._member_combo.currentData()
        role: ProjectRole = self._role_combo.currentData()
        allocation_pct: float = float(self._allocation_spin.value())
        return member_id, role, allocation_pct
