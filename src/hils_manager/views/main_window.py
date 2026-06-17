from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from hils_manager.views.panels.member_panel import MemberPanel
from hils_manager.views.panels.project_list_panel import ProjectListPanel
from hils_manager.views.panels.project_detail_panel import ProjectDetailPanel
from hils_manager.views.panels.resource_panel import ResourcePanel
from hils_manager.views.dialogs.project_dialog import ProjectDialog

if TYPE_CHECKING:
    from hils_manager.services.project_service import ProjectService
    from hils_manager.services.resource_service import ResourceService
    from hils_manager.services.estimate_service import EstimateService
    from hils_manager.services.risk_service import RiskService
    from hils_manager.repositories.requirement_repo import RequirementRepository
    from hils_manager.repositories.wbs_repo import WBSRepository

_PANEL_INDICES: dict[str, int] = {
    "dashboard": 0,
    "projects": 1,
    "members": 2,
    "resources": 3,
    "project_detail": 4,
}


def _make_placeholder(text: str) -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    label = QLabel(text)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet("font-size: 18px; color: #888;")
    layout.addWidget(label)
    return widget


class MainWindow(QMainWindow):
    VERSION = "0.1.0"

    def __init__(
        self,
        project_service: ProjectService,
        resource_service: ResourceService,
        estimate_service: EstimateService,
        risk_service: RiskService,
        requirement_repo: RequirementRepository,
        wbs_repo: WBSRepository,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._project_service = project_service
        self._resource_service = resource_service
        self._estimate_service = estimate_service
        self._risk_service = risk_service
        self._requirement_repo = requirement_repo
        self._wbs_repo = wbs_repo

        self.setWindowTitle(f"HILS開発管理システム v{self.VERSION}")
        self.setMinimumSize(1200, 800)

        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_status_bar()

    def _setup_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("ファイル")
        db_settings_action = QAction("データベース設定", self)
        db_settings_action.triggered.connect(self._on_db_settings)
        file_menu.addAction(db_settings_action)
        file_menu.addSeparator()
        exit_action = QAction("終了", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menu_bar.addMenu("表示")
        for label, key in [
            ("ダッシュボード", "dashboard"),
            ("案件一覧", "projects"),
            ("メンバー管理", "members"),
            ("リソース配置", "resources"),
        ]:
            action = QAction(label, self)
            action.triggered.connect(lambda checked=False, k=key: self.show_panel(k))
            view_menu.addAction(action)

        help_menu = menu_bar.addMenu("ヘルプ")
        about_action = QAction("バージョン情報", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar("メインツールバー")
        toolbar.setObjectName("mainToolBar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        new_project_action = QAction("新規案件", self)
        new_project_action.setToolTip("新しい案件を作成")
        new_project_action.triggered.connect(self._on_new_project)
        toolbar.addAction(new_project_action)

        jira_sync_action = QAction("Jira同期", self)
        jira_sync_action.setToolTip("Jiraと同期 (未実装)")
        jira_sync_action.setEnabled(False)
        toolbar.addAction(jira_sync_action)

        toolbar.addSeparator()

        report_action = QAction("レポート", self)
        report_action.setToolTip("レポート出力 (未実装)")
        report_action.setEnabled(False)
        toolbar.addAction(report_action)

    def _setup_central_widget(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._sidebar = QListWidget()
        self._sidebar.setObjectName("sidebar")
        self._sidebar.setFixedWidth(200)
        self._sidebar.setIconSize(QSize(20, 20))

        for label, _key in [
            ("ダッシュボード", "dashboard"),
            ("案件一覧", "projects"),
            ("メンバー管理", "members"),
            ("リソース配置", "resources"),
        ]:
            item = QListWidgetItem(label)
            item.setSizeHint(QSize(200, 48))
            self._sidebar.addItem(item)

        self._sidebar.currentRowChanged.connect(self._on_sidebar_changed)

        self._stack = QStackedWidget()
        self._stack.setObjectName("contentStack")

        # Index 0 - Dashboard (placeholder for now)
        self.dashboard_panel = _make_placeholder("ダッシュボード (Phase 4 で実装)")
        self._stack.addWidget(self.dashboard_panel)

        # Index 1 - Projects
        self.projects_panel = ProjectListPanel(self._project_service)
        self.projects_panel.project_selected.connect(self.show_project_detail)
        self._stack.addWidget(self.projects_panel)

        # Index 2 - Members
        self.members_panel = MemberPanel(self._resource_service)
        self._stack.addWidget(self.members_panel)

        # Index 3 - Resources
        self.resources_panel = ResourcePanel(self._resource_service)
        self._stack.addWidget(self.resources_panel)

        # Index 4 - Project detail
        self.project_detail_panel = ProjectDetailPanel(
            self._project_service,
            self._requirement_repo,
            self._wbs_repo,
            self._estimate_service,
            self._risk_service,
            self._resource_service,
        )
        self._stack.addWidget(self.project_detail_panel)

        layout.addWidget(self._sidebar)
        layout.addWidget(self._stack, 1)

        self._sidebar.setCurrentRow(0)

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

    def show_panel(self, panel_name: str) -> None:
        index = _PANEL_INDICES.get(panel_name)
        if index is None:
            return
        self._stack.setCurrentIndex(index)
        if index < self._sidebar.count():
            self._sidebar.blockSignals(True)
            self._sidebar.setCurrentRow(index)
            self._sidebar.blockSignals(False)

    def show_project_detail(self, project_id: int) -> None:
        self.project_detail_panel.load_project(project_id)
        self.show_panel("project_detail")

    def _on_sidebar_changed(self, row: int) -> None:
        panel_names = ["dashboard", "projects", "members", "resources"]
        if 0 <= row < len(panel_names):
            self._stack.setCurrentIndex(row)

    def _on_new_project(self) -> None:
        dialog = ProjectDialog(parent=self)
        if dialog.exec():
            project = dialog.get_project()
            self._project_service.create_project(project)
            self.projects_panel.refresh()
            self.show_panel("projects")

    def _on_db_settings(self) -> None:
        QMessageBox.information(
            self, "データベース設定", "データベース設定ダイアログは今後実装されます。"
        )

    def _on_about(self) -> None:
        QMessageBox.about(
            self,
            "バージョン情報",
            f"HILS開発管理システム\nバージョン {self.VERSION}\n\n"
            "自動車組込み開発向けプロジェクト管理ツール",
        )
