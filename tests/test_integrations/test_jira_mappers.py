"""Tests for Jira field mappers."""

from __future__ import annotations

from datetime import date

from hils_manager.constants import (
    RequirementPriority,
    RequirementStatus,
    RiskImpact,
    RiskProbability,
    RiskStatus,
    WBSStatus,
)
from hils_manager.models.requirement import Requirement
from hils_manager.models.risk import Risk
from hils_manager.models.wbs import WBSItem
from hils_manager.integrations.jira_mappers import (
    wbs_to_jira,
    requirement_to_jira,
    risk_to_jira,
    jira_to_wbs_fields,
    jira_to_requirement_fields,
    jira_to_risk_fields,
)


class TestWBSMapper:
    def test_wbs_to_jira_basic(self) -> None:
        wbs = WBSItem(
            wbs_code="1.1",
            title="テスト仕様作成",
            description="テスト仕様書を作成する",
            status=WBSStatus.IN_PROGRESS,
            planned_start=date(2026, 4, 1),
            planned_end=date(2026, 4, 30),
        )
        fields = wbs_to_jira(wbs)
        assert fields["summary"] == "テスト仕様作成"
        assert "テスト仕様書を作成する" in fields["description"]
        assert "priority" in fields

    def test_jira_to_wbs_fields(self) -> None:
        jira_issue = {
            "fields": {
                "summary": "Updated Title",
                "description": "Updated description",
                "status": {"name": "In Progress"},
                "priority": {"name": "High"},
            }
        }
        result = jira_to_wbs_fields(jira_issue)
        assert result["title"] == "Updated Title"
        assert result["description"] == "Updated description"


class TestRequirementMapper:
    def test_requirement_to_jira(self) -> None:
        req = Requirement(
            req_number="REQ-001",
            title="自動テスト機能",
            description="自動テスト実行機能を追加する",
            priority=RequirementPriority.HIGH,
            status=RequirementStatus.ACCEPTED,
        )
        fields = requirement_to_jira(req)
        assert fields["summary"] == "自動テスト機能"
        assert "自動テスト実行機能を追加する" in fields["description"]
        assert fields["priority"]["name"] == "High"

    def test_jira_to_requirement_fields(self) -> None:
        jira_issue = {
            "fields": {
                "summary": "New Requirement",
                "description": "Some description",
                "priority": {"name": "Medium"},
                "status": {"name": "To Do"},
            }
        }
        result = jira_to_requirement_fields(jira_issue)
        assert result["title"] == "New Requirement"
        assert result["description"] == "Some description"


class TestRiskMapper:
    def test_risk_to_jira(self) -> None:
        risk = Risk(
            risk_number="RISK-001",
            title="機材不足リスク",
            description="テスト用機材が不足する可能性",
            probability=RiskProbability.HIGH,
            impact=RiskImpact.HIGH,
            mitigation="代替機材を事前手配する",
            status=RiskStatus.OPEN,
        )
        fields = risk_to_jira(risk)
        assert fields["summary"] == "機材不足リスク"
        assert "代替機材を事前手配する" in fields["description"]
        assert fields["priority"]["name"] == "High"

    def test_risk_with_medium_priority(self) -> None:
        risk = Risk(
            risk_number="RISK-002",
            title="スケジュール遅延",
            probability=RiskProbability.MEDIUM,
            impact=RiskImpact.MEDIUM,
            mitigation="バッファを確保する",
            status=RiskStatus.MITIGATING,
        )
        fields = risk_to_jira(risk)
        assert fields["priority"]["name"] == "Medium"

    def test_jira_to_risk_fields(self) -> None:
        jira_issue = {
            "fields": {
                "summary": "Risk from Jira",
                "description": "Risk description\n\n対策: Fix it",
                "priority": {"name": "High"},
                "status": {"name": "Open"},
            }
        }
        result = jira_to_risk_fields(jira_issue)
        assert result["title"] == "Risk from Jira"
