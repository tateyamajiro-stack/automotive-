"""Utility for extracting Jira project keys from URLs."""

from __future__ import annotations

import re

_PROJECT_KEY_RE = re.compile(r"/projects/([A-Z][A-Z0-9_]+)", re.IGNORECASE)


def extract_jira_project_key(url: str) -> str | None:
    match = _PROJECT_KEY_RE.search(url)
    return match.group(1).upper() if match else None
