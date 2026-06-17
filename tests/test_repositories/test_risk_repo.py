from __future__ import annotations

from datetime import date

from hils_manager.constants import RiskImpact, RiskProbability, RiskStatus
from hils_manager.database.connection import DatabaseConnection
from hils_manager.models.project import Project
from hils_manager.models.risk import Risk
from hils_manager.repositories.project_repo import ProjectRepository
from hils_manager.repositories.risk_repo import RiskRepository


class TestRiskRepository:
    def _create_project(self, db_connection: DatabaseConnection) -> int:
        repo = ProjectRepository(db_connection)
        return repo.create(Project(project_code="P1", name="テスト案件"))

    def test_create_and_get(self, db_connection: DatabaseConnection) -> None:
        pid = self._create_project(db_connection)
        repo = RiskRepository(db_connection)

        risk = Risk(
            project_id=pid,
            risk_number="RISK-001",
            title="HILS環境の納期遅延",
            description="HILS機材の納品が遅れるリスク",
            probability=RiskProbability.HIGH,
            impact=RiskImpact.HIGH,
            mitigation="代替機材の手配と並行検証環境の確保",
            status=RiskStatus.OPEN,
            identified_date=date(2026, 4, 1),
        )
        rid = repo.create(risk)
        assert rid > 0

        fetched = repo.get_by_id(rid)
        assert fetched is not None
        assert fetched.title == "HILS環境の納期遅延"
        assert fetched.probability == RiskProbability.HIGH
        assert fetched.mitigation == "代替機材の手配と並行検証環境の確保"

    def test_open_risks_count(self, db_connection: DatabaseConnection) -> None:
        pid = self._create_project(db_connection)
        repo = RiskRepository(db_connection)

        repo.create(Risk(
            project_id=pid, risk_number="R1", title="リスク1",
            mitigation="対策1", identified_date=date(2026, 4, 1),
            status=RiskStatus.OPEN,
        ))
        repo.create(Risk(
            project_id=pid, risk_number="R2", title="リスク2",
            mitigation="対策2", identified_date=date(2026, 4, 1),
            status=RiskStatus.RESOLVED,
        ))

        assert repo.get_open_risks_count(pid) == 1

    def test_next_risk_number(self, db_connection: DatabaseConnection) -> None:
        pid = self._create_project(db_connection)
        repo = RiskRepository(db_connection)

        num = repo.get_next_risk_number(pid)
        assert num == "RISK-001"

        repo.create(Risk(
            project_id=pid, risk_number=num, title="リスク1",
            mitigation="対策1", identified_date=date(2026, 4, 1),
        ))
        assert repo.get_next_risk_number(pid) == "RISK-002"
