from __future__ import annotations

from datetime import date

from hils_manager.constants import ProjectRole, ProjectStatus
from hils_manager.database.connection import DatabaseConnection
from hils_manager.models.project import Project, ProjectAssignment
from hils_manager.models.team_member import TeamMember
from hils_manager.repositories.member_repo import MemberRepository
from hils_manager.repositories.project_repo import ProjectRepository


class TestProjectRepository:
    def test_create_and_get(self, db_connection: DatabaseConnection) -> None:
        repo = ProjectRepository(db_connection)
        project = Project(
            project_code="PRJ-001",
            name="テスト自動化案件",
            description="HILS環境でのテスト自動化",
            status=ProjectStatus.PLANNING,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 9, 30),
        )
        pid = repo.create(project)
        assert pid > 0

        fetched = repo.get_by_id(pid)
        assert fetched is not None
        assert fetched.name == "テスト自動化案件"
        assert fetched.status == ProjectStatus.PLANNING
        assert fetched.start_date == date(2026, 4, 1)

    def test_status_filter(self, db_connection: DatabaseConnection) -> None:
        repo = ProjectRepository(db_connection)
        repo.create(Project(project_code="P1", name="案件1", status=ProjectStatus.PLANNING))
        repo.create(Project(project_code="P2", name="案件2", status=ProjectStatus.ACTIVE))
        repo.create(Project(project_code="P3", name="案件3", status=ProjectStatus.COMPLETED))

        active = repo.get_all(status_filter=ProjectStatus.ACTIVE)
        assert len(active) == 1
        assert active[0].name == "案件2"

    def test_assignments(self, db_connection: DatabaseConnection) -> None:
        proj_repo = ProjectRepository(db_connection)
        member_repo = MemberRepository(db_connection)

        pid = proj_repo.create(Project(project_code="P1", name="案件1"))
        mid = member_repo.create(TeamMember(employee_id="E01", name="田中"))

        assignment = ProjectAssignment(
            project_id=pid,
            member_id=mid,
            role=ProjectRole.DEVELOPMENT_LEADER,
            allocation_pct=80.0,
        )
        aid = proj_repo.add_assignment(assignment)
        assert aid > 0

        assignments = proj_repo.get_assignments(pid)
        assert len(assignments) == 1
        assert assignments[0].role == ProjectRole.DEVELOPMENT_LEADER
        assert assignments[0].member_name == "田中"

    def test_delete(self, db_connection: DatabaseConnection) -> None:
        repo = ProjectRepository(db_connection)
        pid = repo.create(Project(project_code="P1", name="削除案件"))
        repo.delete(pid)

        assert repo.get_by_id(pid) is None

    def test_get_next_project_code_empty(self, db_connection: DatabaseConnection) -> None:
        repo = ProjectRepository(db_connection)
        assert repo.get_next_project_code() == "PRJ-001"

    def test_get_next_project_code_increments(self, db_connection: DatabaseConnection) -> None:
        repo = ProjectRepository(db_connection)
        repo.create(Project(project_code="PRJ-001", name="案件1"))
        assert repo.get_next_project_code() == "PRJ-002"

        repo.create(Project(project_code="PRJ-002", name="案件2"))
        assert repo.get_next_project_code() == "PRJ-003"

    def test_efficiency_jira_url_field(self, db_connection: DatabaseConnection) -> None:
        repo = ProjectRepository(db_connection)
        project = Project(
            project_code="PRJ-001",
            name="効率化テスト",
            jira_project_key="https://jira.example.com/projects/YOSHI/board",
            efficiency_jira_url="https://jira.example.com/projects/YOSHI/ideas",
        )
        pid = repo.create(project)
        fetched = repo.get_by_id(pid)
        assert fetched is not None
        assert fetched.efficiency_jira_url == "https://jira.example.com/projects/YOSHI/ideas"
        assert fetched.jira_project_key == "https://jira.example.com/projects/YOSHI/board"
