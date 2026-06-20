"""Business logic for report generation and export."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from jinja2 import Environment, FileSystemLoader

if TYPE_CHECKING:
    from hils_manager.integrations.confluence_client import ConfluenceClient
    from hils_manager.models import Report
    from hils_manager.repositories.report_repo import ReportRepository
    from hils_manager.services.estimate_service import EstimateService
    from hils_manager.services.project_service import ProjectService
    from hils_manager.services.resource_service import ResourceService
    from hils_manager.services.risk_service import RiskService

logger = logging.getLogger(__name__)

# Resolve template directory relative to this file.
_TEMPLATE_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "resources"
    / "templates"
)


# ------------------------------------------------------------------
# Custom Jinja2 filters
# ------------------------------------------------------------------


def _jp_date(dt: Any) -> str:
    """Format a datetime-like value as ``YYYY年MM月DD日``."""
    if dt is None:
        return ""
    if hasattr(dt, "strftime"):
        return dt.strftime("%Y年%m月%d日")
    return str(dt)


def _man_hours(val: Any) -> str:
    """Format a numeric value as ``X.X 人時``."""
    try:
        return f"{float(val):.1f} 人時"
    except (TypeError, ValueError):
        return "0.0 人時"


def _man_days(val: Any) -> str:
    """Format a numeric value as ``X.X 人日``."""
    try:
        return f"{float(val):.1f} 人日"
    except (TypeError, ValueError):
        return "0.0 人日"


class ReportService:
    """Orchestrates report generation, export and Confluence publishing.

    Pure business logic -- no Qt dependency.
    """

    def __init__(
        self,
        report_repo: ReportRepository,
        project_service: ProjectService,
        estimate_service: EstimateService,
        risk_service: RiskService,
        resource_service: ResourceService,
        confluence_client: ConfluenceClient | None = None,
    ) -> None:
        self._report_repo = report_repo
        self._project_service = project_service
        self._estimate_service = estimate_service
        self._risk_service = risk_service
        self._resource_service = resource_service
        self._confluence_client = confluence_client

        self._env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=True,
        )
        self._env.filters["jp_date"] = _jp_date
        self._env.filters["man_hours"] = _man_hours
        self._env.filters["man_days"] = _man_days

    # ------------------------------------------------------------------
    # Data gathering
    # ------------------------------------------------------------------

    def _gather_context(
        self,
        report_type: str,
        project_id: int | None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build the template context from the various services."""
        context: dict[str, Any] = {
            "report_type": report_type,
            "params": params or {},
        }

        if project_id is not None:
            project = self._project_service.get_project(project_id)
            context["project"] = project
            context["estimate_vs_actual"] = (
                self._estimate_service.get_estimate_vs_actual(project_id)
            )
            context["risk_summary"] = self._risk_service.get_risk_summary(
                project_id
            )
            context["assignments"] = (
                self._resource_service.get_project_assignments(project_id)
            )

        return context

    # ------------------------------------------------------------------
    # HTML generation
    # ------------------------------------------------------------------

    def generate_html(
        self,
        report_type: str,
        project_id: int | None,
        params: dict[str, Any] | None = None,
    ) -> str:
        """Render an HTML report using a Jinja2 template.

        The template is loaded from
        ``resources/templates/report_{report_type}.html``.
        """
        context = self._gather_context(report_type, project_id, params)
        template = self._env.get_template(f"report_{report_type}.html")
        return template.render(**context)

    # ------------------------------------------------------------------
    # Confluence generation
    # ------------------------------------------------------------------

    def generate_confluence(
        self,
        report_type: str,
        project_id: int | None,
        params: dict[str, Any] | None = None,
    ) -> str:
        """Render Confluence Storage Format content from a template.

        The template is loaded from
        ``resources/templates/confluence_page.html``.
        """
        context = self._gather_context(report_type, project_id, params)
        template = self._env.get_template("confluence_page.html")
        return template.render(**context)

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    @staticmethod
    def export_html_to_file(html: str, path: Path) -> None:
        """Write rendered HTML to *path*, creating parent dirs if needed."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")

    def push_to_confluence(
        self,
        title: str,
        content: str,
        space_key: str | None = None,
        parent_page_id: str | None = None,
    ) -> str | None:
        """Publish content to Confluence.

        If a page with *title* already exists in the space it is updated;
        otherwise a new page is created.

        Returns the Confluence page URL on success, or ``None`` if no
        client is configured or an error occurs.
        """
        if self._confluence_client is None:
            logger.warning("No Confluence client configured — skipping publish")
            return None

        if not space_key:
            logger.warning("No Confluence space key specified — skipping publish")
            return None

        try:
            # Try to find an existing page by title.
            existing = self._confluence_client.find_page_by_title(space_key, title)
            if existing is not None:
                page_id = existing["id"]
                version = existing.get("version", {}).get("number", 1)
                result = self._confluence_client.update_page(
                    page_id, title, content, version + 1
                )
            else:
                result = self._confluence_client.create_page(
                    space_key, title, content, parent_id=parent_page_id
                )
            links = result.get("_links", {})
            base = links.get("base", "")
            webui = links.get("webui", "")
            return f"{base}{webui}" if base and webui else None
        except Exception:  # noqa: BLE001
            logger.exception("Failed to push to Confluence")
            return None

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_report_record(self, report: Report) -> int:
        """Persist a report record via the repository."""
        return self._report_repo.create(report)
