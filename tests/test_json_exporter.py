"""Tests for JSON data exporter."""

import json
import pytest
from datetime import datetime
from github_pm.json_exporter import JSONExporter


class TestJSONExporter:
    """Test suite for JSONExporter."""

    @pytest.fixture
    def sample_issues(self):
        """Sample issues for testing."""
        return [
            {
                "number": 1,
                "title": "Bug in feature A",
                "state": "OPEN",
                "labels": [{"name": "bug"}],
                "assignees": [{"login": "user1"}],
                "milestone": {"title": "v1.0"},
                "url": "https://github.com/owner/repo1/issues/1",
                "createdAt": "2025-01-01T00:00:00Z",
                "updatedAt": "2025-01-02T00:00:00Z",
                "repository": "owner/repo1",
            },
            {
                "number": 2,
                "title": "Feature request B",
                "state": "OPEN",
                "labels": [{"name": "enhancement"}],
                "assignees": [],
                "milestone": None,
                "url": "https://github.com/owner/repo1/issues/2",
                "createdAt": "2025-01-03T00:00:00Z",
                "updatedAt": "2025-01-04T00:00:00Z",
                "repository": "owner/repo1",
            },
        ]

    @pytest.fixture
    def sample_organized_data(self):
        """Sample organized data for testing."""
        return {
            "by_repository": {
                "owner/repo1": [
                    {"number": 1, "title": "Bug in feature A"},
                    {"number": 2, "title": "Feature request B"},
                ]
            },
            "by_labels": {
                "bug": [{"number": 1, "title": "Bug in feature A"}],
                "enhancement": [{"number": 2, "title": "Feature request B"}],
            },
            "by_milestone": {
                "v1.0": [{"number": 1, "title": "Bug in feature A"}],
                "No Milestone": [{"number": 2, "title": "Feature request B"}],
            },
        }

    def test_export_creates_valid_json_structure(self, sample_issues):
        """Test that export creates a valid JSON structure."""
        exporter = JSONExporter()
        result = exporter.export(sample_issues)

        assert "metadata" in result
        assert "issues" in result
        assert "summary" in result
        assert len(result["issues"]) == 2

    def test_export_includes_metadata(self, sample_issues):
        """Test that export includes metadata."""
        exporter = JSONExporter()
        result = exporter.export(sample_issues)

        metadata = result["metadata"]
        assert "generated_at" in metadata
        assert "total_issues" in metadata
        assert metadata["total_issues"] == 2
        assert "version" in metadata

    def test_export_includes_summary_statistics(self, sample_issues):
        """Test that export includes summary statistics."""
        exporter = JSONExporter()
        result = exporter.export(sample_issues)

        summary = result["summary"]
        assert "total_issues" in summary
        assert "by_state" in summary
        assert "by_repository" in summary
        assert "by_label" in summary
        assert summary["total_issues"] == 2
        assert summary["by_state"]["OPEN"] == 2

    def test_export_preserves_all_issue_fields(self, sample_issues):
        """Test that export preserves all issue fields."""
        exporter = JSONExporter()
        result = exporter.export(sample_issues)

        issue = result["issues"][0]
        assert issue["number"] == 1
        assert issue["title"] == "Bug in feature A"
        assert issue["state"] == "OPEN"
        assert issue["url"] == "https://github.com/owner/repo1/issues/1"
        assert issue["repository"] == "owner/repo1"

    def test_export_with_organized_data(self, sample_issues, sample_organized_data):
        """Test export with pre-organized data."""
        exporter = JSONExporter()
        result = exporter.export(sample_issues, organized=sample_organized_data)

        assert "organized" in result
        assert "by_repository" in result["organized"]
        assert "by_labels" in result["organized"]
        assert "by_milestone" in result["organized"]

    def test_export_handles_empty_issues(self):
        """Test export with empty issues list."""
        exporter = JSONExporter()
        result = exporter.export([])

        assert result["metadata"]["total_issues"] == 0
        assert result["issues"] == []
        assert result["summary"]["total_issues"] == 0

    def test_export_calculates_label_counts(self, sample_issues):
        """Test that export calculates label counts."""
        exporter = JSONExporter()
        result = exporter.export(sample_issues)

        label_counts = result["summary"]["by_label"]
        assert "bug" in label_counts
        assert "enhancement" in label_counts
        assert label_counts["bug"] == 1
        assert label_counts["enhancement"] == 1

    def test_export_calculates_repository_counts(self, sample_issues):
        """Test that export calculates repository counts."""
        exporter = JSONExporter()
        result = exporter.export(sample_issues)

        repo_counts = result["summary"]["by_repository"]
        assert "owner/repo1" in repo_counts
        assert repo_counts["owner/repo1"] == 2
