"""Connection settings dialog for Jira and Confluence configuration."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hils_manager.integrations.config import ConnectionConfig
    from hils_manager.integrations.jira_client import JiraClient
    from hils_manager.integrations.confluence_client import ConfluenceClient


class ConnectionSettingsDialog(QDialog):
    """Dialog for configuring Jira and Confluence connections."""

    def __init__(
        self,
        config: ConnectionConfig,
        jira_client_factory: type | None = None,
        confluence_client_factory: type | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._jira_client_factory = jira_client_factory
        self._confluence_client_factory = confluence_client_factory

        self.setWindowTitle("接続設定")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._tabs = QTabWidget()

        self._tabs.addTab(self._create_jira_tab(), "Jira")
        self._tabs.addTab(self._create_confluence_tab(), "Confluence")

        layout.addWidget(self._tabs)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _create_jira_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(12)

        self._jira_url = QLineEdit()
        self._jira_url.setPlaceholderText("https://jira.example.com")
        form.addRow("ベースURL:", self._jira_url)

        self._jira_pat = QLineEdit()
        self._jira_pat.setEchoMode(QLineEdit.EchoMode.Password)
        self._jira_pat.setPlaceholderText("パーソナルアクセストークン")
        form.addRow("PAT:", self._jira_pat)

        self._jira_project_key = QLineEdit()
        self._jira_project_key.setPlaceholderText("例: HILS")
        form.addRow("デフォルトプロジェクトキー:", self._jira_project_key)

        test_layout = QHBoxLayout()
        self._jira_test_btn = QPushButton("接続テスト")
        self._jira_test_btn.clicked.connect(self._on_jira_test)
        self._jira_test_status = QLabel("")
        test_layout.addWidget(self._jira_test_btn)
        test_layout.addWidget(self._jira_test_status)
        test_layout.addStretch()
        form.addRow("", test_layout)

        clear_btn = QPushButton("Jira設定をクリア")
        clear_btn.clicked.connect(self._on_clear_jira)
        form.addRow("", clear_btn)

        return tab

    def _create_confluence_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(12)

        self._confluence_url = QLineEdit()
        self._confluence_url.setPlaceholderText("https://confluence.example.com")
        form.addRow("ベースURL:", self._confluence_url)

        self._confluence_pat = QLineEdit()
        self._confluence_pat.setEchoMode(QLineEdit.EchoMode.Password)
        self._confluence_pat.setPlaceholderText("パーソナルアクセストークン")
        form.addRow("PAT:", self._confluence_pat)

        self._confluence_space = QLineEdit()
        self._confluence_space.setPlaceholderText("例: HILS")
        form.addRow("スペースキー:", self._confluence_space)

        self._confluence_parent_page = QLineEdit()
        self._confluence_parent_page.setPlaceholderText("例: 12345")
        form.addRow("親ページID:", self._confluence_parent_page)

        test_layout = QHBoxLayout()
        self._confluence_test_btn = QPushButton("接続テスト")
        self._confluence_test_btn.clicked.connect(self._on_confluence_test)
        self._confluence_test_status = QLabel("")
        test_layout.addWidget(self._confluence_test_btn)
        test_layout.addWidget(self._confluence_test_status)
        test_layout.addStretch()
        form.addRow("", test_layout)

        clear_btn = QPushButton("Confluence設定をクリア")
        clear_btn.clicked.connect(self._on_clear_confluence)
        form.addRow("", clear_btn)

        return tab

    def _load_settings(self) -> None:
        jira_cfg = self._config.get_jira_config()
        if jira_cfg:
            self._jira_url.setText(jira_cfg.get("base_url", ""))
            self._jira_pat.setText(jira_cfg.get("pat", ""))
            self._jira_project_key.setText(jira_cfg.get("default_project_key", ""))

        confluence_cfg = self._config.get_confluence_config()
        if confluence_cfg:
            self._confluence_url.setText(confluence_cfg.get("base_url", ""))
            self._confluence_pat.setText(confluence_cfg.get("pat", ""))
            self._confluence_space.setText(confluence_cfg.get("space_key", ""))
            self._confluence_parent_page.setText(
                confluence_cfg.get("parent_page_id", "")
            )

    def _on_save(self) -> None:
        jira_url = self._jira_url.text().strip().rstrip("/")
        jira_pat = self._jira_pat.text().strip()
        jira_key = self._jira_project_key.text().strip()

        if jira_url and jira_pat:
            self._config.set_jira_config(jira_url, jira_pat, jira_key)
        elif not jira_url and not jira_pat:
            pass
        else:
            QMessageBox.warning(self, "入力エラー", "JiraのベースURLとPATは両方入力してください。")
            return

        conf_url = self._confluence_url.text().strip().rstrip("/")
        conf_pat = self._confluence_pat.text().strip()
        conf_space = self._confluence_space.text().strip()
        conf_parent = self._confluence_parent_page.text().strip()

        if conf_url and conf_pat:
            self._config.set_confluence_config(conf_url, conf_pat, conf_space, conf_parent)
        elif not conf_url and not conf_pat:
            pass
        else:
            QMessageBox.warning(
                self, "入力エラー", "ConfluenceのベースURLとPATは両方入力してください。"
            )
            return

        self.accept()

    def _on_jira_test(self) -> None:
        url = self._jira_url.text().strip().rstrip("/")
        pat = self._jira_pat.text().strip()
        if not url or not pat:
            self._jira_test_status.setText("URLとPATを入力してください")
            self._jira_test_status.setStyleSheet("color: #c0392b;")
            return

        if self._jira_client_factory is None:
            from hils_manager.integrations.jira_client import JiraClient
            factory = JiraClient
        else:
            factory = self._jira_client_factory

        self._jira_test_status.setText("テスト中...")
        self._jira_test_status.setStyleSheet("color: #7f8c8d;")
        self._jira_test_btn.setEnabled(False)

        try:
            client = factory(url, pat)
            if client.test_connection():
                self._jira_test_status.setText("接続成功")
                self._jira_test_status.setStyleSheet("color: #27ae60;")
            else:
                self._jira_test_status.setText("接続失敗")
                self._jira_test_status.setStyleSheet("color: #c0392b;")
        except Exception as e:
            self._jira_test_status.setText(f"エラー: {e}")
            self._jira_test_status.setStyleSheet("color: #c0392b;")
        finally:
            self._jira_test_btn.setEnabled(True)

    def _on_confluence_test(self) -> None:
        url = self._confluence_url.text().strip().rstrip("/")
        pat = self._confluence_pat.text().strip()
        if not url or not pat:
            self._confluence_test_status.setText("URLとPATを入力してください")
            self._confluence_test_status.setStyleSheet("color: #c0392b;")
            return

        if self._confluence_client_factory is None:
            from hils_manager.integrations.confluence_client import ConfluenceClient
            factory = ConfluenceClient
        else:
            factory = self._confluence_client_factory

        self._confluence_test_status.setText("テスト中...")
        self._confluence_test_status.setStyleSheet("color: #7f8c8d;")
        self._confluence_test_btn.setEnabled(False)

        try:
            client = factory(url, pat)
            if client.test_connection():
                self._confluence_test_status.setText("接続成功")
                self._confluence_test_status.setStyleSheet("color: #27ae60;")
            else:
                self._confluence_test_status.setText("接続失敗")
                self._confluence_test_status.setStyleSheet("color: #c0392b;")
        except Exception as e:
            self._confluence_test_status.setText(f"エラー: {e}")
            self._confluence_test_status.setStyleSheet("color: #c0392b;")
        finally:
            self._confluence_test_btn.setEnabled(True)

    def _on_clear_jira(self) -> None:
        reply = QMessageBox.question(
            self,
            "確認",
            "Jiraの接続設定をクリアしますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._config.clear_jira_config()
            self._jira_url.clear()
            self._jira_pat.clear()
            self._jira_project_key.clear()
            self._jira_test_status.setText("")

    def _on_clear_confluence(self) -> None:
        reply = QMessageBox.question(
            self,
            "確認",
            "Confluenceの接続設定をクリアしますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._config.clear_confluence_config()
            self._confluence_url.clear()
            self._confluence_pat.clear()
            self._confluence_space.clear()
            self._confluence_parent_page.clear()
            self._confluence_test_status.setText("")
