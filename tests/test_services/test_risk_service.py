from __future__ import annotations

import pytest
from datetime import date

from hils_manager.constants import RiskProbability, RiskImpact, RiskStatus
from hils_manager.database.connection import DatabaseConnection
from hils_manager.models.project import Project
from hils_manager.models.risk import Risk
from hils_manager.repositories.project_repo import ProjectRepository
from hils_manager.repositories.risk_repo import RiskRepository
from hils_manager.services.risk_service import RiskService


class TestRiskServiceValidation:
    def test_valid_mitigation(self) -> None:
        is_valid, msg = RiskService.validate_mitigation("代替機材を手配する")
        assert is_valid is True
        assert msg == ""

    def test_empty_mitigation(self) -> None:
        is_valid, msg = RiskService.validate_mitigation("")
        assert is_valid is False

    def test_whitespace_only(self) -> None:
        is_valid, msg = RiskService.validate_mitigation("   ")
        assert is_valid is False

    def test_tbd_rejected(self) -> None:
        is_valid, msg = RiskService.validate_mitigation("TBD")
        assert is_valid is False

    def test_tbd_lowercase_rejected(self) -> None:
        is_valid, msg = RiskService.validate_mitigation("tbd")
        assert is_valid is False

    def test_mitei_rejected(self) -> None:
        is_valid, msg = RiskService.validate_mitigation("未定")
        assert is_valid is False

    def test_youkentou_rejected(self) -> None:
        is_valid, msg = RiskService.validate_mitigation("要検討")
        assert is_valid is False

    def test_atodekimeru_rejected(self) -> None:
        is_valid, msg = RiskService.validate_mitigation("後で決める")
        assert is_valid is False

    def test_na_rejected(self) -> None:
        is_valid, msg = RiskService.validate_mitigation("N/A")
        assert is_valid is False


class TestRiskServiceCRUD:
    def test_create_risk_with_valid_mitigation(self, db_connection: DatabaseConnection) -> None:
        proj_repo = ProjectRepository(db_connection)
        pid = proj_repo.create(Project(project_code="P1", name="テスト"))

        risk_repo = RiskRepository(db_connection)
        service = RiskService(risk_repo)

        risk = Risk(
            project_id=pid,
            risk_number="RISK-001",
            title="テストリスク",
            mitigation="具体的な対策を実施する",
            identified_date=date(2026, 4, 1),
        )
        rid = service.create_risk(risk)
        assert rid > 0

    def test_create_risk_with_tbd_raises(self, db_connection: DatabaseConnection) -> None:
        proj_repo = ProjectRepository(db_connection)
        pid = proj_repo.create(Project(project_code="P1", name="テスト"))

        risk_repo = RiskRepository(db_connection)
        service = RiskService(risk_repo)

        risk = Risk(
            project_id=pid,
            risk_number="RISK-001",
            title="テストリスク",
            mitigation="TBD",
            identified_date=date(2026, 4, 1),
        )
        with pytest.raises(ValueError):
            service.create_risk(risk)

    def test_risk_summary(self, db_connection: DatabaseConnection) -> None:
        proj_repo = ProjectRepository(db_connection)
        pid = proj_repo.create(Project(project_code="P1", name="テスト"))

        risk_repo = RiskRepository(db_connection)
        service = RiskService(risk_repo)

        service.create_risk(Risk(
            project_id=pid, risk_number="R1", title="リスク1",
            probability=RiskProbability.HIGH, impact=RiskImpact.HIGH,
            mitigation="対策1", identified_date=date(2026, 4, 1),
            status=RiskStatus.OPEN,
        ))
        service.create_risk(Risk(
            project_id=pid, risk_number="R2", title="リスク2",
            mitigation="対策2", identified_date=date(2026, 4, 1),
            status=RiskStatus.RESOLVED,
        ))

        summary = service.get_risk_summary(pid)
        assert summary["total"] == 2
        assert summary["open"] >= 1
        assert summary["resolved"] >= 1
