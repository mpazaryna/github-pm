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
    ) -> Path:
        """
        Create a timestamped snapshot of collected data.

        Args:
            issues: List of all issues
            organized_data: Pre-organized data by different criteria
            config: Configuration used for this collection

        Returns:
            Path to the snapshot directory
        """
        # Create timestamped directory
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        snapshot_dir = self.base_data_dir / timestamp
        snapshot_dir.mkdir(exist_ok=True)

        # Save raw JSON data
        raw_data = {
            "metadata": {
                "collected_at": datetime.now().isoformat(),
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

        raw_path = snapshot_dir / "raw.json"
        raw_path.write_text(json.dumps(raw_data, indent=2))

        # Save metadata separately for quick access
        metadata_path = snapshot_dir / "metadata.json"
        metadata_path.write_text(json.dumps(raw_data["metadata"], indent=2))

        # Update 'latest' symlink
        latest_link = self.base_data_dir / "latest"
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        latest_link.symlink_to(timestamp, target_is_directory=True)

        return snapshot_dir

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

    def list_snapshots(self) -> list[Path]:
        """
        List all available snapshots in chronological order.

        Returns:
            List of snapshot directory paths
        """
        snapshots = [
            d
            for d in self.base_data_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]
        return sorted(snapshots)

    def load_snapshot(self, snapshot_path: Path | str) -> dict[str, Any]:
        """
        Load data from a snapshot.

        Args:
            snapshot_path: Path to snapshot directory or timestamp string

        Returns:
            Dictionary containing the snapshot data

        Raises:
            FileNotFoundError: If snapshot doesn't exist
        """
        if isinstance(snapshot_path, str):
            snapshot_path = self.base_data_dir / snapshot_path

        raw_path = Path(snapshot_path) / "raw.json"
        if not raw_path.exists():
            raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")

        with open(raw_path) as f:
            return json.load(f)
