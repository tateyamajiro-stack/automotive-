"""Database migration runner for HILS Manager.

Reads ``schema.sql`` from the same package directory and applies it to the
database.  Schema version is tracked in the ``app_settings`` table so that
future migrations can be applied incrementally.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

_SCHEMA_DIR = Path(__file__).resolve().parent
_SCHEMA_FILE = _SCHEMA_DIR / "schema.sql"

# Bump this whenever schema.sql is updated with a new migration.
CURRENT_SCHEMA_VERSION = "2"


def _get_schema_version(conn: sqlite3.Connection) -> str | None:
    """Return the stored schema version, or ``None`` if untracked."""
    try:
        row = conn.execute(
            "SELECT value FROM app_settings WHERE key = 'schema_version'"
        ).fetchone()
        return row["value"] if row else None
    except sqlite3.OperationalError:
        # app_settings table does not exist yet.
        return None


def _set_schema_version(conn: sqlite3.Connection, version: str) -> None:
    """Insert or update the schema version in app_settings."""
    conn.execute(
        """
        INSERT INTO app_settings (key, value, description)
        VALUES ('schema_version', ?, 'Current database schema version')
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (version,),
    )


def run_migrations(conn: sqlite3.Connection) -> None:
    """Apply pending migrations to *conn*.

    On a fresh database this creates all tables from ``schema.sql`` and seeds
    the process definitions.  On an already-initialised database it checks the
    stored schema version and applies any newer migrations.

    Parameters
    ----------
    conn:
        An open :class:`sqlite3.Connection`.  The caller is responsible for
        committing or rolling back the transaction afterwards.
    """
    current = _get_schema_version(conn)

    if current is None:
        logger.info("Initialising database from schema.sql ...")
        _apply_schema(conn)
        _set_schema_version(conn, CURRENT_SCHEMA_VERSION)
        conn.commit()
        logger.info("Database initialised at schema version %s.", CURRENT_SCHEMA_VERSION)
        return

    if current == CURRENT_SCHEMA_VERSION:
        logger.debug("Database is up-to-date (schema version %s).", current)
        return

    if current == "1":
        logger.info("Migrating schema from version 1 to 2 ...")
        conn.execute("ALTER TABLE projects ADD COLUMN efficiency_jira_url TEXT")
        _set_schema_version(conn, "2")
        conn.commit()
        current = "2"
        logger.info("Schema migrated to version 2.")

    if current != CURRENT_SCHEMA_VERSION:
        logger.warning(
            "Database schema version (%s) differs from application version (%s).",
            current,
            CURRENT_SCHEMA_VERSION,
        )


def _apply_schema(conn: sqlite3.Connection) -> None:
    """Read and execute the full schema.sql DDL."""
    schema_sql = _SCHEMA_FILE.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
