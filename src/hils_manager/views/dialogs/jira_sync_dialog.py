"""Jira synchronization dialog."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from hils_manager.services.jira_service import JiraService

logger = logging.getLogger(__name__)


class _SyncWorker(QThread):
    """Background worker for Jira sync operations."""

    finished = Signal(dict)
    error = Signal(str)

    def __init__(
        self,
        jira_service: JiraService,
        project_id: int,
        jira_project_key: str,
        operation: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._jira_service = jira_service
        self._project_id = project_id
        self._jira_project_key = jira_project_key
        self._operation = operation

    def run(self) -> None:
        try:
            if self._operation == "push":
                result = self._jira_service.push(
                    self._project_id, self._jira_project_key
                )
            else:
                result = self._jira_service.fetch(
                    self._project_id, self._jira_project_key
                )
            self.finished.emit(result)
        except Exception as e:
            logger.exception("Jira sync error")
            self.error.emit(str(e))


class JiraSyncDialog(QDialog):
    """Dialog for Jira push/fetch synchronization."""

    def __init__(
        self,
        jira_service: JiraService,
        project_id: int,
        project_name: str,
        jira_project_key: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._jira_service = jira_service
        self._project_id = project_id
        self._project_name = project_name
        self._jira_project_key = jira_project_key
        self._worker: _SyncWorker | None = None

        self.setWindowTitle("Jira同期")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        self._setup_ui()
        self._load_sync_status()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        info_group = QGroupBox("プロジェクト情報")
        info_layout = QHBoxLayout(info_group)
        info_layout.addWidget(QLabel(f"案件: {self._project_name}"))
        info_layout.addWidget(QLabel(f"Jiraキー: {self._jira_project_key}"))
        info_layout.addStretch()
        layout.addWidget(info_group)

        btn_layout = QHBoxLayout()
        self._push_btn = QPushButton("Jira Push (ローカル → Jira)")
        self._push_btn.clicked.connect(self._on_push)
        btn_layout.addWidget(self._push_btn)

        self._fetch_btn = QPushButton("Jira Fetch (Jira → ローカル)")
        self._fetch_btn.clicked.connect(self._on_fetch)
        btn_layout.addWidget(self._fetch_btn)

        self._refresh_btn = QPushButton("状態更新")
        self._refresh_btn.clicked.connect(self._load_sync_status)
        btn_layout.addWidget(self._refresh_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        status_group = QGroupBox("同期ステータス")
        status_layout = QVBoxLayout(status_group)

        self._status_table = QTableWidget()
        self._status_table.setColumnCount(5)
        self._status_table.setHorizontalHeaderLabels(
            ["エンティティ", "ローカルID", "Jiraキー", "ステータス", "最終同期"]
        )
        header = self._status_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._status_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._status_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        status_layout.addWidget(self._status_table)
        layout.addWidget(status_group)

        log_group = QGroupBox("ログ")
        log_layout = QVBoxLayout(log_group)
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMaximumHeight(120)
        log_layout.addWidget(self._log_text)
        layout.addWidget(log_group)

        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("閉じる")
        close_btn.clicked.connect(self.accept)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)

    def _load_sync_status(self) -> None:
        try:
            statuses = self._jira_service.get_sync_status(self._project_id)
        except Exception as e:
            logger.warning("Failed to load sync status: %s", e)
            statuses = []

        self._status_table.setRowCount(len(statuses))
        _STATUS_LABELS = {
            "synced": "同期済",
            "local_modified": "ローカル変更あり",
            "remote_modified": "リモート変更あり",
            "conflict": "コンフリクト",
        }
        for row, s in enumerate(statuses):
            self._status_table.setItem(
                row, 0, QTableWidgetItem(s.get("local_entity", ""))
            )
            self._status_table.setItem(
                row, 1, QTableWidgetItem(str(s.get("local_id", "")))
            )
            self._status_table.setItem(
                row, 2, QTableWidgetItem(s.get("jira_issue_key", ""))
            )
            status_text = _STATUS_LABELS.get(
                s.get("sync_status", ""), s.get("sync_status", "")
            )
            status_item = QTableWidgetItem(status_text)
            if s.get("sync_status") == "conflict":
                status_item.setForeground(Qt.GlobalColor.red)
            self._status_table.setItem(row, 3, status_item)
            self._status_table.setItem(
                row, 4, QTableWidgetItem(s.get("last_sync_at", ""))
            )

    def _set_busy(self, busy: bool) -> None:
        self._push_btn.setEnabled(not busy)
        self._fetch_btn.setEnabled(not busy)
        self._refresh_btn.setEnabled(not busy)
        self._progress.setVisible(busy)

    def _on_push(self) -> None:
        if not self._jira_project_key:
            QMessageBox.warning(self, "エラー", "Jiraプロジェクトキーが設定されていません。")
            return
        self._set_busy(True)
        self._log_text.append("Push開始...")
        self._worker = _SyncWorker(
            self._jira_service,
            self._project_id,
            self._jira_project_key,
            "push",
            self,
        )
        self._worker.finished.connect(self._on_sync_finished)
        self._worker.error.connect(self._on_sync_error)
        self._worker.start()

    def _on_fetch(self) -> None:
        if not self._jira_project_key:
            QMessageBox.warning(self, "エラー", "Jiraプロジェクトキーが設定されていません。")
            return
        self._set_busy(True)
        self._log_text.append("Fetch開始...")
        self._worker = _SyncWorker(
            self._jira_service,
            self._project_id,
            self._jira_project_key,
            "fetch",
            self,
        )
        self._worker.finished.connect(self._on_sync_finished)
        self._worker.error.connect(self._on_sync_error)
        self._worker.start()

    def _on_sync_finished(self, result: dict) -> None:
        self._set_busy(False)
        pushed = result.get("pushed", 0)
        fetched = result.get("fetched", 0)
        conflicts = result.get("conflicts", 0)
        errors = result.get("errors", [])

        if pushed:
            self._log_text.append(f"Push完了: {pushed}件同期しました。")
        if fetched:
            self._log_text.append(f"Fetch完了: {fetched}件取得しました。")
        if conflicts:
            self._log_text.append(f"コンフリクト: {conflicts}件")
        for err in errors:
            self._log_text.append(f"エラー: {err}")

        if not errors:
            self._log_text.append("同期が正常に完了しました。")

        self._load_sync_status()

    def _on_sync_error(self, error_msg: str) -> None:
        self._set_busy(False)
        self._log_text.append(f"同期エラー: {error_msg}")
        QMessageBox.critical(self, "同期エラー", f"Jira同期中にエラーが発生しました:\n{error_msg}")
