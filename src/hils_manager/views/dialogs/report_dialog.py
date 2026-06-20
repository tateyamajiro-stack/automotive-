"""Report output dialog."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from hils_manager.services.report_service import ReportService

logger = logging.getLogger(__name__)

_REPORT_TYPES = [
    ("detailed", "詳細レポート"),
    ("summary", "サマリーレポート"),
    ("weekly", "週次レポート"),
    ("monthly", "月次レポート"),
    ("annual", "年次レポート"),
]

_OUTPUT_FORMATS = [
    ("html", "HTML"),
    ("confluence", "Confluenceページ"),
]


class ReportDialog(QDialog):
    """Dialog for generating and exporting reports."""

    def __init__(
        self,
        report_service: ReportService,
        project_id: int | None,
        project_name: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._report_service = report_service
        self._project_id = project_id
        self._project_name = project_name
        self._current_html: str = ""

        self.setWindowTitle("レポート出力")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        options_group = QGroupBox("レポート設定")
        options_layout = QHBoxLayout(options_group)

        options_layout.addWidget(QLabel("対象案件:"))
        project_label = QLabel(self._project_name or "全プロジェクト")
        project_label.setStyleSheet("font-weight: bold;")
        options_layout.addWidget(project_label)

        options_layout.addSpacing(20)

        options_layout.addWidget(QLabel("種別:"))
        self._type_combo = QComboBox()
        for value, label in _REPORT_TYPES:
            self._type_combo.addItem(label, value)
        options_layout.addWidget(self._type_combo)

        options_layout.addSpacing(20)

        options_layout.addWidget(QLabel("形式:"))
        self._format_combo = QComboBox()
        for value, label in _OUTPUT_FORMATS:
            self._format_combo.addItem(label, value)
        options_layout.addWidget(self._format_combo)

        options_layout.addStretch()
        layout.addWidget(options_group)

        btn_layout = QHBoxLayout()
        preview_btn = QPushButton("プレビュー")
        preview_btn.clicked.connect(self._on_preview)
        btn_layout.addWidget(preview_btn)

        self._save_html_btn = QPushButton("HTML保存")
        self._save_html_btn.clicked.connect(self._on_save_html)
        self._save_html_btn.setEnabled(False)
        btn_layout.addWidget(self._save_html_btn)

        self._confluence_btn = QPushButton("Confluenceへ出力")
        self._confluence_btn.clicked.connect(self._on_push_confluence)
        self._confluence_btn.setEnabled(False)
        btn_layout.addWidget(self._confluence_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        preview_group = QGroupBox("プレビュー")
        preview_layout = QVBoxLayout(preview_group)
        self._preview_browser = QTextBrowser()
        self._preview_browser.setOpenExternalLinks(True)
        preview_layout.addWidget(self._preview_browser)
        layout.addWidget(preview_group, 1)

        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_btn = QPushButton("閉じる")
        close_btn.clicked.connect(self.accept)
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)

    def _on_preview(self) -> None:
        report_type = self._type_combo.currentData()
        output_format = self._format_combo.currentData()

        try:
            if output_format == "html":
                html = self._report_service.generate_html(
                    report_type, self._project_id
                )
            else:
                html = self._report_service.generate_confluence(
                    report_type, self._project_id
                )

            self._current_html = html
            self._preview_browser.setHtml(html)
            self._save_html_btn.setEnabled(True)
            self._confluence_btn.setEnabled(output_format == "confluence")

        except Exception as e:
            logger.exception("Report generation error")
            QMessageBox.critical(
                self, "エラー", f"レポート生成中にエラーが発生しました:\n{e}"
            )

    def _on_save_html(self) -> None:
        if not self._current_html:
            return

        report_type = self._type_combo.currentData()
        default_name = f"report_{report_type}.html"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "HTMLレポートを保存",
            default_name,
            "HTML Files (*.html);;All Files (*)",
        )
        if not file_path:
            return

        try:
            self._report_service.export_html_to_file(
                self._current_html, Path(file_path)
            )
            QMessageBox.information(
                self, "保存完了", f"レポートを保存しました:\n{file_path}"
            )
        except Exception as e:
            logger.exception("Failed to save HTML report")
            QMessageBox.critical(self, "エラー", f"保存に失敗しました:\n{e}")

    def _on_push_confluence(self) -> None:
        if not self._current_html:
            return

        report_type = self._type_combo.currentData()
        type_label = self._type_combo.currentText()
        title = f"{self._project_name} - {type_label}"

        reply = QMessageBox.question(
            self,
            "Confluence出力確認",
            f"以下のタイトルでConfluenceにページを作成/更新しますか？\n\n「{title}」",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            url = self._report_service.push_to_confluence(title, self._current_html)
            if url:
                QMessageBox.information(
                    self,
                    "Confluence出力完了",
                    f"Confluenceページを作成/更新しました。\n\nURL: {url}",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Confluence出力",
                    "Confluenceへの出力が完了しましたが、URLを取得できませんでした。\n"
                    "Confluence接続設定を確認してください。",
                )
        except Exception as e:
            logger.exception("Failed to push to Confluence")
            QMessageBox.critical(
                self, "エラー", f"Confluenceへの出力に失敗しました:\n{e}"
            )
