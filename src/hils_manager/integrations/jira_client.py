"""REST client for Jira Data Center (PAT / Bearer authentication)."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Exceptions
# ------------------------------------------------------------------


class JiraApiError(Exception):
    """Raised when the Jira REST API returns a non-2xx response."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str = "",
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


# ------------------------------------------------------------------
# Client
# ------------------------------------------------------------------

_MAX_RETRIES = 3
_BACKOFF_SECONDS = (1, 2, 4)


class JiraClient:
    """Thin wrapper around the Jira Data Center REST API v2.

    Uses a :pymod:`requests` session with ``Authorization: Bearer``
    header derived from the provided Personal Access Token.
    """

    def __init__(self, base_url: str, pat: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {pat}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self._base_url}{path}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        """Execute an HTTP request with retry on 5xx / connection errors."""
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = self._session.request(
                    method,
                    self._url(path),
                    json=json,
                    params=params,
                    timeout=30,
                )
                if resp.status_code >= 500:
                    logger.warning(
                        "Jira %s %s returned %s (attempt %d/%d)",
                        method,
                        path,
                        resp.status_code,
                        attempt + 1,
                        _MAX_RETRIES,
                    )
                    last_exc = JiraApiError(
                        f"Server error {resp.status_code}",
                        status_code=resp.status_code,
                        response_body=resp.text,
                    )
                    time.sleep(_BACKOFF_SECONDS[attempt])
                    continue

                if not resp.ok:
                    raise JiraApiError(
                        f"Jira API error: {resp.status_code} {resp.reason}",
                        status_code=resp.status_code,
                        response_body=resp.text,
                    )
                return resp

            except requests.ConnectionError as exc:
                logger.warning(
                    "Connection error for %s %s (attempt %d/%d): %s",
                    method,
                    path,
                    attempt + 1,
                    _MAX_RETRIES,
                    exc,
                )
                last_exc = JiraApiError(
                    f"Connection error: {exc}",
                    status_code=None,
                    response_body="",
                )
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(_BACKOFF_SECONDS[attempt])

        # All retries exhausted.
        raise last_exc  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def test_connection(self) -> bool:
        """Verify connectivity by fetching the authenticated user profile.

        Returns ``True`` on success, ``False`` on any API / network
        error.
        """
        try:
            self._request("GET", "/rest/api/2/myself")
            return True
        except (JiraApiError, requests.RequestException):
            return False

    def get_issue(self, key: str) -> dict[str, Any]:
        """Fetch a single issue by its key (e.g. ``PROJ-123``)."""
        resp = self._request("GET", f"/rest/api/2/issue/{key}")
        return resp.json()  # type: ignore[no-any-return]

    def create_issue(
        self,
        project_key: str,
        issue_type: str,
        fields: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a new issue and return the API response.

        *fields* should contain at minimum ``summary``.  The
        ``project`` and ``issuetype`` fields are injected
        automatically.
        """
        payload: dict[str, Any] = {
            "fields": {
                "project": {"key": project_key},
                "issuetype": {"name": issue_type},
                **fields,
            }
        }
        resp = self._request("POST", "/rest/api/2/issue", json=payload)
        return resp.json()  # type: ignore[no-any-return]

    def update_issue(self, key: str, fields: dict[str, Any]) -> None:
        """Update fields on an existing issue."""
        self._request(
            "PUT", f"/rest/api/2/issue/{key}", json={"fields": fields}
        )

    def search_issues(
        self,
        jql: str,
        fields: list[str] | None = None,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        """Run a JQL search and return the list of matching issues."""
        params: dict[str, Any] = {"jql": jql, "maxResults": max_results}
        if fields is not None:
            params["fields"] = ",".join(fields)
        resp = self._request("GET", "/rest/api/2/search", params=params)
        return resp.json().get("issues", [])  # type: ignore[no-any-return]

    def get_project(self, key: str) -> dict[str, Any]:
        """Fetch project metadata by key."""
        resp = self._request("GET", f"/rest/api/2/project/{key}")
        return resp.json()  # type: ignore[no-any-return]

    def get_transitions(self, issue_key: str) -> list[dict[str, Any]]:
        """Return available workflow transitions for an issue."""
        resp = self._request(
            "GET", f"/rest/api/2/issue/{issue_key}/transitions"
        )
        return resp.json().get("transitions", [])  # type: ignore[no-any-return]

    def transition_issue(
        self, issue_key: str, transition_id: str
    ) -> None:
        """Execute a workflow transition on an issue."""
        self._request(
            "POST",
            f"/rest/api/2/issue/{issue_key}/transitions",
            json={"transition": {"id": transition_id}},
        )
