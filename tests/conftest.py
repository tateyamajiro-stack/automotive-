from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from hils_manager.database.connection import DatabaseConnection
from hils_manager.database.migrations import run_migrations


@pytest.fixture()
def db_connection(tmp_path: Path) -> DatabaseConnection:
    """Create a fresh in-memory-like DatabaseConnection per test."""
    DatabaseConnection.reset()
    db_path = tmp_path / "test.db"
    db = DatabaseConnection(db_path)
    with db as conn:
        run_migrations(conn)
    yield db
    DatabaseConnection.reset()


@pytest.fixture()
def conn(db_connection: DatabaseConnection) -> sqlite3.Connection:
    return db_connection.get_connection()
