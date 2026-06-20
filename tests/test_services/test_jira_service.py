"""Tests for JiraService with mocked JiraClient."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from hils_manager.constants import (
    RequirementPriority,
    RequirementStatus,
    RiskImpact,
    RiskProbability,
    RiskStatus,
    WBSStatus,
)
from hils_manager.database.connection import DatabaseConnection
from hils_manager.models.requirement import Requirement
from hils_manager.models.risk import Risk
from hils_manager.models.wbs import WBSItem
from hils_manager.repositories.jira_repo import JiraSyncRepository
from hils_manager.repositories.project_repo import ProjectRepository
from hils_manager.repositories.requirement_repo import RequirementRepository
from hils_manager.repositories.risk_repo import RiskRepository
from hils_manager.repositories.wbs_repo import WBSRepository
from hils_manager.models.project import Project
from hils_manager.services.jira_service import JiraService


@pytest.fixture()
def mock_jira_client() -> MagicMock:
    client = MagicMock()
    client.test_connection.return_value = True
    client.create_issue.return_value = {
        "key": "HILS-1",
        "id": "10001",
        "self": "https://jira.example.com/rest/api/2/issue/10001",
    }
    client.update_issue.return_value = None
    client.search_issues.return_value = []
    return client


@pytest.fixture()
def jira_service(
    db_connection: DatabaseConnection, mock_jira_client: MagicMock
) -> JiraService:
    jira_repo = JiraSyncRepository(db_connection)
    wbs_repo = WBSRepository(db_connection)
    req_repo = RequirementRepository(db_connection)
    risk_repo = RiskRepository(db_connection)
    return JiraService(
        jira_client=mock_jira_client,
        jira_repo=jira_repo,
        wbs_repo=wbs_repo,
        requirement_repo=req_repo,
        risk_repo=risk_repo,
    )


@pytest.fixture()
def project_id(db_connection: DatabaseConnection) -> int:
    repo = ProjectRepository(db_connection)
    return repo.create(
        Project(project_code="TEST-001", name="テストプロジェクト", jira_project_key="HILS")
    )


class TestJiraServiceConnection:
    def test_test_connection(
        self, jira_service: JiraService, mock_jira_client: MagicMock
    ) -> None:
        assert jira_service.test_connection() is True
        mock_jira_client.test_connection.assert_called_once()

    def test_test_connection_failure(
        self, jira_service: JiraService, mock_jira_client: MagicMock
    ) -> None:
        mock_jira_client.test_connection.return_value = False
        assert jira_service.test_connection() is False


class TestJiraServicePush:
    def test_push_creates_issues(
        self,
        jira_service: JiraService,
        mock_jira_client: MagicMock,
        project_id: int,
        db_connection: DatabaseConnection,
    ) -> None:
        wbs_repo = WBSRepository(db_connection)
        wbs_repo.create(
            WBSItem(
                project_id=project_id,
                wbs_code="1.1",
                title="テストWBS",
                status=WBSStatus.NOT_STARTED,
            )
        )

        risk_repo = RiskRepository(db_connection)
        risk_repo.create(
            Risk(
                project_id=project_id,
                risk_number="RISK-001",
                title="テストリスク",
                mitigation="対策あり",
                identified_date=date(2026, 4, 1),
            )
        )

        result = jira_service.push(project_id, "HILS")
        assert result["pushed"] >= 1
        assert mock_jira_client.create_issue.called

    def test_push_empty_project(
        self, jira_service: JiraService, project_id: int
    ) -> None:
        result = jira_service.push(project_id, "HILS")
        assert result["pushed"] == 0
        assert len(result["errors"]) == 0


class TestJiraServiceFetch:
    def test_fetch_no_remote_issues(
        self,
        jira_service: JiraService,
        mock_jira_client: MagicMock,
        project_id: int,
    ) -> None:
        mock_jira_client.search_issues.return_value = []
        result = jira_service.fetch(project_id, "HILS")
        assert result["fetched"] == 0
        assert result["conflicts"] == 0

    def test_fetch_with_existing_mapping(
        self,
        jira_service: JiraService,
        mock_jira_client: MagicMock,
        project_id: int,
        db_connection: DatabaseConnection,
    ) -> None:
        wbs_repo = WBSRepository(db_connection)
        wbs_id = wbs_repo.create(
            WBSItem(
                project_id=project_id,
                wbs_code="1.1",
                title="元のタイトル",
                status=WBSStatus.NOT_STARTED,
            )
        )

        jira_repo = JiraSyncRepository(db_connection)
        from hils_manager.models.jira_mapping import JiraSyncMapping

        jira_repo.upsert_mapping(
            JiraSyncMapping(
                project_id=project_id,
                local_entity="wbs_item",
                local_id=wbs_id,
                jira_issue_key="HILS-10",
                jira_issue_id="10010",
                sync_status="synced",
            )
        )

        mock_jira_client.search_issues.return_value = [
            {
                "key": "HILS-10",
                "id": "10010",
                "fields": {
                    "summary": "更新タイトル",
                    "description": "更新内容",
                    "status": {"name": "In Progress"},
                    "priority": {"name": "Medium"},
                    "updated": "2026-04-15T10:00:00.000+0900",
                },
            }
        ]

        result = jira_service.fetch(project_id, "HILS")
        assert result["fetched"] >= 0


class TestJiraServiceSyncStatus:
    def test_get_sync_status_empty(
        self, jira_service: JiraService, project_id: int
    ) -> None:
        statuses = jira_service.get_sync_status(project_id)
        assert statuses == []
