"""Markdown report generator for GitHub issues."""

from datetime import datetime
from typing import Any


class MarkdownReportGenerator:
    """Generates markdown reports from organized GitHub issues."""

    def generate_report(
        self,
        organized_issues: dict[str, list[dict[str, Any]]],
        group_by: str = "repository",
    ) -> str:
        """
        Generate a markdown report from organized issues.

        Args:
            organized_issues: Dictionary of grouped issues
            group_by: How issues are grouped (repository, labels, milestone, assignee)

        Returns:
            Markdown-formatted report string
        """
        lines = []

        # Header
        lines.append("# GitHub Issues Report")
        lines.append("")
        lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Summary
        total_issues = sum(len(issues) for issues in organized_issues.values())
        lines.append("## Summary")
        lines.append("")
        lines.append(f"Total Issues: {total_issues}")
        # Pluralize the group name
        group_name = group_by.title()
        if group_name.endswith("y"):
            group_name = group_name[:-1] + "ies"
        else:
            group_name = group_name + "s"
        lines.append(f"Total {group_name}: {len(organized_issues)}")
        lines.append("")

        # Check if no issues
        if total_issues == 0:
            lines.append("No issues found.")
            return "\n".join(lines)

        # Group sections
        for group_name, issues in organized_issues.items():
            lines.append(f"## {group_name}")
            lines.append("")

            for issue in issues:
                self._add_issue_to_report(lines, issue)

        return "\n".join(lines)

    def _add_issue_to_report(
        self, lines: list[str], issue: dict[str, Any]
    ) -> None:
        """
        Add a single issue to the report.

        Args:
            lines: List of report lines to append to
            issue: Issue dictionary
        """
        number = issue.get("number", "?")
        title = issue.get("title", "No title")
        state = issue.get("state", "unknown")

        # Issue header
        lines.append(f"### #{number}: {title}")
        lines.append("")

        # State
        lines.append(f"**State:** {state}")
        lines.append("")

        # Labels
        labels = issue.get("labels", [])
        if labels:
            label_names = [label.get("name", "?") for label in labels]
            lines.append(f"**Labels:** {', '.join(label_names)}")
        else:
            lines.append("**Labels:** None")
        lines.append("")

        # Assignees
        assignees = issue.get("assignees", [])
        if assignees:
            assignee_logins = [assignee.get("login", "?") for assignee in assignees]
            lines.append(f"**Assignee:** {', '.join(assignee_logins)}")
        else:
            lines.append("**Assignee:** Unassigned")
        lines.append("")

        # Milestone
        milestone = issue.get("milestone")
        if milestone:
            milestone_title = milestone.get("title", "?")
            lines.append(f"**Milestone:** {milestone_title}")
        else:
            lines.append("**Milestone:** None")
        lines.append("")

        # Created date
        created_at = issue.get("createdAt", "")
        if created_at:
            lines.append(f"**Created:** {created_at}")
            lines.append("")

        # URL
        url = issue.get("url", "")
        if url:
            lines.append(f"**Link:** {url}")
            lines.append("")

        lines.append("---")
        lines.append("")
