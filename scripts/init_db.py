#!/usr/bin/env python3
"""Initialize the HILS Manager database.

Creates the SQLite database file, applies schema, and seeds process definitions.
Can be run standalone or imported.
"""
from __future__ import annotations

import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_dir))

from hils_manager.database.connection import DatabaseConnection
from hils_manager.database.migrations import run_migrations


def main(db_path: Path | None = None) -> None:
    if db_path is None:
        db_path = Path.cwd() / "data" / "hils_manager.db"

    db_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"データベース初期化: {db_path}")

    DatabaseConnection.reset()
    db = DatabaseConnection(db_path)
    with db as conn:
        run_migrations(conn)

    print("データベースの初期化が完了しました。")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    main(target)
