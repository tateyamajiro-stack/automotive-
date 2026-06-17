"""Business logic for project and process management."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hils_manager.models import ProcessSelection, Project
    from hils_manager.repositories.process_repository import ProcessRepository
    from hils_manager.repositories.project_repository import ProjectRepository


class ProjectService:
    """Orchestrates project CRUD and process-selection logic.

    Pure business logic -- no Qt dependency.
    """

    def __init__(
        self,
        project_repo: ProjectRepository,
        process_repo: ProcessRepository,
    ) -> None:
        self._project_repo = project_repo
        self._process_repo = process_repo

    # ------------------------------------------------------------------
    # Project CRUD
    # ------------------------------------------------------------------

    def get_all_projects(self) -> list[Project]:
        """Return every project."""
        return self._project_repo.get_all()

    def get_project(self, project_id: int) -> Project | None:
        """Return a single project by id, or ``None``."""
        return self._project_repo.get_by_id(project_id)

    def create_project(self, project: Project) -> int:
        """Persist a new project and return its id."""
        return self._project_repo.create(project)

    def update_project(self, project: Project) -> None:
        """Update an existing project."""
        self._project_repo.update(project)

    # ------------------------------------------------------------------
    # Process selections
    # ------------------------------------------------------------------

    def get_process_selections(self, project_id: int) -> list[ProcessSelection]:
        """Return process selections for *project_id*.

        If no selections exist yet (first access), the repository is asked to
        create a default set based on :pyclass:`ProcessDefinition` defaults.
        """
        selections = self._process_repo.get_selections(project_id)
        if not selections:
            self._process_repo.initialize_selections(project_id)
            selections = self._process_repo.get_selections(project_id)
        return selections

    def update_process_selection(self, selection: ProcessSelection) -> None:
        """Persist a change to a single process selection."""
        self._process_repo.update_selection(selection)
