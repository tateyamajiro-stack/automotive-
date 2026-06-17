from __future__ import annotations

from hils_manager.database.connection import DatabaseConnection
from hils_manager.models.team_member import TeamMember
from hils_manager.repositories.member_repo import MemberRepository


class TestMemberRepository:
    def test_create_and_get(self, db_connection: DatabaseConnection) -> None:
        repo = MemberRepository(db_connection)
        member = TeamMember(
            employee_id="EMP001",
            name="田中太郎",
            email="tanaka@example.com",
            is_outsourced=False,
            skills=["Python", "HILS"],
        )
        new_id = repo.create(member)
        assert new_id > 0

        fetched = repo.get_by_id(new_id)
        assert fetched is not None
        assert fetched.name == "田中太郎"
        assert fetched.employee_id == "EMP001"
        assert "Python" in fetched.skills

    def test_get_all(self, db_connection: DatabaseConnection) -> None:
        repo = MemberRepository(db_connection)
        repo.create(TeamMember(employee_id="E01", name="メンバー1"))
        repo.create(TeamMember(employee_id="E02", name="メンバー2"))

        all_members = repo.get_all()
        assert len(all_members) == 2

    def test_update(self, db_connection: DatabaseConnection) -> None:
        repo = MemberRepository(db_connection)
        mid = repo.create(TeamMember(employee_id="E01", name="元の名前"))

        member = repo.get_by_id(mid)
        assert member is not None
        member.name = "新しい名前"
        member.email = "new@example.com"
        repo.update(member)

        updated = repo.get_by_id(mid)
        assert updated is not None
        assert updated.name == "新しい名前"
        assert updated.email == "new@example.com"

    def test_soft_delete(self, db_connection: DatabaseConnection) -> None:
        repo = MemberRepository(db_connection)
        mid = repo.create(TeamMember(employee_id="E01", name="削除対象"))

        repo.delete(mid)

        active = repo.get_all(active_only=True)
        assert len(active) == 0

        all_members = repo.get_all(active_only=False)
        assert len(all_members) == 1
        assert all_members[0].is_active is False

    def test_outsourced_members(self, db_connection: DatabaseConnection) -> None:
        repo = MemberRepository(db_connection)
        repo.create(TeamMember(employee_id="P01", name="プロパー", is_outsourced=False))
        repo.create(
            TeamMember(
                employee_id="OS01",
                name="OS太郎",
                is_outsourced=True,
                daily_rate=50000.0,
            )
        )

        os_members = repo.get_outsourced_members()
        assert len(os_members) == 1
        assert os_members[0].name == "OS太郎"
        assert os_members[0].daily_rate == 50000.0
