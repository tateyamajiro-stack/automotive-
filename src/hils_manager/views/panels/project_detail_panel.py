"""案件詳細パネル.

プロジェクトの詳細情報をタブ形式で表示するパネル。
基本情報、要望リスト、WBS、見積・実績、リスク、プロセス、アサインの
各タブを持つ。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from hils_manager.views.panels.requirement_panel import RequirementPanel
from hils_manager.views.panels.wbs_panel import WBSPanel
from hils_manager.views.panels.estimate_panel import EstimatePanel
from hils_manager.views.panels.risk_panel import RiskPanel

if TYPE_CHECKING:
    from hils_manager.models import Project
    from hils_manager.repositories.requirement_repo import RequirementRepository
    from hils_manager.repositories.wbs_repo import WBSRepository
    from hils_manager.services.estimate_service import EstimateService
    from hils_manager.services.project_service import ProjectService
    from hils_manager.services.resource_service import ResourceService
    from hils_manager.services.risk_service import RiskService


class ProjectDetailPanel(QWidget):
    """案件詳細パネル."""

    def __init__(
        self,
        project_service: ProjectService | None = None,
        requirement_repo: RequirementRepository | None = None,
        wbs_repo: WBSRepository | None = None,
        estimate_service: EstimateService | None = None,
        risk_service: RiskService | None = None,
        resource_service: ResourceService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._project_service = project_service
        self._requirement_repo = requirement_repo
        self._wbs_repo = wbs_repo
        self._estimate_service = estimate_service
        self._risk_service = risk_service
        self._resource_service = resource_service
        self._project_id: int | None = None
        self._project: Project | None = None

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI構築
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # --- ヘッダー ---
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        self._project_name_label = QLabel("案件詳細")
        self._project_name_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(self._project_name_label)

        self._status_badge = QLabel("")
        self._status_badge.setStyleSheet(
            "font-size: 12px; padding: 4px 12px; border-radius: 4px; "
            "background-color: #e0e0e0; color: #333;"
        )
        header_layout.addWidget(self._status_badge)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # --- タブウィジェット ---
        self._tabs = QTabWidget()
        self._tabs.setObjectName("projectDetailTabs")

        # タブ1: 基本情報
        self._basic_info_tab = self._create_basic_info_tab()
        self._tabs.addTab(self._basic_info_tab, "基本情報")

        # タブ2: 要望リスト
        self._requirement_panel = RequirementPanel(self._requirement_repo)
        self._tabs.addTab(self._requirement_panel, "要望リスト")

        # タブ3: WBS
        self._wbs_panel = WBSPanel(self._wbs_repo)
        self._tabs.addTab(self._wbs_panel, "WBS")

        # タブ4: 見積・実績
        self._estimate_panel = EstimatePanel(self._estimate_service)
        self._tabs.addTab(self._estimate_panel, "見積・実績")

        # タブ5: リスク
        self._risk_panel = RiskPanel(self._risk_service)
        self._tabs.addTab(self._risk_panel, "リスク")

        # タブ6: プロセス
        self._process_tab = self._create_process_tab()
        self._tabs.addTab(self._process_tab, "プロセス")

        # タブ7: アサイン
        self._assignment_tab = self._create_assignment_tab()
        self._tabs.addTab(self._assignment_tab, "アサイン")

        layout.addWidget(self._tabs, 1)

    # ------------------------------------------------------------------
    # 基本情報タブ
    # ------------------------------------------------------------------

    def _create_basic_info_tab(self) -> QWidget:
        """基本情報タブを生成する."""
        widget = QWidget()
        outer_layout = QVBoxLayout(widget)
        outer_layout.setContentsMargins(16, 16, 16, 16)
        outer_layout.setSpacing(12)

        # 編集ボタン
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._btn_basic_edit = QPushButton("編集")
        self._btn_basic_edit.clicked.connect(self._on_basic_edit)
        btn_layout.addWidget(self._btn_basic_edit)
        outer_layout.addLayout(btn_layout)

        # フォームレイアウト
        info_group = QGroupBox("案件情報")
        form = QFormLayout(info_group)
        form.setSpacing(10)
        form.setContentsMargins(16, 16, 16, 16)

        self._lbl_project_code = QLabel("—")
        form.addRow("案件コード:", self._lbl_project_code)

        self._lbl_project_name = QLabel("—")
        form.addRow("案件名:", self._lbl_project_name)

        self._lbl_description = QLabel("—")
        self._lbl_description.setWordWrap(True)
        form.addRow("説明:", self._lbl_description)

        self._lbl_status = QLabel("—")
        form.addRow("ステータス:", self._lbl_status)

        self._lbl_start_date = QLabel("—")
        form.addRow("開始予定日:", self._lbl_start_date)

        self._lbl_end_date = QLabel("—")
        form.addRow("終了予定日:", self._lbl_end_date)

        self._lbl_actual_start = QLabel("—")
        form.addRow("実績開始日:", self._lbl_actual_start)

        self._lbl_actual_end = QLabel("—")
        form.addRow("実績終了日:", self._lbl_actual_end)

        self._lbl_jira_key = QLabel("—")
        form.addRow("Jiraプロジェクトキー:", self._lbl_jira_key)

        outer_layout.addWidget(info_group)
        outer_layout.addStretch()

        return widget

    # ------------------------------------------------------------------
    # プロセスタブ
    # ------------------------------------------------------------------

    def _create_process_tab(self) -> QWidget:
        """プロセステーラリングタブを生成する."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel("プロセステーラリング")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)

        self._process_table = QTableWidget()
        self._process_table.setColumnCount(3)
        self._process_table.setHorizontalHeaderLabels(["選択", "プロセス名", "スキップ理由"])
        self._process_table.horizontalHeader().setStretchLastSection(True)
        self._process_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self._process_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._process_table.verticalHeader().setVisible(False)
        self._process_table.setAlternatingRowColors(True)
        layout.addWidget(self._process_table, 1)

        return widget

    # ------------------------------------------------------------------
    # アサインタブ
    # ------------------------------------------------------------------

    def _create_assignment_tab(self) -> QWidget:
        """アサインタブを生成する."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_layout = QHBoxLayout()
        header = QLabel("アサイン一覧")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(header)

        header_layout.addStretch()

        self._btn_assign_add = QPushButton("追加")
        self._btn_assign_add.clicked.connect(self._on_assign_add)
        header_layout.addWidget(self._btn_assign_add)

        self._btn_assign_remove = QPushButton("削除")
        self._btn_assign_remove.setEnabled(False)
        self._btn_assign_remove.clicked.connect(self._on_assign_remove)
        header_layout.addWidget(self._btn_assign_remove)

        layout.addLayout(header_layout)

        self._assignment_table = QTableWidget()
        self._assignment_table.setColumnCount(4)
        self._assignment_table.setHorizontalHeaderLabels(
            ["メンバー名", "役割", "配分率(%)", "期間"]
        )
        self._assignment_table.horizontalHeader().setStretchLastSection(True)
        self._assignment_table.verticalHeader().setVisible(False)
        self._assignment_table.setAlternatingRowColors(True)
        self._assignment_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._assignment_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self._assignment_table.itemSelectionChanged.connect(
            self._on_assignment_selection_changed
        )
        layout.addWidget(self._assignment_table, 1)

        return widget

    # ------------------------------------------------------------------
    # プロジェクト読み込み
    # ------------------------------------------------------------------

    def current_project(self) -> Project | None:
        """Return the currently loaded project, or ``None``."""
        return self._project

    def load_project(self, project_id: int) -> None:
        """プロジェクトデータを読み込み、全サブパネルを更新する."""
        self._project_id = project_id

        # 基本情報の読み込み
        if self._project_service is not None:
            self._project = self._project_service.get_project(project_id)
            self._update_basic_info()
            self._load_process_selections()
            self._load_assignments()

        # サブパネルのプロジェクト設定
        self._requirement_panel.set_project(project_id)
        self._wbs_panel.set_project(project_id)
        self._estimate_panel.set_project(project_id)
        self._risk_panel.set_project(project_id)

    # ------------------------------------------------------------------
    # 基本情報更新
    # ------------------------------------------------------------------

    def _update_basic_info(self) -> None:
        """基本情報ラベルを更新する."""
        project = self._project
        if project is None:
            self._project_name_label.setText("案件詳細")
            self._status_badge.setText("")
            return

        self._project_name_label.setText(project.name or "案件詳細")

        # ステータスバッジの色
        status_colors = {
            "計画中": ("#e3f2fd", "#1565c0"),
            "実行中": ("#e8f5e9", "#2e7d32"),
            "保留": ("#fff3e0", "#e65100"),
            "完了": ("#e0e0e0", "#424242"),
            "中止": ("#ffebee", "#c62828"),
        }
        status_label = project.status.label if hasattr(project.status, "label") else str(project.status)
        bg, fg = status_colors.get(status_label, ("#e0e0e0", "#333"))
        self._status_badge.setText(status_label)
        self._status_badge.setStyleSheet(
            f"font-size: 12px; padding: 4px 12px; border-radius: 4px; "
            f"background-color: {bg}; color: {fg}; font-weight: bold;"
        )

        # フォーム値
        self._lbl_project_code.setText(project.project_code or "—")
        self._lbl_project_name.setText(project.name or "—")
        self._lbl_description.setText(project.description or "—")
        self._lbl_status.setText(status_label)
        self._lbl_start_date.setText(
            project.start_date.strftime("%Y/%m/%d") if project.start_date else "—"
        )
        self._lbl_end_date.setText(
            project.end_date.strftime("%Y/%m/%d") if project.end_date else "—"
        )
        self._lbl_actual_start.setText(
            project.actual_start.strftime("%Y/%m/%d") if project.actual_start else "—"
        )
        self._lbl_actual_end.setText(
            project.actual_end.strftime("%Y/%m/%d") if project.actual_end else "—"
        )
        self._lbl_jira_key.setText(project.jira_project_key or "—")

    # ------------------------------------------------------------------
    # プロセス選択の読み込み
    # ------------------------------------------------------------------

    def _load_process_selections(self) -> None:
        """プロセステーラリング情報を読み込む."""
        if self._project_service is None or self._project_id is None:
            return

        selections = self._project_service.get_process_selections(self._project_id)
        self._process_table.setRowCount(len(selections))

        for row, sel in enumerate(selections):
            # 選択チェックボックス
            checkbox = QCheckBox()
            checkbox.setChecked(sel.is_selected)
            checkbox.setEnabled(False)  # 読み取り専用 (編集はダイアログで)
            cell_widget = QWidget()
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.addWidget(checkbox)
            cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            self._process_table.setCellWidget(row, 0, cell_widget)

            # プロセス名
            name_item = QTableWidgetItem(sel.process_name_ja or "")
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._process_table.setItem(row, 1, name_item)

            # スキップ理由
            reason_item = QTableWidgetItem(sel.skip_reason or "")
            reason_item.setFlags(reason_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._process_table.setItem(row, 2, reason_item)

    # ------------------------------------------------------------------
    # アサイン情報の読み込み
    # ------------------------------------------------------------------

    def _load_assignments(self) -> None:
        """アサイン情報を読み込む."""
        if self._resource_service is None or self._project_id is None:
            return

        assignments = self._resource_service.get_project_assignments(self._project_id)
        self._assignment_table.setRowCount(len(assignments))

        for row, assign in enumerate(assignments):
            # メンバー名
            name_item = QTableWidgetItem(assign.member_name or f"ID:{assign.member_id}")
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._assignment_table.setItem(row, 0, name_item)

            # 役割
            role_label = assign.role.label if hasattr(assign.role, "label") else str(assign.role)
            role_item = QTableWidgetItem(role_label)
            role_item.setFlags(role_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._assignment_table.setItem(row, 1, role_item)

            # 配分率
            alloc_item = QTableWidgetItem(f"{assign.allocation_pct:.0f}")
            alloc_item.setFlags(alloc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            alloc_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._assignment_table.setItem(row, 2, alloc_item)

            # 期間
            start = assign.start_date.strftime("%Y/%m/%d") if assign.start_date else ""
            end = assign.end_date.strftime("%Y/%m/%d") if assign.end_date else ""
            period = f"{start} - {end}" if start or end else "—"
            period_item = QTableWidgetItem(period)
            period_item.setFlags(period_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._assignment_table.setItem(row, 3, period_item)

    # ------------------------------------------------------------------
    # スロット
    # ------------------------------------------------------------------

    def _on_basic_edit(self) -> None:
        """基本情報編集ボタン押下."""
        pass

    def _on_assign_add(self) -> None:
        """アサイン追加ボタン押下."""
        pass

    def _on_assign_remove(self) -> None:
        """アサイン削除ボタン押下."""
        pass

    def _on_assignment_selection_changed(self) -> None:
        """アサイン行選択変更時にボタンの有効/無効を切り替え."""
        has_selection = len(self._assignment_table.selectedItems()) > 0
        self._btn_assign_remove.setEnabled(has_selection)

    def refresh(self) -> None:
        """全サブパネルのデータを再読み込みする."""
        if self._project_id is not None:
            self.load_project(self._project_id)
