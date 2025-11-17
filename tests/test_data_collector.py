"""Tests for data collector."""

import json
from pathlib import Path

import pytest

from github_pm.data_collector import DataCollector


@pytest.fixture
def sample_issues():
    """Sample issues for testing."""
    return [
        {
            "number": 1,
            "title": "Bug fix",
            "state": "OPEN",
            "repository": "owner/repo1",
            "labels": [{"name": "bug"}],
            "assignees": [{"login": "user1"}],
            "milestone": {"title": "v1.0"},
        },
        {
            "number": 2,
            "title": "Feature request",
            "state": "OPEN",
            "repository": "owner/repo2",
            "labels": [{"name": "enhancement"}],
            "assignees": [],
            "milestone": None,
        },
    ]


@pytest.fixture
def sample_organized():
    """Sample organized data for testing."""
    return {
        "by_repository": {"owner/repo1": [], "owner/repo2": []},
        "by_labels": {"bug": [], "enhancement": []},
        "by_milestone": {"v1.0": [], "No Milestone": []},
        "by_assignee": {"user1": [], "Unassigned": []},
    }


@pytest.fixture
def sample_config():
    """Sample config for testing."""
    return {
        "repositories": [
            {"owner": "owner", "name": "repo1"},
            {"owner": "owner", "name": "repo2"},
        ],
        "issue_state": "open",
        "limit": 100,
    }


def test_create_snapshot(tmp_path, sample_issues, sample_organized, sample_config):
    """Test creating a timestamped snapshot."""
    collector = DataCollector(base_data_dir=str(tmp_path))

    snapshot_dir = collector.create_snapshot(
        sample_issues, sample_organized, sample_config
    )

    # Verify directory was created
    assert snapshot_dir.exists()
    assert snapshot_dir.is_dir()

    # Verify raw.json exists and has correct structure
    raw_path = snapshot_dir / "raw.json"
    assert raw_path.exists()

    with open(raw_path) as f:
        data = json.load(f)

    assert "metadata" in data
    assert "issues" in data
    assert "summary" in data
    assert "organized" in data

    assert data["metadata"]["total_issues"] == 2
    assert len(data["issues"]) == 2
    assert data["organized"] == sample_organized

    # Verify metadata.json exists
    metadata_path = snapshot_dir / "metadata.json"
    assert metadata_path.exists()

    # Verify latest symlink was created
    latest_link = tmp_path / "latest"
    assert latest_link.exists()
    assert latest_link.is_symlink()


def test_generate_summary(tmp_path, sample_issues, sample_organized, sample_config):
    """Test summary generation."""
    collector = DataCollector(base_data_dir=str(tmp_path))

    snapshot_dir = collector.create_snapshot(
        sample_issues, sample_organized, sample_config
    )

    with open(snapshot_dir / "raw.json") as f:
        data = json.load(f)

    summary = data["summary"]

    # Verify summary structure
    assert summary["total_issues"] == 2
    assert summary["by_state"] == {"OPEN": 2}
    assert summary["by_repository"] == {"owner/repo1": 1, "owner/repo2": 1}
    assert summary["by_label"] == {"bug": 1, "enhancement": 1}
    assert summary["by_milestone"] == {"v1.0": 1, "No Milestone": 1}
    assert summary["by_assignee"] == {"user1": 1, "Unassigned": 1}


def test_list_snapshots(tmp_path, sample_issues, sample_organized, sample_config):
    """Test listing snapshots."""
    collector = DataCollector(base_data_dir=str(tmp_path))

    # Create multiple snapshots
    snapshot1 = collector.create_snapshot(sample_issues, sample_organized, sample_config)
    snapshot2 = collector.create_snapshot(sample_issues, sample_organized, sample_config)

    snapshots = collector.list_snapshots()

    assert len(snapshots) >= 2
    assert snapshot1 in snapshots
    assert snapshot2 in snapshots


def test_load_snapshot(tmp_path, sample_issues, sample_organized, sample_config):
    """Test loading a snapshot."""
    collector = DataCollector(base_data_dir=str(tmp_path))

    # Create snapshot
    snapshot_dir = collector.create_snapshot(
        sample_issues, sample_organized, sample_config
    )

    # Load by path
    loaded_data = collector.load_snapshot(snapshot_dir)
    assert loaded_data["metadata"]["total_issues"] == 2
    assert len(loaded_data["issues"]) == 2

    # Load by timestamp string
    timestamp = snapshot_dir.name
    loaded_data2 = collector.load_snapshot(timestamp)
    assert loaded_data2 == loaded_data


def test_load_nonexistent_snapshot(tmp_path):
    """Test loading a snapshot that doesn't exist."""
    collector = DataCollector(base_data_dir=str(tmp_path))

    with pytest.raises(FileNotFoundError):
        collector.load_snapshot("nonexistent")
