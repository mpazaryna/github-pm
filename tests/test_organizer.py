"""Tests for issue organizer."""

import pytest
from github_pm.organizer import IssueOrganizer


class TestIssueOrganizer:
    """Test suite for IssueOrganizer."""

    @pytest.fixture
    def sample_issues(self):
        """Sample issues for testing."""
        return [
            {
                "number": 1,
                "title": "Bug in feature A",
                "state": "open",
                "labels": [{"name": "bug"}, {"name": "priority-high"}],
                "assignees": [{"login": "user1"}],
                "milestone": {"title": "v1.0"},
                "url": "https://github.com/owner/repo1/issues/1",
                "repository": "owner/repo1",
            },
            {
                "number": 2,
                "title": "Feature request B",
                "state": "open",
                "labels": [{"name": "enhancement"}],
                "assignees": [],
                "milestone": {"title": "v2.0"},
                "url": "https://github.com/owner/repo1/issues/2",
                "repository": "owner/repo1",
            },
            {
                "number": 3,
                "title": "Bug in feature C",
                "state": "open",
                "labels": [{"name": "bug"}],
                "assignees": [{"login": "user2"}],
                "milestone": None,
                "url": "https://github.com/owner/repo2/issues/3",
                "repository": "owner/repo2",
            },
        ]

    def test_organize_by_repository(self, sample_issues):
        """Test organizing issues by repository."""
        organizer = IssueOrganizer()
        organized = organizer.organize_by_repository(sample_issues)

        assert "owner/repo1" in organized
        assert "owner/repo2" in organized
        assert len(organized["owner/repo1"]) == 2
        assert len(organized["owner/repo2"]) == 1
        assert organized["owner/repo1"][0]["number"] == 1
        assert organized["owner/repo2"][0]["number"] == 3

    def test_organize_by_labels(self, sample_issues):
        """Test organizing issues by labels."""
        organizer = IssueOrganizer()
        organized = organizer.organize_by_labels(sample_issues)

        assert "bug" in organized
        assert "enhancement" in organized
        assert "priority-high" in organized
        assert len(organized["bug"]) == 2
        assert len(organized["enhancement"]) == 1
        assert organized["bug"][0]["number"] in [1, 3]

    def test_organize_by_milestone(self, sample_issues):
        """Test organizing issues by milestone."""
        organizer = IssueOrganizer()
        organized = organizer.organize_by_milestone(sample_issues)

        assert "v1.0" in organized
        assert "v2.0" in organized
        assert "No Milestone" in organized
        assert len(organized["v1.0"]) == 1
        assert len(organized["v2.0"]) == 1
        assert len(organized["No Milestone"]) == 1
        assert organized["v1.0"][0]["number"] == 1
        assert organized["No Milestone"][0]["number"] == 3

    def test_organize_by_assignee(self, sample_issues):
        """Test organizing issues by assignee."""
        organizer = IssueOrganizer()
        organized = organizer.organize_by_assignee(sample_issues)

        assert "user1" in organized
        assert "user2" in organized
        assert "Unassigned" in organized
        assert len(organized["user1"]) == 1
        assert len(organized["user2"]) == 1
        assert len(organized["Unassigned"]) == 1

    def test_organize_empty_list(self):
        """Test organizing an empty list of issues."""
        organizer = IssueOrganizer()
        organized = organizer.organize_by_repository([])

        assert organized == {}

    def test_organize_issues_without_labels(self):
        """Test organizing issues that have no labels."""
        issues = [
            {
                "number": 1,
                "labels": [],
                "repository": "owner/repo",
            }
        ]
        organizer = IssueOrganizer()
        organized = organizer.organize_by_labels(issues)

        assert organized == {}
