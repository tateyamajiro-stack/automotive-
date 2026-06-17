"""Business logic for team-member and project-assignment management."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hils_manager.constants import ProjectRole
    from hils_manager.models import Project, ProjectAssignment, TeamMember
    from hils_manager.repositories.member_repository import MemberRepository
    from hils_manager.repositories.project_repository import ProjectRepository


@dataclass
class ResourceAllocation:
    """A single allocation entry used by :pymeth:`ResourceService.get_resource_overview`."""

    project: Project
    role: ProjectRole
    allocation_pct: float


class ResourceService:
    """Orchestrates member / assignment logic across projects.

    Pure business logic -- no Qt dependency.
    """

    def __init__(
        self,
        member_repo: MemberRepository,
        project_repo: ProjectRepository,
    ) -> None:
        self._member_repo = member_repo
        self._project_repo = project_repo

    # ------------------------------------------------------------------
    # Member CRUD
    # ------------------------------------------------------------------

    def get_all_members(self) -> list[TeamMember]:
        """Return every team member."""
        return self._member_repo.get_all()

    def get_member(self, member_id: int) -> TeamMember | None:
        """Return a single member by id, or ``None``."""
        return self._member_repo.get_by_id(member_id)

    def create_member(self, member: TeamMember) -> int:
        """Persist a new member and return its id."""
        return self._member_repo.create(member)

    def update_member(self, member: TeamMember) -> None:
        """Update an existing member."""
        self._member_repo.update(member)

    def deactivate_member(self, member_id: int) -> None:
        """Soft-delete a member by setting ``is_active = False``."""
        member = self._member_repo.get_by_id(member_id)
        if member is not None:
            member.is_active = False
            self._member_repo.update(member)

    # ------------------------------------------------------------------
    # Assignments
    # ------------------------------------------------------------------

    def get_project_assignments(self, project_id: int) -> list[ProjectAssignment]:
        """Return all member assignments for *project_id*."""
        return self._project_repo.get_assignments(project_id)

    def assign_member(
        self,
        project_id: int,
        member_id: int,
        role: ProjectRole,
        allocation_pct: float,
    ) -> int:
        """Assign a member to a project and return the assignment id."""
        from hils_manager.models import ProjectAssignment

        assignment = ProjectAssignment(
            project_id=project_id,
            member_id=member_id,
            role=role,
            allocation_pct=allocation_pct,
        )
        return self._project_repo.add_assignment(assignment)

    def unassign_member(self, assignment_id: int) -> None:
        """Remove an assignment."""
        self._project_repo.remove_assignment(assignment_id)

    # ------------------------------------------------------------------
    # Unassigned queries
    # ------------------------------------------------------------------

    def get_unassigned_members(self) -> list[TeamMember]:
        """Return active members that are not assigned to any active project."""
        return self._member_repo.get_unassigned_members()

    def get_unassigned_outsourced_members(self) -> list[TeamMember]:
        """Return outsourced members not assigned to any active project.

        This is a **critical alert** condition -- outsourced members without
        work still incur cost.
        """
        return self._member_repo.get_outsourced_members()

    # ------------------------------------------------------------------
    # Cross-project resource overview
    # ------------------------------------------------------------------

    def get_resource_overview(self) -> dict[int, list[ResourceAllocation]]:
        """Build a cross-project view of every member's allocations.

        Returns a mapping of ``member_id`` to a list of
        :pyclass:`ResourceAllocation` entries, one per active project the
        member participates in.
        """
        members = self._member_repo.get_all()
        overview: dict[int, list[ResourceAllocation]] = {}

        for member in members:
            if not member.is_active or member.id is None:
                continue

            projects = self._project_repo.get_active_projects_for_member(member.id)
            allocations: list[ResourceAllocation] = []
            for project in projects:
                if project.id is None:
                    continue
                assignments = self._project_repo.get_assignments(project.id)
                for assignment in assignments:
                    if assignment.member_id == member.id:
                        allocations.append(
                            ResourceAllocation(
                                project=project,
                                role=assignment.role,
                                allocation_pct=assignment.allocation_pct,
                            )
                        )
            if allocations:
                overview[member.id] = allocations

        return overview
