"""Main application window for HILS Manager.

Provides the top-level layout with a navigation sidebar, stacked content
panels, toolbar, menu bar, and status bar.  Panel slots are filled with
placeholder widgets until the real panel classes are swapped in.
"""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


# ---- Sidebar panel index mapping ------------------------------------------

_PANEL_INDICES: dict[str, int] = {
    "dashboard": 0,
    "projects": 1,
    "members": 2,
    "resources": 3,
    "project_detail": 4,
}


# ---- Placeholder factory ---------------------------------------------------

def _make_placeholder(text: str) -> QWidget:
    """Return a centred QLabel wrapped in a QWidget, used as a temporary panel."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    label = QLabel(text)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet("font-size: 18px; color: #888;")
    layout.addWidget(label)
    return widget


def _make_project_detail_placeholder() -> QWidget:
    """Return a tab-widget placeholder for the project detail view."""
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # Header
    header = QLabel("案件詳細")
    header.setObjectName("projectDetailHeader")
    header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 8px;")
    layout.addWidget(header)

    # Sub-tabs
    tabs = QTabWidget()
    tabs.setObjectName("projectDetailTabs")
    tabs.addTab(_make_placeholder("要望リスト (準備中)"), "要望リスト")
    tabs.addTab(_make_placeholder("WBS (準備中)"), "WBS")
    tabs.addTab(_make_placeholder("見積・実績 (準備中)"), "見積・実績")
    tabs.addTab(_make_placeholder("リスク (準備中)"), "リスク")
    layout.addWidget(tabs)

    return widget


# ---- Main Window -----------------------------------------------------------

class MainWindow(QMainWindow):
    """Primary application window."""

    VERSION = "0.1.0"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle(f"HILS開発管理システム v{self.VERSION}")
        self.setMinimumSize(1200, 800)

        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_status_bar()

    # ------------------------------------------------------------------
    # Menu bar
    # ------------------------------------------------------------------

    def _setup_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        # ファイル
        file_menu = menu_bar.addMenu("ファイル")

        db_settings_action = QAction("データベース設定", self)
        db_settings_action.triggered.connect(self._on_db_settings)
        file_menu.addAction(db_settings_action)

        file_menu.addSeparator()

        exit_action = QAction("終了", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 表示
        view_menu = menu_bar.addMenu("表示")

        dashboard_action = QAction("ダッシュボード", self)
        dashboard_action.triggered.connect(lambda: self.show_panel("dashboard"))
        view_menu.addAction(dashboard_action)

        projects_action = QAction("案件一覧", self)
        projects_action.triggered.connect(lambda: self.show_panel("projects"))
        view_menu.addAction(projects_action)

        members_action = QAction("メンバー管理", self)
        members_action.triggered.connect(lambda: self.show_panel("members"))
        view_menu.addAction(members_action)

        resources_action = QAction("リソース配置", self)
        resources_action.triggered.connect(lambda: self.show_panel("resources"))
        view_menu.addAction(resources_action)

        # ヘルプ
        help_menu = menu_bar.addMenu("ヘルプ")

        about_action = QAction("バージョン情報", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    # ------------------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------------------

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar("メインツールバー")
        toolbar.setObjectName("mainToolBar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # 新規案件
        new_project_action = QAction("新規案件", self)
        new_project_action.setToolTip("新しい案件を作成")
        new_project_action.triggered.connect(self._on_new_project)
        toolbar.addAction(new_project_action)

        # Jira同期 (placeholder)
        jira_sync_action = QAction("Jira同期", self)
        jira_sync_action.setToolTip("Jiraと同期 (未実装)")
        jira_sync_action.setEnabled(False)
        toolbar.addAction(jira_sync_action)

        toolbar.addSeparator()

        # レポート (placeholder)
        report_action = QAction("レポート", self)
        report_action.setToolTip("レポート出力 (未実装)")
        report_action.setEnabled(False)
        toolbar.addAction(report_action)

    # ------------------------------------------------------------------
    # Central widget (sidebar + stacked content)
    # ------------------------------------------------------------------

    def _setup_central_widget(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        self._sidebar = QListWidget()
        self._sidebar.setObjectName("sidebar")
        self._sidebar.setFixedWidth(200)
        self._sidebar.setIconSize(QSize(20, 20))

        sidebar_items = [
            ("ダッシュボード", "dashboard"),
            ("案件一覧", "projects"),
            ("メンバー管理", "members"),
            ("リソース配置", "resources"),
        ]
        for label, _key in sidebar_items:
            item = QListWidgetItem(label)
            item.setSizeHint(QSize(200, 48))
            self._sidebar.addItem(item)

        self._sidebar.currentRowChanged.connect(self._on_sidebar_changed)

        # Content stack
        self._stack = QStackedWidget()
        self._stack.setObjectName("contentStack")

        # Index 0 - Dashboard
        self.dashboard_panel = _make_placeholder("ダッシュボード (準備中)")
        self._stack.addWidget(self.dashboard_panel)

        # Index 1 - Projects
        self.projects_panel = _make_placeholder("案件一覧 (準備中)")
        self._stack.addWidget(self.projects_panel)

        # Index 2 - Members
        self.members_panel = _make_placeholder("メンバー管理 (準備中)")
        self._stack.addWidget(self.members_panel)

        # Index 3 - Resources
        self.resources_panel = _make_placeholder("リソース配置 (準備中)")
        self._stack.addWidget(self.resources_panel)

        # Index 4 - Project detail (hidden by default)
        self.project_detail_panel = _make_project_detail_placeholder()
        self._stack.addWidget(self.project_detail_panel)

        # Layout
        layout.addWidget(self._sidebar)
        layout.addWidget(self._stack, 1)

        # Select dashboard by default
        self._sidebar.setCurrentRow(0)

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------

    def _setup_status_bar(self) -> None:
        status = self.statusBar()
        status.setObjectName("appStatusBar")

        today = date.today().strftime("%Y/%m/%d")

        self._connection_label = QLabel("接続: ローカルDB")
        self._connection_label.setObjectName("statusConnection")
        status.addPermanentWidget(self._connection_label)

        self._date_label = QLabel(today)
        self._date_label.setObjectName("statusDate")
        status.addPermanentWidget(self._date_label)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def show_panel(self, panel_name: str) -> None:
        """Switch the content stack to the named panel.

        Parameters
        ----------
        panel_name:
            One of ``"dashboard"``, ``"projects"``, ``"members"``,
            ``"resources"``, or ``"project_detail"``.
        """
        index = _PANEL_INDICES.get(panel_name)
        if index is None:
            return

        self._stack.setCurrentIndex(index)

        # Keep sidebar selection in sync (project_detail has no sidebar item)
        if index < self._sidebar.count():
            self._sidebar.blockSignals(True)
            self._sidebar.setCurrentRow(index)
            self._sidebar.blockSignals(False)

    def show_project_detail(self, project_id: int) -> None:
        """Switch to the project detail view for *project_id*.

        The real project detail panel will load project data when it is
        implemented.  For now we just switch to the placeholder tab widget.
        """
        # Update the header with the project id as a minimal indicator
        header = self.project_detail_panel.findChild(QLabel, "projectDetailHeader")
        if header is not None:
            header.setText(f"案件詳細 (ID: {project_id})")

        self.show_panel("project_detail")

    # ------------------------------------------------------------------
    # Slot handlers
    # ------------------------------------------------------------------

    def _on_sidebar_changed(self, row: int) -> None:
        """Handle sidebar navigation clicks."""
        panel_names = ["dashboard", "projects", "members", "resources"]
        if 0 <= row < len(panel_names):
            self._stack.setCurrentIndex(row)

    def _on_new_project(self) -> None:
        """Handle the 'new project' toolbar action.

        Opens the new-project dialog when it is implemented.
        """
        QMessageBox.information(
            self,
            "新規案件",
            "新規案件ダイアログは今後実装されます。",
        )

    def _on_db_settings(self) -> None:
        """Handle the database settings menu action."""
        QMessageBox.information(
            self,
            "データベース設定",
            "データベース設定ダイアログは今後実装されます。",
        )

    def _on_about(self) -> None:
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "バージョン情報",
            f"HILS開発管理システム\nバージョン {self.VERSION}\n\n"
            "自動車組込み開発向けプロジェクト管理ツール",
        )
