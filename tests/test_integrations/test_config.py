"""Tests for ConnectionConfig PAT encryption round-trip."""

from __future__ import annotations

from pathlib import Path

import pytest

from hils_manager.database.connection import DatabaseConnection
from hils_manager.database.migrations import run_migrations
from hils_manager.repositories.settings_repo import SettingsRepository
from hils_manager.integrations.config import ConnectionConfig


@pytest.fixture()
def config(db_connection: DatabaseConnection) -> ConnectionConfig:
    settings_repo = SettingsRepository(db_connection)
    return ConnectionConfig(settings_repo)


class TestConnectionConfig:
    def test_jira_not_configured_initially(self, config: ConnectionConfig) -> None:
        assert config.is_jira_configured() is False
        assert config.get_jira_config() is None

    def test_confluence_not_configured_initially(self, config: ConnectionConfig) -> None:
        assert config.is_confluence_configured() is False
        assert config.get_confluence_config() is None

    def test_set_and_get_jira_config(self, config: ConnectionConfig) -> None:
        config.set_jira_config(
            "https://jira.example.com", "my-secret-pat", "HILS"
        )
        assert config.is_jira_configured() is True
        cfg = config.get_jira_config()
        assert cfg is not None
        assert cfg["base_url"] == "https://jira.example.com"
        assert cfg["pat"] == "my-secret-pat"
        assert cfg["default_project_key"] == "HILS"

    def test_set_and_get_confluence_config(self, config: ConnectionConfig) -> None:
        config.set_confluence_config(
            "https://confluence.example.com", "conf-pat", "HILS", "12345"
        )
        assert config.is_confluence_configured() is True
        cfg = config.get_confluence_config()
        assert cfg is not None
        assert cfg["base_url"] == "https://confluence.example.com"
        assert cfg["pat"] == "conf-pat"
        assert cfg["space_key"] == "HILS"
        assert cfg["parent_page_id"] == "12345"

    def test_pat_round_trip_encryption(self, config: ConnectionConfig) -> None:
        original_pat = "a-very-secret-token-12345"
        config.set_jira_config("https://jira.test.com", original_pat)
        retrieved = config.get_jira_config()
        assert retrieved is not None
        assert retrieved["pat"] == original_pat

    def test_clear_jira_config(self, config: ConnectionConfig) -> None:
        config.set_jira_config("https://jira.test.com", "pat123")
        assert config.is_jira_configured() is True
        config.clear_jira_config()
        assert config.is_jira_configured() is False
        assert config.get_jira_config() is None

    def test_clear_confluence_config(self, config: ConnectionConfig) -> None:
        config.set_confluence_config("https://conf.test.com", "pat456", "SP", "1")
        assert config.is_confluence_configured() is True
        config.clear_confluence_config()
        assert config.is_confluence_configured() is False
        assert config.get_confluence_config() is None

    def test_update_existing_config(self, config: ConnectionConfig) -> None:
        config.set_jira_config("https://old.com", "old-pat")
        config.set_jira_config("https://new.com", "new-pat", "NEWKEY")
        cfg = config.get_jira_config()
        assert cfg is not None
        assert cfg["base_url"] == "https://new.com"
        assert cfg["pat"] == "new-pat"
        assert cfg["default_project_key"] == "NEWKEY"
