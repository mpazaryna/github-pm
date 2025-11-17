"""JSON data exporter for GitHub issues."""

from collections import defaultdict
from datetime import datetime
from typing import Any


class JSONExporter:
    """Exports GitHub issues data to structured JSON format."""

    def export(
        self,
        issues: list[dict[str, Any]],
        organized: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Export issues to structured JSON format.

        Args:
            issues: List of issue dictionaries
            organized: Optional pre-organized data by different criteria

        Returns:
            Dictionary containing metadata, issues, summary, and organized data
        """
        timestamp = datetime.now().isoformat()

        # Build the export structure
        export_data = {
            "metadata": {
                "generated_at": timestamp,
                "version": "0.1.0",
                "total_issues": len(issues),
            },
            "issues": issues,
            "summary": self._generate_summary(issues),
        }

        # Add organized data if provided
        if organized:
            export_data["organized"] = organized

        return export_data

    def _generate_summary(self, issues: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Generate summary statistics from issues.

        Args:
            issues: List of issue dictionaries

        Returns:
            Dictionary with summary statistics
        """
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
