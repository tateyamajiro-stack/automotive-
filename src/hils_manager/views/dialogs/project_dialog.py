"""新規案件・案件編集ダイアログ."""

from __future__ import annotations

from datetime import date
from typing import Optional

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from hils_manager.constants import ProjectStatus
from hils_manager.models.project import Project

_DEV_JIRA_PLACEHOLDER = (
    "例: https://tateyamajiro.atlassian.net/jira/polaris/projects/YOSHI/"
    "ideas/view/13753945?selectedIssue=YOSHI-7&issueViewSection=overview"
)
_EFF_JIRA_PLACEHOLDER = (
    "例: https://tateyamajiro.atlassian.net/jira/polaris/projects/YOSHI/"
    "ideas/view/13753945?selectedIssue=YOSHI-8&issueViewSection=overview"
)


class ProjectDialog(QDialog):
    """案件の追加・編集ダイアログ."""

    def __init__(
        self,
        project: Optional[Project] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._project = project
        self._is_edit = project is not None

        self.setWindowTitle("案件編集" if self._is_edit else "新規案件")
        self.setMinimumWidth(520)

        self._setup_ui()

        if self._is_edit and project is not None:
            self._populate(project)

    # ------------------------------------------------------------------
    # UI構築
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # 案件コード (auto-generated, read-only)
        self._code_edit = QLineEdit()
        self._code_edit.setReadOnly(True)
        if not self._is_edit:
            self._code_edit.setPlaceholderText("自動採番")
            self._code_edit.setStyleSheet("background-color: #f0f0f0;")
        form.addRow("案件コード:", self._code_edit)

        # 案件名
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("例: HILS制御モデル開発")
        form.addRow("案件名:", self._name_edit)

        # 説明
        self._description_edit = QTextEdit()
        self._description_edit.setFixedHeight(72)
        form.addRow("説明:", self._description_edit)

        # ステータス (edit mode only)
        self._status_combo = QComboBox()
        for status in ProjectStatus:
            self._status_combo.addItem(status.label, status)
        self._status_label = QLabel("ステータス:")
        if self._is_edit:
            form.addRow(self._status_label, self._status_combo)
        else:
            self._status_combo.hide()
            self._status_label.hide()

        # 開始予定日
        self._start_date_edit = QDateEdit()
        self._start_date_edit.setCalendarPopup(True)
        self._start_date_edit.setDisplayFormat("yyyy/MM/dd")
        self._start_date_edit.setDate(QDate.currentDate())
        form.addRow("開始予定日:", self._start_date_edit)

        # 終了予定日
        self._end_date_edit = QDateEdit()
        self._end_date_edit.setCalendarPopup(True)
        self._end_date_edit.setDisplayFormat("yyyy/MM/dd")
        self._end_date_edit.setDate(QDate.currentDate().addMonths(3))
        form.addRow("終了予定日:", self._end_date_edit)

        # 実開始日 (edit mode only)
        self._actual_start_widget = QWidget()
        actual_start_layout = QHBoxLayout(self._actual_start_widget)
        actual_start_layout.setContentsMargins(0, 0, 0, 0)
        self._actual_start_check = QCheckBox()
        self._actual_start_check.toggled.connect(self._on_actual_start_toggled)
        actual_start_layout.addWidget(self._actual_start_check)
        self._actual_start_edit = QDateEdit()
        self._actual_start_edit.setCalendarPopup(True)
        self._actual_start_edit.setDisplayFormat("yyyy/MM/dd")
        self._actual_start_edit.setDate(QDate.currentDate())
        self._actual_start_edit.setEnabled(False)
        actual_start_layout.addWidget(self._actual_start_edit)
        self._actual_start_label = QLabel("実開始日:")
        if self._is_edit:
            form.addRow(self._actual_start_label, self._actual_start_widget)
        else:
            self._actual_start_widget.hide()
            self._actual_start_label.hide()

        # 実終了日 (edit mode only)
        self._actual_end_widget = QWidget()
        actual_end_layout = QHBoxLayout(self._actual_end_widget)
        actual_end_layout.setContentsMargins(0, 0, 0, 0)
        self._actual_end_check = QCheckBox()
        self._actual_end_check.toggled.connect(self._on_actual_end_toggled)
        actual_end_layout.addWidget(self._actual_end_check)
        self._actual_end_edit = QDateEdit()
        self._actual_end_edit.setCalendarPopup(True)
        self._actual_end_edit.setDisplayFormat("yyyy/MM/dd")
        self._actual_end_edit.setDate(QDate.currentDate())
        self._actual_end_edit.setEnabled(False)
        actual_end_layout.addWidget(self._actual_end_edit)
        self._actual_end_label = QLabel("実終了日:")
        if self._is_edit:
            form.addRow(self._actual_end_label, self._actual_end_widget)
        else:
            self._actual_end_widget.hide()
            self._actual_end_label.hide()

        # 開発用JIRA (renamed from Jiraプロジェクトキー)
        self._jira_key_edit = QLineEdit()
        self._jira_key_edit.setPlaceholderText(_DEV_JIRA_PLACEHOLDER)
        form.addRow("開発用JIRA:", self._jira_key_edit)

        # 効率化JIRA (new field)
        self._efficiency_jira_edit = QLineEdit()
        self._efficiency_jira_edit.setPlaceholderText(_EFF_JIRA_PLACEHOLDER)
        form.addRow("効率化JIRA:", self._efficiency_jira_edit)

        layout.addLayout(form)

        # ボタン
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)
        layout.addWidget(self._button_box)

    # ------------------------------------------------------------------
    # 外部から案件コードを設定
    # ------------------------------------------------------------------

    def set_project_code(self, code: str) -> None:
        """Set the auto-generated project code."""
        self._code_edit.setText(code)

    # ------------------------------------------------------------------
    # スロット
    # ------------------------------------------------------------------

    def _on_actual_start_toggled(self, checked: bool) -> None:
        self._actual_start_edit.setEnabled(checked)

    def _on_actual_end_toggled(self, checked: bool) -> None:
        self._actual_end_edit.setEnabled(checked)

    # ------------------------------------------------------------------
    # データ入出力
    # ------------------------------------------------------------------

    def _populate(self, project: Project) -> None:
        """既存案件データをフォームにセットする."""
        self._code_edit.setText(project.project_code)
        self._name_edit.setText(project.name)
        self._description_edit.setPlainText(project.description)

        # ステータス
        for i in range(self._status_combo.count()):
            if self._status_combo.itemData(i) == project.status:
                self._status_combo.setCurrentIndex(i)
                break

        # 日付
        if project.start_date is not None:
            self._start_date_edit.setDate(
                QDate(project.start_date.year, project.start_date.month, project.start_date.day)
            )
        if project.end_date is not None:
            self._end_date_edit.setDate(
                QDate(project.end_date.year, project.end_date.month, project.end_date.day)
            )

        if project.actual_start is not None:
            self._actual_start_check.setChecked(True)
            self._actual_start_edit.setDate(
                QDate(project.actual_start.year, project.actual_start.month, project.actual_start.day)
            )
        if project.actual_end is not None:
            self._actual_end_check.setChecked(True)
            self._actual_end_edit.setDate(
                QDate(project.actual_end.year, project.actual_end.month, project.actual_end.day)
            )

        self._jira_key_edit.setText(project.jira_project_key)
        self._efficiency_jira_edit.setText(project.efficiency_jira_url)

    @staticmethod
    def _qdate_to_date(qdate: QDate) -> date:
        return date(qdate.year(), qdate.month(), qdate.day())

    def get_project(self) -> Project:
        """フォーム値からProjectオブジェクトを生成して返す."""
        actual_start: date | None = None
        actual_end: date | None = None

        if self._is_edit:
            if self._actual_start_check.isChecked():
                actual_start = self._qdate_to_date(self._actual_start_edit.date())
            if self._actual_end_check.isChecked():
                actual_end = self._qdate_to_date(self._actual_end_edit.date())

        status = self._status_combo.currentData() if self._is_edit else ProjectStatus.PLANNING

        return Project(
            id=self._project.id if self._project else None,
            project_code=self._code_edit.text().strip(),
            name=self._name_edit.text().strip(),
            description=self._description_edit.toPlainText().strip(),
            status=status,
            start_date=self._qdate_to_date(self._start_date_edit.date()),
            end_date=self._qdate_to_date(self._end_date_edit.date()),
            actual_start=actual_start,
            actual_end=actual_end,
            jira_project_key=self._jira_key_edit.text().strip(),
            efficiency_jira_url=self._efficiency_jira_edit.text().strip(),
            created_at=self._project.created_at if self._project else None,
            updated_at=self._project.updated_at if self._project else None,
        )

    # ------------------------------------------------------------------
    # バリデーション
    # ------------------------------------------------------------------

    def accept(self) -> None:
        """OKボタン押下時のバリデーション."""
        if not self._name_edit.text().strip():
            QMessageBox.warning(self, "入力エラー", "案件名は必須です。")
            self._name_edit.setFocus()
            return
        super().accept()
