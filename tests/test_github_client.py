"""Tests for GitHub CLI wrapper."""

import json
import pytest
from github_pm.github_client import GitHubClient


class TestGitHubClient:
    """Test suite for GitHubClient."""

    def test_fetch_issues_calls_gh_cli(self, mocker):
        """Test that fetch_issues calls gh CLI with correct parameters."""
        # Mock subprocess.run
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps([
            {
                "number": 1,
                "title": "Test issue",
                "state": "open",
                "labels": [{"name": "bug"}],
                "assignees": [{"login": "user1"}],
                "milestone": {"title": "v1.0"},
                "url": "https://github.com/owner/repo/issues/1",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-02T00:00:00Z",
            }
        ])

        client = GitHubClient()
        issues = client.fetch_issues("owner", "repo")

        # Verify gh CLI was called with correct command
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "gh" in call_args[0][0]
        assert "issue" in call_args[0][0]
        assert "list" in call_args[0][0]
        assert "--repo" in call_args[0][0]
        assert "owner/repo" in call_args[0][0]

        # Verify issues were parsed correctly
        assert len(issues) == 1
        assert issues[0]["number"] == 1
        assert issues[0]["title"] == "Test issue"

    def test_fetch_issues_with_state_filter(self, mocker):
        """Test fetching issues with state filter."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "[]"

        client = GitHubClient()
        client.fetch_issues("owner", "repo", state="closed")

        call_args = mock_run.call_args
        assert "--state" in call_args[0][0]
        assert "closed" in call_args[0][0]

    def test_fetch_issues_with_limit(self, mocker):
        """Test fetching issues with limit."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "[]"

        client = GitHubClient()
        client.fetch_issues("owner", "repo", limit=50)

        call_args = mock_run.call_args
        assert "--limit" in call_args[0][0]
        assert "50" in call_args[0][0]

    def test_fetch_issues_handles_gh_error(self, mocker):
        """Test that fetch_issues handles gh CLI errors gracefully."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Authentication failed"

        client = GitHubClient()
        with pytest.raises(RuntimeError, match="GitHub CLI error"):
            client.fetch_issues("owner", "repo")

    def test_fetch_issues_handles_invalid_json(self, mocker):
        """Test that fetch_issues handles invalid JSON response."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "not valid json"

        client = GitHubClient()
        with pytest.raises(ValueError, match="Invalid JSON"):
            client.fetch_issues("owner", "repo")
