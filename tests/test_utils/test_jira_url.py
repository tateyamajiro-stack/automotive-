"""Tests for Jira URL utility."""

from hils_manager.utils.jira_url import extract_jira_project_key


class TestExtractJiraProjectKey:
    def test_standard_url(self) -> None:
        url = (
            "https://tateyamajiro.atlassian.net/jira/polaris/projects/YOSHI/"
            "ideas/view/13753945?selectedIssue=YOSHI-7&issueViewSection=overview"
        )
        assert extract_jira_project_key(url) == "YOSHI"

    def test_simple_project_url(self) -> None:
        url = "https://jira.example.com/projects/HILS/board"
        assert extract_jira_project_key(url) == "HILS"

    def test_lowercase_key_normalized(self) -> None:
        url = "https://jira.example.com/projects/myproject/board"
        assert extract_jira_project_key(url) == "MYPROJECT"

    def test_no_projects_segment(self) -> None:
        url = "https://jira.example.com/issues/HILS-123"
        assert extract_jira_project_key(url) is None

    def test_empty_string(self) -> None:
        assert extract_jira_project_key("") is None

    def test_plain_key_no_url(self) -> None:
        assert extract_jira_project_key("HILS") is None

    def test_key_with_numbers(self) -> None:
        url = "https://jira.example.com/projects/PROJ2/settings"
        assert extract_jira_project_key(url) == "PROJ2"
