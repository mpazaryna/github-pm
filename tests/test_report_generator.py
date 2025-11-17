"""Tests for markdown report generator."""

import pytest
from datetime import datetime
from github_pm.report_generator import MarkdownReportGenerator


class TestMarkdownReportGenerator:
    """Test suite for MarkdownReportGenerator."""

    @pytest.fixture
    def sample_organized_issues(self):
        """Sample organized issues for testing."""
        return {
            "owner/repo1": [
                {
                    "number": 1,
                    "title": "Bug in feature A",
                    "state": "open",
                    "labels": [{"name": "bug"}, {"name": "priority-high"}],
                    "assignees": [{"login": "user1"}],
                    "milestone": {"title": "v1.0"},
                    "url": "https://github.com/owner/repo1/issues/1",
                    "createdAt": "2025-01-01T00:00:00Z",
                },
                {
                    "number": 2,
                    "title": "Feature request B",
                    "state": "open",
                    "labels": [{"name": "enhancement"}],
                    "assignees": [],
                    "milestone": {"title": "v2.0"},
                    "url": "https://github.com/owner/repo1/issues/2",
                    "createdAt": "2025-01-02T00:00:00Z",
                },
            ],
            "owner/repo2": [
                {
                    "number": 3,
                    "title": "Bug in feature C",
                    "state": "open",
                    "labels": [{"name": "bug"}],
                    "assignees": [{"login": "user2"}],
                    "milestone": None,
                    "url": "https://github.com/owner/repo2/issues/3",
                    "createdAt": "2025-01-03T00:00:00Z",
                },
            ],
        }

    def test_generate_report_includes_header(self, sample_organized_issues):
        """Test that report includes a header."""
        generator = MarkdownReportGenerator()
        report = generator.generate_report(sample_organized_issues)

        assert "# GitHub Issues Report" in report
        assert "Generated on:" in report

    def test_generate_report_includes_summary(self, sample_organized_issues):
        """Test that report includes a summary section."""
        generator = MarkdownReportGenerator()
        report = generator.generate_report(sample_organized_issues)

        assert "## Summary" in report
        assert "Total Issues: 3" in report
        assert "Total Repositories: 2" in report

    def test_generate_report_groups_by_repository(self, sample_organized_issues):
        """Test that report groups issues by repository."""
        generator = MarkdownReportGenerator()
        report = generator.generate_report(sample_organized_issues)

        assert "## owner/repo1" in report
        assert "## owner/repo2" in report
        assert "### #1: Bug in feature A" in report
        assert "### #3: Bug in feature C" in report

    def test_generate_report_includes_issue_details(self, sample_organized_issues):
        """Test that report includes issue details."""
        generator = MarkdownReportGenerator()
        report = generator.generate_report(sample_organized_issues)

        assert "Labels:" in report
        assert "bug" in report
        assert "priority-high" in report
        assert "Assignee:" in report
        assert "user1" in report
        assert "Milestone:" in report
        assert "v1.0" in report
        assert "https://github.com/owner/repo1/issues/1" in report

    def test_generate_report_handles_missing_fields(self):
        """Test that report handles missing optional fields."""
        issues = {
            "owner/repo": [
                {
                    "number": 1,
                    "title": "Test issue",
                    "state": "open",
                    "labels": [],
                    "assignees": [],
                    "milestone": None,
                    "url": "https://github.com/owner/repo/issues/1",
                    "createdAt": "2025-01-01T00:00:00Z",
                }
            ]
        }
        generator = MarkdownReportGenerator()
        report = generator.generate_report(issues)

        assert "**Labels:** None" in report
        assert "**Assignee:** Unassigned" in report
        assert "**Milestone:** None" in report

    def test_generate_report_empty_issues(self):
        """Test generating report with no issues."""
        generator = MarkdownReportGenerator()
        report = generator.generate_report({})

        assert "# GitHub Issues Report" in report
        assert "Total Issues: 0" in report
        assert "No issues found" in report

    def test_generate_report_with_label_grouping(self, sample_organized_issues):
        """Test generating report with label grouping."""
        # Reorganize by labels for this test
        by_labels = {
            "bug": [
                sample_organized_issues["owner/repo1"][0],
                sample_organized_issues["owner/repo2"][0],
            ],
            "enhancement": [sample_organized_issues["owner/repo1"][1]],
        }

        generator = MarkdownReportGenerator()
        report = generator.generate_report(by_labels, group_by="labels")

        assert "## bug" in report
        assert "## enhancement" in report
