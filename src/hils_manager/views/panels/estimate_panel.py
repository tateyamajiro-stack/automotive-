"""見積・実績パネル.

見積一覧と実績工数を上下に分割表示し、見積 vs 実績のサマリを表示するパネル。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from hils_manager.services.estimate_service import EstimateService


class EstimatePanel(QWidget):
    """見積・実績パネル."""

    def __init__(self, estimate_service: EstimateService | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._estimate_service: EstimateService | None = estimate_service
        self._estimate_model = None
        self._time_entry_model = None
        self._project_id: int | None = None

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI構築
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # --- 左側: スプリッタ (見積一覧 + 実績工数) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # 上部: 見積一覧
        estimate_widget = QWidget()
        estimate_layout = QVBoxLayout(estimate_widget)
        estimate_layout.setContentsMargins(0, 0, 0, 0)
        estimate_layout.setSpacing(8)

        estimate_header = QHBoxLayout()
        estimate_header.setSpacing(8)

        estimate_title = QLabel("見積一覧")
        estimate_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        estimate_header.addWidget(estimate_title)

        estimate_header.addStretch()

        self._btn_estimate_add = QPushButton("追加")
        self._btn_estimate_add.clicked.connect(self._on_estimate_add)
        estimate_header.addWidget(self._btn_estimate_add)

        self._btn_estimate_edit = QPushButton("編集")
        self._btn_estimate_edit.setEnabled(False)
        self._btn_estimate_edit.clicked.connect(self._on_estimate_edit)
        estimate_header.addWidget(self._btn_estimate_edit)

        self._btn_estimate_delete = QPushButton("削除")
        self._btn_estimate_delete.setEnabled(False)
        self._btn_estimate_delete.clicked.connect(self._on_estimate_delete)
        estimate_header.addWidget(self._btn_estimate_delete)

        estimate_layout.addLayout(estimate_header)

        self._estimate_table = QTableView()
        self._estimate_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._estimate_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._estimate_table.setAlternatingRowColors(True)
        self._estimate_table.setSortingEnabled(True)
        self._estimate_table.horizontalHeader().setStretchLastSection(True)
        self._estimate_table.verticalHeader().setVisible(False)
        estimate_layout.addWidget(self._estimate_table, 1)

        splitter.addWidget(estimate_widget)

        # 下部: 実績工数
        time_entry_widget = QWidget()
        time_entry_layout = QVBoxLayout(time_entry_widget)
        time_entry_layout.setContentsMargins(0, 0, 0, 0)
        time_entry_layout.setSpacing(8)

        time_header = QHBoxLayout()
        time_header.setSpacing(8)

        time_title = QLabel("実績工数")
        time_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        time_header.addWidget(time_title)

        time_header.addStretch()

        self._btn_time_add = QPushButton("工数追加")
        self._btn_time_add.clicked.connect(self._on_time_entry_add)
        time_header.addWidget(self._btn_time_add)

        time_entry_layout.addLayout(time_header)

        self._time_entry_table = QTableView()
        self._time_entry_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._time_entry_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._time_entry_table.setAlternatingRowColors(True)
        self._time_entry_table.setSortingEnabled(True)
        self._time_entry_table.horizontalHeader().setStretchLastSection(True)
        self._time_entry_table.verticalHeader().setVisible(False)
        time_entry_layout.addWidget(self._time_entry_table, 1)

        splitter.addWidget(time_entry_widget)

        left_layout.addWidget(splitter)
        main_layout.addWidget(left_widget, 3)

        # --- 右側: サマリ ---
        self._summary_group = QGroupBox("見積 vs 実績")
        summary_layout = QVBoxLayout(self._summary_group)
        summary_layout.setSpacing(12)

        self._lbl_planned_hours = QLabel("予定工数: —")
        self._lbl_planned_hours.setStyleSheet("font-size: 14px;")
        summary_layout.addWidget(self._lbl_planned_hours)

        self._lbl_actual_hours = QLabel("実績工数: —")
        self._lbl_actual_hours.setStyleSheet("font-size: 14px;")
        summary_layout.addWidget(self._lbl_actual_hours)

        self._lbl_variance = QLabel("差異: —")
        self._lbl_variance.setStyleSheet("font-size: 14px; font-weight: bold;")
        summary_layout.addWidget(self._lbl_variance)

        summary_layout.addStretch()

        main_layout.addWidget(self._summary_group, 1)

    # ------------------------------------------------------------------
    # プロジェクト設定
    # ------------------------------------------------------------------

    def set_project(self, project_id: int) -> None:
        """プロジェクトIDを設定し、見積・実績データを読み込む."""
        from hils_manager.viewmodels import EstimateTableModel, TimeEntryTableModel

        self._project_id = project_id
        if self._estimate_service is None:
            return

        # 見積モデル
        self._estimate_model = EstimateTableModel(self._estimate_service, project_id)
        self._estimate_table.setModel(self._estimate_model)
        self._estimate_table.selectionModel().selectionChanged.connect(
            self._on_estimate_selection_changed
        )

        # 実績工数モデル
        self._time_entry_model = TimeEntryTableModel(self._estimate_service, project_id)
        self._time_entry_table.setModel(self._time_entry_model)

        # サマリ更新
        self._update_summary()

    # ------------------------------------------------------------------
    # サマリ更新
    # ------------------------------------------------------------------

    def _update_summary(self) -> None:
        """見積 vs 実績サマリを更新する."""
        if self._estimate_service is None or self._project_id is None:
            return

        summary = self._estimate_service.get_estimate_vs_actual(self._project_id)
        planned = summary.get("planned_hours", 0.0)
        actual = summary.get("actual_hours", 0.0)
        variance = summary.get("variance_pct", 0.0)

        self._lbl_planned_hours.setText(f"予定工数: {planned:.1f} h")
        self._lbl_actual_hours.setText(f"実績工数: {actual:.1f} h")

        # 差異の色分け
        if variance > 10.0:
            color = "#d32f2f"  # 赤: 超過
        elif variance < -10.0:
            color = "#1976d2"  # 青: 下回り
        else:
            color = "#388e3c"  # 緑: 正常範囲
        self._lbl_variance.setText(f"差異: {variance:+.1f}%")
        self._lbl_variance.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color};")

    # ------------------------------------------------------------------
    # スロット
    # ------------------------------------------------------------------

    def _on_estimate_selection_changed(self) -> None:
        """見積行選択変更時にボタンの有効/無効を切り替え."""
        has_selection = self._estimate_table.selectionModel().hasSelection()
        self._btn_estimate_edit.setEnabled(has_selection)
        self._btn_estimate_delete.setEnabled(has_selection)

    def _on_estimate_add(self) -> None:
        """見積追加ボタン押下."""
        pass

    def _on_estimate_edit(self) -> None:
        """見積編集ボタン押下."""
        pass

    def _on_estimate_delete(self) -> None:
        """見積削除ボタン押下."""
        pass

    def _on_time_entry_add(self) -> None:
        """工数追加ボタン押下."""
        pass

    def refresh(self) -> None:
        """データを再読み込みする."""
        if self._estimate_model is not None:
            self._estimate_model.refresh()
        if self._time_entry_model is not None:
            self._time_entry_model.refresh()
        self._update_summary()
