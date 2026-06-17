"""リスク追加・編集ダイアログ."""

from __future__ import annotations

from datetime import date
from typing import Optional

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from hils_manager.constants import RiskImpact, RiskProbability, RiskStatus
from hils_manager.models.risk import Risk
from hils_manager.models.team_member import TeamMember
from hils_manager.services.risk_service import RiskService

# 発生確率・影響度の日本語ラベル
_PROBABILITY_LABELS: dict[RiskProbability, str] = {
    RiskProbability.HIGH: "高",
    RiskProbability.MEDIUM: "中",
    RiskProbability.LOW: "低",
}

_IMPACT_LABELS: dict[RiskImpact, str] = {
    RiskImpact.HIGH: "高",
    RiskImpact.MEDIUM: "中",
    RiskImpact.LOW: "低",
}


class RiskDialog(QDialog):
    """リスクの追加・編集ダイアログ."""

    def __init__(
        self,
        risk: Optional[Risk] = None,
        risk_number: str = "",
        members: Optional[list[TeamMember]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._risk = risk
        self._is_edit = risk is not None
        self._members = members or []

        self.setWindowTitle("リスク編集" if self._is_edit else "リスク追加")
        self.setMinimumWidth(560)

        self._setup_ui()

        if self._is_edit and risk is not None:
            self._populate(risk)
        elif risk_number:
            self._risk_number_edit.setText(risk_number)

    # ------------------------------------------------------------------
    # UI構築
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # リスク番号
        self._risk_number_edit = QLineEdit()
        self._risk_number_edit.setReadOnly(not self._is_edit)
        self._risk_number_edit.setPlaceholderText("自動生成")
        form.addRow("リスク番号:", self._risk_number_edit)

        # タイトル
        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("リスクのタイトルを入力")
        form.addRow("タイトル:", self._title_edit)

        # 説明
        self._description_edit = QTextEdit()
        self._description_edit.setFixedHeight(72)
        form.addRow("説明:", self._description_edit)

        # 発生確率
        self._probability_combo = QComboBox()
        for prob in RiskProbability:
            self._probability_combo.addItem(_PROBABILITY_LABELS[prob], prob)
        form.addRow("発生確率:", self._probability_combo)

        # 影響度
        self._impact_combo = QComboBox()
        for imp in RiskImpact:
            self._impact_combo.addItem(_IMPACT_LABELS[imp], imp)
        form.addRow("影響度:", self._impact_combo)

        # 対策
        self._mitigation_edit = QTextEdit()
        self._mitigation_edit.setFixedHeight(120)
        self._mitigation_edit.setPlaceholderText("具体的な対策内容を記入してください")
        form.addRow("対策:", self._mitigation_edit)

        # 対策の注意書き
        mitigation_warning = QLabel("※ 対策は必須です。「TBD」「未定」等は使用できません。")
        mitigation_warning.setStyleSheet("color: red; font-size: 11px; padding-left: 2px;")
        form.addRow("", mitigation_warning)

        # ステータス
        self._status_combo = QComboBox()
        for status in RiskStatus:
            self._status_combo.addItem(status.label, status)
        form.addRow("ステータス:", self._status_combo)

        # 担当者
        self._owner_combo = QComboBox()
        self._owner_combo.addItem("(未割当)", None)
        for member in self._members:
            display = f"{member.employee_id} - {member.name}"
            self._owner_combo.addItem(display, member.id)
        form.addRow("担当者:", self._owner_combo)

        # 識別日
        self._identified_date_edit = QDateEdit()
        self._identified_date_edit.setCalendarPopup(True)
        self._identified_date_edit.setDisplayFormat("yyyy/MM/dd")
        self._identified_date_edit.setDate(QDate.currentDate())
        form.addRow("識別日:", self._identified_date_edit)

        # 目標解決日
        self._target_date_edit = QDateEdit()
        self._target_date_edit.setCalendarPopup(True)
        self._target_date_edit.setDisplayFormat("yyyy/MM/dd")
        self._target_date_edit.setDate(QDate.currentDate().addMonths(1))
        form.addRow("目標解決日:", self._target_date_edit)

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

    def _populate(self, risk: Risk) -> None:
        """既存リスクデータをフォームにセットする."""
        self._risk_number_edit.setText(risk.risk_number)
        self._title_edit.setText(risk.title)
        self._description_edit.setPlainText(risk.description)

        for i in range(self._probability_combo.count()):
            if self._probability_combo.itemData(i) == risk.probability:
                self._probability_combo.setCurrentIndex(i)
                break

        for i in range(self._impact_combo.count()):
            if self._impact_combo.itemData(i) == risk.impact:
                self._impact_combo.setCurrentIndex(i)
                break

        self._mitigation_edit.setPlainText(risk.mitigation)

        for i in range(self._status_combo.count()):
            if self._status_combo.itemData(i) == risk.status:
                self._status_combo.setCurrentIndex(i)
                break

        if risk.owner_id is not None:
            for i in range(self._owner_combo.count()):
                if self._owner_combo.itemData(i) == risk.owner_id:
                    self._owner_combo.setCurrentIndex(i)
                    break

        if risk.identified_date is not None:
            self._identified_date_edit.setDate(
                QDate(risk.identified_date.year, risk.identified_date.month, risk.identified_date.day)
            )
        if risk.target_date is not None:
            self._target_date_edit.setDate(
                QDate(risk.target_date.year, risk.target_date.month, risk.target_date.day)
            )

    @staticmethod
    def _qdate_to_date(qdate: QDate) -> date:
        return date(qdate.year(), qdate.month(), qdate.day())

    def get_risk(self) -> Risk:
        """フォーム値からRiskオブジェクトを生成して返す."""
        owner_id: int | None = self._owner_combo.currentData()

        return Risk(
            id=self._risk.id if self._risk else None,
            project_id=self._risk.project_id if self._risk else 0,
            risk_number=self._risk_number_edit.text().strip(),
            title=self._title_edit.text().strip(),
            description=self._description_edit.toPlainText().strip(),
            probability=self._probability_combo.currentData(),
            impact=self._impact_combo.currentData(),
            mitigation=self._mitigation_edit.toPlainText().strip(),
            status=self._status_combo.currentData(),
            owner_id=owner_id,
            identified_date=self._qdate_to_date(self._identified_date_edit.date()),
            target_date=self._qdate_to_date(self._target_date_edit.date()),
            resolution_date=self._risk.resolution_date if self._risk else None,
            created_at=self._risk.created_at if self._risk else None,
            updated_at=self._risk.updated_at if self._risk else None,
        )

    # ------------------------------------------------------------------
    # バリデーション
    # ------------------------------------------------------------------

    def accept(self) -> None:
        """OKボタン押下時のバリデーション.

        タイトルと対策内容を検証し、対策はRiskService.validate_mitigation()で
        プレースホルダー文言の使用を防止する。
        """
        if not self._title_edit.text().strip():
            QMessageBox.warning(self, "入力エラー", "タイトルは必須です。")
            self._title_edit.setFocus()
            return

        mitigation_text = self._mitigation_edit.toPlainText().strip()
        is_valid, error_msg = RiskService.validate_mitigation(mitigation_text)
        if not is_valid:
            QMessageBox.warning(self, "対策エラー", error_msg)
            self._mitigation_edit.setFocus()
            return

        super().accept()
