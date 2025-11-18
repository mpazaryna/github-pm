"""Data collector for timestamped GitHub issue snapshots."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class DataCollector:
    """Manages timestamped data collection and storage."""

    def __init__(self, base_data_dir: str = "data"):
        """
        Initialize data collector.

        Args:
            base_data_dir: Base directory for storing collected data
        """
        self.base_data_dir = Path(base_data_dir)
        self.base_data_dir.mkdir(exist_ok=True)

    def create_snapshot(
        self,
        issues: list[dict[str, Any]],
        organized_data: dict[str, Any],
        config: dict[str, Any],
        label: str = "snapshot",
        date: str | None = None,
    ) -> Path:
        """
        Create a timestamped snapshot of collected data.

        Args:
            issues: List of all issues
            organized_data: Pre-organized data by different criteria
            config: Configuration used for this collection
            label: Snapshot label (e.g., "sod", "eod", "snapshot")
            date: Date string (YYYY-MM-DD). If None, uses today's date.

        Returns:
            Path to the snapshot file
        """
        # Use provided date or today's date
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        # Create filename: YYYY-MM-DD-label.json
        filename = f"{date}-{label.lower()}.json"
        snapshot_path = self.base_data_dir / filename

        # Save snapshot data
        snapshot_data = {
            "metadata": {
                "snapshot_date": date,
                "snapshot_type": label.upper(),
                "timestamp": datetime.now().isoformat(),
                "generated_by": "github-pm",
                "version": "0.1.0",
                "total_issues": len(issues),
                "repositories": [
                    f"{repo['owner']}/{repo['name']}"
                    for repo in config.get("repositories", [])
                ],
                "config": config,
            },
            "issues": issues,
            "summary": self._generate_summary(issues),
            "organized": organized_data,
        }

        snapshot_path.write_text(json.dumps(snapshot_data, indent=2))

        # Update latest symlink for this label type
        latest_link = self.base_data_dir / f"latest-{label.lower()}.json"
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        latest_link.symlink_to(filename, target_is_directory=False)

        return snapshot_path

    def _generate_summary(self, issues: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Generate summary statistics from issues.

        Args:
            issues: List of issue dictionaries

        Returns:
            Dictionary with summary statistics
        """
        from collections import defaultdict

        # Count by state
        state_counts = defaultdict(int)
        for issue in issues:
            state = issue.get("state", "UNKNOWN")
            state_counts[state] += 1

        # Count by repository
        repo_counts = defaultdict(int)
        for issue in issues:
            repo = issue.get("repository", "unknown")
            repo_counts[repo] += 1

        # Count by label
        label_counts = defaultdict(int)
        for issue in issues:
            labels = issue.get("labels", [])
            for label in labels:
                label_name = label.get("name", "unknown")
                label_counts[label_name] += 1

        # Count by milestone
        milestone_counts = defaultdict(int)
        for issue in issues:
            milestone = issue.get("milestone")
            if milestone:
                milestone_title = milestone.get("title", "unknown")
                milestone_counts[milestone_title] += 1
            else:
                milestone_counts["No Milestone"] += 1

        # Count by assignee
        assignee_counts = defaultdict(int)
        for issue in issues:
            assignees = issue.get("assignees", [])
            if not assignees:
                assignee_counts["Unassigned"] += 1
            else:
                for assignee in assignees:
                    login = assignee.get("login", "unknown")
                    assignee_counts[login] += 1

        return {
            "total_issues": len(issues),
            "by_state": dict(state_counts),
            "by_repository": dict(repo_counts),
            "by_label": dict(label_counts),
            "by_milestone": dict(milestone_counts),
            "by_assignee": dict(assignee_counts),
        }

    def list_snapshots(self, label: str | None = None) -> list[Path]:
        """
        List all available snapshots in chronological order.

        Args:
            label: Optional label filter (e.g., "sod", "eod")

        Returns:
            List of snapshot file paths
        """
        if label:
            # Filter by label
            pattern = f"*-{label.lower()}.json"
        else:
            # All snapshots (exclude latest-* symlinks)
            pattern = "*.json"

        snapshots = [
            f
            for f in self.base_data_dir.glob(pattern)
            if f.is_file() and not f.name.startswith("latest-")
        ]
        return sorted(snapshots)

    def load_snapshot(self, snapshot_identifier: Path | str) -> dict[str, Any]:
        """
        Load data from a snapshot.

        Args:
            snapshot_identifier: Can be:
                - Full filename: "2025-01-18-sod.json"
                - Date and label: "2025-01-18-sod"
                - Label only: "latest-sod" or "sod" (loads latest)
                - Path object

        Returns:
            Dictionary containing the snapshot data

        Raises:
            FileNotFoundError: If snapshot doesn't exist
        """
        if isinstance(snapshot_identifier, Path):
            snapshot_path = snapshot_identifier
        else:
            # Handle different identifier formats
            if snapshot_identifier in ["latest-sod", "latest-eod", "latest-snapshot"]:
                # Load from symlink
                snapshot_path = self.base_data_dir / f"{snapshot_identifier}.json"
            elif snapshot_identifier in ["sod", "eod", "snapshot"]:
                # Load latest of this type
                snapshot_path = self.base_data_dir / f"latest-{snapshot_identifier}.json"
            elif not snapshot_identifier.endswith(".json"):
                # Add .json extension if missing
                snapshot_path = self.base_data_dir / f"{snapshot_identifier}.json"
            else:
                # Full filename provided
                snapshot_path = self.base_data_dir / snapshot_identifier

        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")

        with open(snapshot_path) as f:
            return json.load(f)
