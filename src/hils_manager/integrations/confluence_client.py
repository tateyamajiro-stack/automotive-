"""REST client for Confluence Data Center (PAT / Bearer authentication)."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Exceptions
# ------------------------------------------------------------------


class ConfluenceApiError(Exception):
    """Raised when the Confluence REST API returns a non-2xx response."""

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


class ConfluenceClient:
    """Thin wrapper around the Confluence Data Center REST API.

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
                        "Confluence %s %s returned %s (attempt %d/%d)",
                        method,
                        path,
                        resp.status_code,
                        attempt + 1,
                        _MAX_RETRIES,
                    )
                    last_exc = ConfluenceApiError(
                        f"Server error {resp.status_code}",
                        status_code=resp.status_code,
                        response_body=resp.text,
                    )
                    time.sleep(_BACKOFF_SECONDS[attempt])
                    continue

                if not resp.ok:
                    raise ConfluenceApiError(
                        f"Confluence API error: {resp.status_code} {resp.reason}",
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
                last_exc = ConfluenceApiError(
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
            self._request("GET", "/rest/api/user/current")
            return True
        except (ConfluenceApiError, requests.RequestException):
            return False

    def create_page(
        self,
        space_key: str,
        title: str,
        body_storage: str,
        parent_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new page in the given space.

        *body_storage* should be Confluence storage-format XHTML.
        If *parent_id* is provided the page is created as a child.
        """
        payload: dict[str, Any] = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": body_storage,
                    "representation": "storage",
                }
            },
        }
        if parent_id is not None:
            payload["ancestors"] = [{"id": parent_id}]

        resp = self._request("POST", "/rest/api/content", json=payload)
        return resp.json()  # type: ignore[no-any-return]

    def update_page(
        self,
        page_id: str,
        title: str,
        body_storage: str,
        version: int,
    ) -> dict[str, Any]:
        """Update an existing page.

        *version* must be the **next** version number (current + 1).
        """
        payload: dict[str, Any] = {
            "type": "page",
            "title": title,
            "version": {"number": version},
            "body": {
                "storage": {
                    "value": body_storage,
                    "representation": "storage",
                }
            },
        }
        resp = self._request(
            "PUT", f"/rest/api/content/{page_id}", json=payload
        )
        return resp.json()  # type: ignore[no-any-return]

    def get_page(self, page_id: str) -> dict[str, Any]:
        """Fetch a page by ID, including its storage-format body."""
        resp = self._request(
            "GET",
            f"/rest/api/content/{page_id}",
            params={"expand": "body.storage,version"},
        )
        return resp.json()  # type: ignore[no-any-return]

    def find_page_by_title(
        self, space_key: str, title: str
    ) -> dict[str, Any] | None:
        """Search for a page by exact title within a space.

        Returns the first matching page dict, or ``None`` if no match
        is found.
        """
        resp = self._request(
            "GET",
            "/rest/api/content",
            params={
                "spaceKey": space_key,
                "title": title,
                "expand": "body.storage,version",
            },
        )
        results = resp.json().get("results", [])
        return results[0] if results else None
