"""WBS項目追加・編集ダイアログ."""

from __future__ import annotations

from datetime import date
from typing import Optional

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from hils_manager.constants import WBSStatus
from hils_manager.models.team_member import TeamMember
from hils_manager.models.wbs import WBSItem


class WBSDialog(QDialog):
    """WBS項目の追加・編集ダイアログ."""

    def __init__(
        self,
        wbs_item: Optional[WBSItem] = None,
        wbs_code: str = "",
        members: Optional[list[TeamMember]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._wbs_item = wbs_item
        self._is_edit = wbs_item is not None
        self._members = members or []

        self.setWindowTitle("WBS項目編集" if self._is_edit else "WBS項目追加")
        self.setMinimumWidth(520)

        self._setup_ui()

        if self._is_edit and wbs_item is not None:
            self._populate(wbs_item)
        elif wbs_code:
            self._wbs_code_edit.setText(wbs_code)

    # ------------------------------------------------------------------
    # UI構築
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # WBSコード
        self._wbs_code_edit = QLineEdit()
        self._wbs_code_edit.setReadOnly(not self._is_edit)
        self._wbs_code_edit.setPlaceholderText("自動生成")
        form.addRow("WBSコード:", self._wbs_code_edit)

        # タイトル
        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("作業項目名を入力")
        form.addRow("タイトル:", self._title_edit)

        # 説明
        self._description_edit = QTextEdit()
        self._description_edit.setFixedHeight(72)
        form.addRow("説明:", self._description_edit)

        # ステータス
        self._status_combo = QComboBox()
        for status in WBSStatus:
            self._status_combo.addItem(status.label, status)
        form.addRow("ステータス:", self._status_combo)

        # 担当者
        self._assignee_combo = QComboBox()
        self._assignee_combo.addItem("(未割当)", None)
        for member in self._members:
            display = f"{member.employee_id} - {member.name}"
            self._assignee_combo.addItem(display, member.id)
        form.addRow("担当者:", self._assignee_combo)

        # 開始予定日
        self._planned_start_edit = QDateEdit()
        self._planned_start_edit.setCalendarPopup(True)
        self._planned_start_edit.setDisplayFormat("yyyy/MM/dd")
        self._planned_start_edit.setDate(QDate.currentDate())
        form.addRow("開始予定日:", self._planned_start_edit)

        # 終了予定日
        self._planned_end_edit = QDateEdit()
        self._planned_end_edit.setCalendarPopup(True)
        self._planned_end_edit.setDisplayFormat("yyyy/MM/dd")
        self._planned_end_edit.setDate(QDate.currentDate().addMonths(1))
        form.addRow("終了予定日:", self._planned_end_edit)

        # 予定工数
        self._planned_hours_spin = QDoubleSpinBox()
        self._planned_hours_spin.setRange(0, 99999)
        self._planned_hours_spin.setDecimals(1)
        self._planned_hours_spin.setSuffix(" 人時")
        form.addRow("予定工数(人時):", self._planned_hours_spin)

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

    def _populate(self, wbs_item: WBSItem) -> None:
        """既存WBS項目データをフォームにセットする."""
        self._wbs_code_edit.setText(wbs_item.wbs_code)
        self._title_edit.setText(wbs_item.title)
        self._description_edit.setPlainText(wbs_item.description)

        for i in range(self._status_combo.count()):
            if self._status_combo.itemData(i) == wbs_item.status:
                self._status_combo.setCurrentIndex(i)
                break

        # 担当者の選択
        if wbs_item.assigned_to is not None:
            for i in range(self._assignee_combo.count()):
                if self._assignee_combo.itemData(i) == wbs_item.assigned_to:
                    self._assignee_combo.setCurrentIndex(i)
                    break

        if wbs_item.planned_start is not None:
            self._planned_start_edit.setDate(
                QDate(wbs_item.planned_start.year, wbs_item.planned_start.month, wbs_item.planned_start.day)
            )
        if wbs_item.planned_end is not None:
            self._planned_end_edit.setDate(
                QDate(wbs_item.planned_end.year, wbs_item.planned_end.month, wbs_item.planned_end.day)
            )
        if wbs_item.planned_hours is not None:
            self._planned_hours_spin.setValue(wbs_item.planned_hours)

    @staticmethod
    def _qdate_to_date(qdate: QDate) -> date:
        return date(qdate.year(), qdate.month(), qdate.day())

    def get_wbs_item(self) -> WBSItem:
        """フォーム値からWBSItemオブジェクトを生成して返す."""
        assigned_to: int | None = self._assignee_combo.currentData()

        hours_val = self._planned_hours_spin.value()
        planned_hours: float | None = hours_val if hours_val > 0 else None

        return WBSItem(
            id=self._wbs_item.id if self._wbs_item else None,
            project_id=self._wbs_item.project_id if self._wbs_item else 0,
            parent_id=self._wbs_item.parent_id if self._wbs_item else None,
            wbs_code=self._wbs_code_edit.text().strip(),
            title=self._title_edit.text().strip(),
            description=self._description_edit.toPlainText().strip(),
            assigned_to=assigned_to,
            status=self._status_combo.currentData(),
            planned_start=self._qdate_to_date(self._planned_start_edit.date()),
            planned_end=self._qdate_to_date(self._planned_end_edit.date()),
            actual_start=self._wbs_item.actual_start if self._wbs_item else None,
            actual_end=self._wbs_item.actual_end if self._wbs_item else None,
            planned_hours=planned_hours,
            sort_order=self._wbs_item.sort_order if self._wbs_item else 0,
            jira_issue_key=self._wbs_item.jira_issue_key if self._wbs_item else None,
            created_at=self._wbs_item.created_at if self._wbs_item else None,
            updated_at=self._wbs_item.updated_at if self._wbs_item else None,
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
