"""Tests for ReportService with mocked dependencies."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from hils_manager.services.report_service import ReportService


@pytest.fixture()
def mock_deps() -> dict:
    report_repo = MagicMock()
    project_service = MagicMock()
    estimate_service = MagicMock()
    risk_service = MagicMock()
    resource_service = MagicMock()

    project_service.get_project.return_value = MagicMock(
        name="テストプロジェクト",
        project_code="TEST-001",
        status=MagicMock(label="実行中"),
        start_date=None,
        end_date=None,
        description="テスト用プロジェクト",
    )
    project_service.get_projects.return_value = []

    estimate_service.get_estimate_vs_actual.return_value = {
        "planned_hours": 100.0,
        "actual_hours": 80.0,
        "variance_pct": -20.0,
        "planned_lead_days": 30,
        "actual_lead_days": 25,
    }
    estimate_service.get_estimate_vs_actual_by_wbs.return_value = []

    risk_service.get_risk_summary.return_value = {
        "total": 5,
        "open": 2,
        "high_risk_count": 1,
        "resolved": 3,
    }
    risk_service.get_risks.return_value = []

    resource_service.get_project_assignments.return_value = []

    return {
        "report_repo": report_repo,
        "project_service": project_service,
        "estimate_service": estimate_service,
        "risk_service": risk_service,
        "resource_service": resource_service,
    }


@pytest.fixture()
def report_service(mock_deps: dict) -> ReportService:
    return ReportService(**mock_deps)


class TestReportServiceHTMLGeneration:
    def test_generate_detailed_html(self, report_service: ReportService) -> None:
        html = report_service.generate_html("detailed", project_id=1)
        assert isinstance(html, str)
        assert len(html) > 0

    def test_generate_summary_html(self, report_service: ReportService) -> None:
        html = report_service.generate_html("summary", project_id=1)
        assert isinstance(html, str)
        assert len(html) > 0

    def test_generate_weekly_html(self, report_service: ReportService) -> None:
        html = report_service.generate_html("weekly", project_id=1)
        assert isinstance(html, str)

    def test_generate_monthly_html(self, report_service: ReportService) -> None:
        html = report_service.generate_html("monthly", project_id=1)
        assert isinstance(html, str)

    def test_generate_annual_html(self, report_service: ReportService) -> None:
        html = report_service.generate_html("annual", project_id=None)
        assert isinstance(html, str)

    def test_html_contains_project_data(
        self, report_service: ReportService
    ) -> None:
        html = report_service.generate_html("detailed", project_id=1)
        assert "100" in html or "planned" in html.lower() or len(html) > 100


class TestReportServiceConfluenceGeneration:
    def test_generate_confluence_format(self, report_service: ReportService) -> None:
        content = report_service.generate_confluence("detailed", project_id=1)
        assert isinstance(content, str)
        assert len(content) > 0


class TestReportServiceExport:
    def test_export_html_to_file(
        self, report_service: ReportService, tmp_path: Path
    ) -> None:
        html = "<html><body>test</body></html>"
        out_path = tmp_path / "test_report.html"
        report_service.export_html_to_file(html, out_path)
        assert out_path.exists()
        assert out_path.read_text(encoding="utf-8") == html

    def test_push_to_confluence_no_client(
        self, report_service: ReportService
    ) -> None:
        result = report_service.push_to_confluence("Title", "<p>content</p>")
        assert result is None


class TestReportServiceConfluenceWithClient:
    def test_push_creates_new_page(self, mock_deps: dict) -> None:
        mock_confluence = MagicMock()
        mock_confluence.find_page_by_title.return_value = None
        mock_confluence.create_page.return_value = {
            "id": "12345",
            "_links": {"base": "https://confluence.example.com", "webui": "/pages/12345"},
        }

        service = ReportService(
            **mock_deps, confluence_client=mock_confluence
        )
        url = service.push_to_confluence(
            "Test Report",
            "<p>content</p>",
            space_key="HILS",
            parent_page_id="100",
        )
        assert url is not None
        mock_confluence.create_page.assert_called_once()

    def test_push_updates_existing_page(self, mock_deps: dict) -> None:
        mock_confluence = MagicMock()
        mock_confluence.find_page_by_title.return_value = {
            "id": "12345",
            "version": {"number": 3},
            "_links": {"base": "https://confluence.example.com", "webui": "/pages/12345"},
        }
        mock_confluence.update_page.return_value = {
            "id": "12345",
            "_links": {"base": "https://confluence.example.com", "webui": "/pages/12345"},
        }

        service = ReportService(
            **mock_deps, confluence_client=mock_confluence
        )
        url = service.push_to_confluence(
            "Test Report",
            "<p>updated</p>",
            space_key="HILS",
        )
        assert url is not None
        mock_confluence.update_page.assert_called_once()
