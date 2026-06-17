"""Repository for process definition and selection persistence."""

from __future__ import annotations

import sqlite3
from typing import Optional

from hils_manager.constants import ProcessPhase
from hils_manager.models import ProcessDefinition, ProcessSelection

from .base_repository import BaseRepository


class ProcessRepository(BaseRepository):
    """CRUD operations for ``process_definitions`` and ``process_selections`` tables."""

    # ------------------------------------------------------------------
    # Row mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_definition(row: sqlite3.Row) -> ProcessDefinition:
        return ProcessDefinition(
            id=row["id"],
            code=row["code"],
            name_ja=row["name_ja"],
            name_en=row["name_en"] or "",
            phase=ProcessPhase(row["phase"]),
            sort_order=row["sort_order"],
            is_default=bool(row["is_default"]),
        )

    @staticmethod
    def _row_to_selection(row: sqlite3.Row) -> ProcessSelection:
        return ProcessSelection(
            id=row["id"],
            project_id=row["project_id"],
            process_def_id=row["process_def_id"],
            is_selected=bool(row["is_selected"]),
            skip_reason=row["skip_reason"] or "",
            process_name_ja=(
                row["process_name_ja"]
                if "process_name_ja" in row.keys()
                else None
            ),
        )

    # ------------------------------------------------------------------
    # Process definition queries
    # ------------------------------------------------------------------

    def get_all_definitions(self) -> list[ProcessDefinition]:
        """Return all process definitions ordered by phase and sort order."""
        sql = "SELECT * FROM process_definitions ORDER BY sort_order"
        return [self._row_to_definition(r) for r in self._fetchall(sql)]

    # ------------------------------------------------------------------
    # Process selection queries
    # ------------------------------------------------------------------

    def get_selections(self, project_id: int) -> list[ProcessSelection]:
        """Return all process selections for a project, with process names."""
        sql = """
            SELECT ps.*, pd.name_ja AS process_name_ja
            FROM process_selections ps
            JOIN process_definitions pd ON pd.id = ps.process_def_id
            WHERE ps.project_id = ?
            ORDER BY pd.sort_order
        """
        return [
            self._row_to_selection(r)
            for r in self._fetchall(sql, (project_id,))
        ]

    def initialize_selections(self, project_id: int) -> None:
        """Create default process selections for a project from all definitions.

        Each process definition is added with ``is_selected`` set to the
        definition's ``is_default`` flag.  Existing selections for the
        project are left untouched; only missing definitions are inserted.
        """
        definitions = self.get_all_definitions()

        # Fetch already-existing selection definition IDs
        existing_rows = self._fetchall(
            "SELECT process_def_id FROM process_selections WHERE project_id = ?",
            (project_id,),
        )
        existing_ids = {r["process_def_id"] for r in existing_rows}

        for defn in definitions:
            if defn.id not in existing_ids:
                self._execute(
                    """
                    INSERT INTO process_selections
                        (project_id, process_def_id, is_selected, skip_reason)
                    VALUES (?, ?, ?, '')
                    """,
                    (project_id, defn.id, int(defn.is_default)),
                )

    def update_selection(self, selection: ProcessSelection) -> None:
        """Update an existing process selection row."""
        self._execute(
            """
            UPDATE process_selections
            SET is_selected = ?,
                skip_reason = ?
            WHERE id = ?
            """,
            (
                int(selection.is_selected),
                selection.skip_reason,
                selection.id,
            ),
        )
