from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from hils_manager.database.connection import DatabaseConnection
from hils_manager.database.migrations import run_migrations
from hils_manager.repositories.member_repo import MemberRepository
from hils_manager.repositories.project_repo import ProjectRepository
from hils_manager.repositories.requirement_repo import RequirementRepository
from hils_manager.repositories.wbs_repo import WBSRepository
from hils_manager.repositories.estimate_repo import EstimateRepository
from hils_manager.repositories.risk_repo import RiskRepository
from hils_manager.repositories.process_repo import ProcessRepository
from hils_manager.repositories.settings_repo import SettingsRepository
from hils_manager.repositories.jira_repo import JiraSyncRepository
from hils_manager.repositories.report_repo import ReportRepository
from hils_manager.integrations.config import ConnectionConfig
from hils_manager.services.project_service import ProjectService
from hils_manager.services.resource_service import ResourceService
from hils_manager.services.estimate_service import EstimateService
from hils_manager.services.risk_service import RiskService
from hils_manager.services.report_service import ReportService
from hils_manager.views.main_window import MainWindow

logger = logging.getLogger(__name__)

_APP_DIR = Path(__file__).resolve().parent
_RESOURCES_DIR = _APP_DIR.parent.parent / "resources"
_QSS_PATH = _RESOURCES_DIR / "styles" / "app_style.qss"
_CONFIG_PATH = _APP_DIR / "config.yaml"
_DEFAULT_DB_DIR = Path.cwd() / "data"
_DEFAULT_DB_PATH = _DEFAULT_DB_DIR / "hils_manager.db"


def _resolve_db_path() -> Path:
    if _CONFIG_PATH.exists():
        try:
            import yaml

            with _CONFIG_PATH.open(encoding="utf-8") as fh:
                cfg = yaml.safe_load(fh)
            if cfg and isinstance(cfg, dict):
                db_section = cfg.get("database", {})
                if isinstance(db_section, dict) and "path" in db_section:
                    return Path(db_section["path"]).expanduser().resolve()
        except Exception:
            logger.warning("config.yaml が読み込めませんでした。デフォルトのDBパスを使用します。")

    return _DEFAULT_DB_PATH


def run() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = QApplication(sys.argv)
    app.setApplicationName("HILS開発管理")
    app.setOrganizationName("HILS Manager")

    db_path = _resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("データベース: %s", db_path)

    db = DatabaseConnection(db_path)
    with db as conn:
        run_migrations(conn)

    if _QSS_PATH.exists():
        qss = _QSS_PATH.read_text(encoding="utf-8")
        app.setStyleSheet(qss)
        logger.info("スタイルシート読み込み: %s", _QSS_PATH)

    member_repo = MemberRepository(db)
    project_repo = ProjectRepository(db)
    requirement_repo = RequirementRepository(db)
    wbs_repo = WBSRepository(db)
    estimate_repo = EstimateRepository(db)
    risk_repo = RiskRepository(db)
    process_repo = ProcessRepository(db)
    settings_repo = SettingsRepository(db)
    jira_sync_repo = JiraSyncRepository(db)
    report_repo = ReportRepository(db)

    project_service = ProjectService(project_repo, process_repo)
    resource_service = ResourceService(member_repo, project_repo)
    estimate_service = EstimateService(estimate_repo)
    risk_service = RiskService(risk_repo)

    connection_config = ConnectionConfig(settings_repo)

    jira_service = None
    confluence_client = None
    jira_cfg = connection_config.get_jira_config()
    if jira_cfg:
        from hils_manager.integrations.jira_client import JiraClient
        from hils_manager.services.jira_service import JiraService

        jira_client = JiraClient(jira_cfg["base_url"], jira_cfg["pat"])
        jira_service = JiraService(
            jira_client=jira_client,
            jira_repo=jira_sync_repo,
            wbs_repo=wbs_repo,
            requirement_repo=requirement_repo,
            risk_repo=risk_repo,
        )

    confluence_cfg = connection_config.get_confluence_config()
    if confluence_cfg:
        from hils_manager.integrations.confluence_client import ConfluenceClient

        confluence_client = ConfluenceClient(
            confluence_cfg["base_url"], confluence_cfg["pat"]
        )

    report_service = ReportService(
        report_repo=report_repo,
        project_service=project_service,
        estimate_service=estimate_service,
        risk_service=risk_service,
        resource_service=resource_service,
        confluence_client=confluence_client,
    )

    window = MainWindow(
        project_service=project_service,
        resource_service=resource_service,
        estimate_service=estimate_service,
        risk_service=risk_service,
        requirement_repo=requirement_repo,
        wbs_repo=wbs_repo,
        jira_service=jira_service,
        report_service=report_service,
        connection_config=connection_config,
    )
    window.show()

    return app.exec()
