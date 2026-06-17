"""見積追加・編集ダイアログおよび工数入力ダイアログ."""

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
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from hils_manager.constants import EstimateType
from hils_manager.models.estimate import Estimate, TimeEntry
from hils_manager.models.team_member import TeamMember
from hils_manager.models.wbs import WBSItem


# ======================================================================
# EstimateDialog
# ======================================================================


class EstimateDialog(QDialog):
    """見積の追加・編集ダイアログ."""

    def __init__(
        self,
        estimate: Optional[Estimate] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._estimate = estimate
        self._is_edit = estimate is not None

        self.setWindowTitle("見積編集" if self._is_edit else "見積追加")
        self.setMinimumWidth(480)

        self._setup_ui()

        if self._is_edit and estimate is not None:
            self._populate(estimate)

    # ------------------------------------------------------------------
    # UI構築
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # 見積種別
        self._type_combo = QComboBox()
        for et in EstimateType:
            self._type_combo.addItem(et.label, et)
        form.addRow("見積種別:", self._type_combo)

        # 工数(人時)
        self._man_hours_spin = QDoubleSpinBox()
        self._man_hours_spin.setRange(0, 99999)
        self._man_hours_spin.setDecimals(1)
        self._man_hours_spin.setSuffix(" 人時")
        form.addRow("工数(人時):", self._man_hours_spin)

        # リードタイム(日)
        self._lead_time_spin = QSpinBox()
        self._lead_time_spin.setRange(0, 9999)
        self._lead_time_spin.setSuffix(" 日")
        form.addRow("リードタイム(日):", self._lead_time_spin)

        # 前提条件
        self._assumptions_edit = QTextEdit()
        self._assumptions_edit.setFixedHeight(72)
        form.addRow("前提条件:", self._assumptions_edit)

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

    def _populate(self, estimate: Estimate) -> None:
        """既存見積データをフォームにセットする."""
        for i in range(self._type_combo.count()):
            if self._type_combo.itemData(i) == estimate.estimate_type:
                self._type_combo.setCurrentIndex(i)
                break

        self._man_hours_spin.setValue(estimate.man_hours)
        if estimate.lead_time_days is not None:
            self._lead_time_spin.setValue(estimate.lead_time_days)
        self._assumptions_edit.setPlainText(estimate.assumptions)

    def get_estimate(self) -> Estimate:
        """フォーム値からEstimateオブジェクトを生成して返す."""
        lead_time_val = self._lead_time_spin.value()
        lead_time: int | None = lead_time_val if lead_time_val > 0 else None

        return Estimate(
            id=self._estimate.id if self._estimate else None,
            project_id=self._estimate.project_id if self._estimate else 0,
            wbs_item_id=self._estimate.wbs_item_id if self._estimate else None,
            estimate_type=self._type_combo.currentData(),
            man_hours=self._man_hours_spin.value(),
            lead_time_days=lead_time,
            estimator_id=self._estimate.estimator_id if self._estimate else None,
            assumptions=self._assumptions_edit.toPlainText().strip(),
            created_at=self._estimate.created_at if self._estimate else None,
        )


# ======================================================================
# TimeEntryDialog
# ======================================================================


class TimeEntryDialog(QDialog):
    """工数入力ダイアログ."""

    def __init__(
        self,
        members: Optional[list[TeamMember]] = None,
        wbs_items: Optional[list[WBSItem]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._members = members or []
        self._wbs_items = wbs_items or []

        self.setWindowTitle("工数入力")
        self.setMinimumWidth(480)

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI構築
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # 作業日
        self._work_date_edit = QDateEdit()
        self._work_date_edit.setCalendarPopup(True)
        self._work_date_edit.setDisplayFormat("yyyy/MM/dd")
        self._work_date_edit.setDate(QDate.currentDate())
        form.addRow("作業日:", self._work_date_edit)

        # 担当者
        self._member_combo = QComboBox()
        for member in self._members:
            display = f"{member.employee_id} - {member.name}"
            self._member_combo.addItem(display, member.id)
        form.addRow("担当者:", self._member_combo)

        # WBS
        self._wbs_combo = QComboBox()
        self._wbs_combo.addItem("(なし)", None)
        for item in self._wbs_items:
            display = f"{item.wbs_code} - {item.title}"
            self._wbs_combo.addItem(display, item.id)
        form.addRow("WBS:", self._wbs_combo)

        # 工数(時間)
        self._hours_spin = QDoubleSpinBox()
        self._hours_spin.setRange(0, 24)
        self._hours_spin.setSingleStep(0.5)
        self._hours_spin.setDecimals(1)
        self._hours_spin.setSuffix(" 時間")
        form.addRow("工数(時間):", self._hours_spin)

        # 内容
        self._description_edit = QLineEdit()
        self._description_edit.setPlaceholderText("作業内容を入力")
        form.addRow("内容:", self._description_edit)

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

    @staticmethod
    def _qdate_to_date(qdate: QDate) -> date:
        return date(qdate.year(), qdate.month(), qdate.day())

    def get_time_entry(self) -> TimeEntry:
        """フォーム値からTimeEntryオブジェクトを生成して返す."""
        wbs_item_id: int | None = self._wbs_combo.currentData()
        member_id: int = self._member_combo.currentData()

        return TimeEntry(
            project_id=0,
            wbs_item_id=wbs_item_id,
            member_id=member_id if member_id is not None else 0,
            work_date=self._qdate_to_date(self._work_date_edit.date()),
            hours=self._hours_spin.value(),
            description=self._description_edit.text().strip(),
        )
