"""Application bootstrap for HILS Manager.

Creates the QApplication, initialises the database, loads stylesheets,
and launches the main window.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from hils_manager.database.connection import DatabaseConnection
from hils_manager.database.migrations import run_migrations
from hils_manager.views.main_window import MainWindow

logger = logging.getLogger(__name__)

_APP_DIR = Path(__file__).resolve().parent
_RESOURCES_DIR = _APP_DIR.parent.parent / "resources"
_QSS_PATH = _RESOURCES_DIR / "styles" / "app_style.qss"
_CONFIG_PATH = _APP_DIR / "config.yaml"
_DEFAULT_DB_DIR = Path.cwd() / "data"
_DEFAULT_DB_PATH = _DEFAULT_DB_DIR / "hils_manager.db"


def _resolve_db_path() -> Path:
    """Determine the database file path.

    Checks for a ``config.yaml`` next to the package first.  If it exists and
    contains a ``database.path`` key the value is used.  Otherwise falls back
    to ``./data/hils_manager.db`` relative to the working directory.
    """
    if _CONFIG_PATH.exists():
        try:
            import yaml  # type: ignore[import-untyped]

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
    """Application entry point.  Returns the exit code."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = QApplication(sys.argv)
    app.setApplicationName("HILS開発管理")
    app.setOrganizationName("HILS Manager")

    # --- Database -----------------------------------------------------------
    db_path = _resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("データベース: %s", db_path)

    db = DatabaseConnection(db_path)
    with db as conn:
        run_migrations(conn)

    # --- Stylesheet ---------------------------------------------------------
    if _QSS_PATH.exists():
        qss = _QSS_PATH.read_text(encoding="utf-8")
        app.setStyleSheet(qss)
        logger.info("スタイルシート読み込み: %s", _QSS_PATH)
    else:
        logger.debug("スタイルシートが見つかりません: %s", _QSS_PATH)

    # --- Main window --------------------------------------------------------
    window = MainWindow()
    window.show()

    return app.exec()
