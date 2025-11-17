"""Issue organizer for grouping issues by different criteria."""

from collections import defaultdict
from typing import Any


class IssueOrganizer:
    """Organizes GitHub issues by various criteria."""

    def organize_by_repository(
        self, issues: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Organize issues by repository.

        Args:
            issues: List of issue dictionaries

        Returns:
            Dictionary mapping repository names to lists of issues
        """
        organized = defaultdict(list)
        for issue in issues:
            repo = issue.get("repository", "unknown")
            organized[repo].append(issue)
        return dict(organized)

    def organize_by_labels(
        self, issues: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Organize issues by labels.

        Args:
            issues: List of issue dictionaries

        Returns:
            Dictionary mapping label names to lists of issues
        """
        organized = defaultdict(list)
        for issue in issues:
            labels = issue.get("labels", [])
            if not labels:
                continue
            for label in labels:
                label_name = label.get("name", "unknown")
                organized[label_name].append(issue)
        return dict(organized)

    def organize_by_milestone(
        self, issues: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Organize issues by milestone.

        Args:
            issues: List of issue dictionaries

        Returns:
            Dictionary mapping milestone titles to lists of issues
        """
        organized = defaultdict(list)
        for issue in issues:
            milestone = issue.get("milestone")
            if milestone:
                milestone_title = milestone.get("title", "unknown")
            else:
                milestone_title = "No Milestone"
            organized[milestone_title].append(issue)
        return dict(organized)

    def organize_by_assignee(
        self, issues: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Organize issues by assignee.

        Args:
            issues: List of issue dictionaries

        Returns:
            Dictionary mapping assignee logins to lists of issues
        """
        organized = defaultdict(list)
        for issue in issues:
            assignees = issue.get("assignees", [])
            if not assignees:
                organized["Unassigned"].append(issue)
            else:
                for assignee in assignees:
                    login = assignee.get("login", "unknown")
                    organized[login].append(issue)
        return dict(organized)
