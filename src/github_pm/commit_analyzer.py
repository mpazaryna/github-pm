"""Commit message analyzer for extracting and parsing git commits."""

import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any


class CommitAnalyzer:
    """Analyzes commit messages from GitHub repositories."""

    # Conventional Commits pattern
    # Format: type(scope): description
    CONVENTIONAL_COMMIT_PATTERN = re.compile(
        r"^(?P<type>feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert)"
        r"(?:\((?P<scope>[^)]+)\))?"
        r"(?P<breaking>!)?"
        r":\s*(?P<description>.+)$",
        re.MULTILINE,
    )

    # Issue reference pattern (e.g., #123, fixes #456, closes #789)
    ISSUE_PATTERN = re.compile(
        r"(?:fixes?|closes?|resolves?|refs?|see)?\s*#(\d+)", re.IGNORECASE
    )

    def fetch_commits(
        self,
        owner: str,
        repo: str,
        since: str | None = None,
        until: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Fetch commits from a GitHub repository using gh CLI.

        Args:
            owner: Repository owner
            repo: Repository name
            since: ISO 8601 date string (e.g., '2025-01-01')
            until: ISO 8601 date string (e.g., '2025-01-31')
            limit: Maximum number of commits to fetch

        Returns:
            List of commit dictionaries

        Raises:
            RuntimeError: If gh CLI command fails
            ValueError: If response is not valid JSON
        """
        # Build gh CLI command
        cmd = [
            "gh",
            "api",
            f"repos/{owner}/{repo}/commits",
            "--paginate",
            "-X",
            "GET",
            "-F",
            f"per_page={min(limit, 100)}",
        ]

        if since:
            cmd.extend(["-F", f"since={since}T00:00:00Z"])
        if until:
            cmd.extend(["-F", f"until={until}T23:59:59Z"])

        # Execute command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        # Check for errors
        if result.returncode != 0:
            raise RuntimeError(
                f"GitHub CLI error: {result.stderr or 'Unknown error'}"
            )

        # Parse JSON response
        try:
            commits = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from gh CLI: {e}") from e

        # Limit results
        return commits[:limit]

    def parse_conventional_commit(self, message: str) -> dict[str, Any] | None:
        """
        Parse a conventional commit message.

        Args:
            message: Commit message (first line)

        Returns:
            Dictionary with parsed components or None if not conventional
        """
        # Get first line of commit message
        first_line = message.split("\n")[0].strip()

        match = self.CONVENTIONAL_COMMIT_PATTERN.match(first_line)
        if match:
            return {
                "type": match.group("type"),
                "scope": match.group("scope"),
                "breaking": match.group("breaking") is not None,
                "description": match.group("description").strip(),
                "raw": first_line,
            }
        return None

    def extract_issue_references(self, message: str) -> list[int]:
        """
        Extract issue numbers referenced in commit message.

        Args:
            message: Full commit message

        Returns:
            List of issue numbers
        """
        matches = self.ISSUE_PATTERN.findall(message)
        return [int(num) for num in matches]

    def analyze_commits(
        self, commits: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Analyze a list of commits and extract insights.

        Args:
            commits: List of commit data from GitHub API

        Returns:
            Dictionary with analysis results
        """
        total_commits = len(commits)
        conventional_commits = 0
        commit_types = Counter()
        commit_scopes = Counter()
        breaking_changes = []
        issue_references = Counter()
        authors = Counter()
        daily_commits = defaultdict(int)

        parsed_commits = []

        for commit in commits:
            commit_data = commit.get("commit", {})
            message = commit_data.get("message", "")
            author = commit_data.get("author", {}).get("name", "Unknown")
            date = commit_data.get("author", {}).get("date", "")
            sha = commit.get("sha", "")

            # Parse conventional commit
            parsed = self.parse_conventional_commit(message)
            if parsed:
                conventional_commits += 1
                commit_types[parsed["type"]] += 1
                if parsed["scope"]:
                    commit_scopes[parsed["scope"]] += 1
                if parsed["breaking"]:
                    breaking_changes.append(
                        {
                            "sha": sha[:7],
                            "message": parsed["raw"],
                            "author": author,
                            "date": date,
                        }
                    )

            # Extract issue references
            issues = self.extract_issue_references(message)
            for issue_num in issues:
                issue_references[issue_num] += 1

            # Count authors
            authors[author] += 1

            # Count by day
            if date:
                day = date[:10]  # YYYY-MM-DD
                daily_commits[day] += 1

            # Store parsed commit
            parsed_commits.append(
                {
                    "sha": sha[:7],
                    "author": author,
                    "date": date,
                    "message": message.split("\n")[0],  # First line
                    "full_message": message,
                    "conventional": parsed,
                    "issues": issues,
                }
            )

        return {
            "total_commits": total_commits,
            "conventional_commits": conventional_commits,
            "conventional_percentage": (
                (conventional_commits / total_commits * 100)
                if total_commits > 0
                else 0
            ),
            "commit_types": dict(commit_types.most_common()),
            "commit_scopes": dict(commit_scopes.most_common(10)),
            "breaking_changes": breaking_changes,
            "issue_references": dict(issue_references.most_common(20)),
            "authors": dict(authors.most_common()),
            "daily_commits": dict(sorted(daily_commits.items())),
            "commits": parsed_commits,
        }

    def generate_summary(self, analysis: dict[str, Any]) -> str:
        """
        Generate a human-readable summary of commit analysis.

        Args:
            analysis: Analysis results from analyze_commits

        Returns:
            Markdown-formatted summary
        """
        lines = []

        lines.append("# Commit Analysis Summary")
        lines.append("")
        lines.append(f"**Total Commits:** {analysis['total_commits']}")
        lines.append(
            f"**Conventional Commits:** {analysis['conventional_commits']} "
            f"({analysis['conventional_percentage']:.1f}%)"
        )
        lines.append("")

        # Commit types
        if analysis["commit_types"]:
            lines.append("## Commit Types")
            lines.append("")
            for commit_type, count in analysis["commit_types"].items():
                lines.append(f"- **{commit_type}**: {count}")
            lines.append("")

        # Scopes
        if analysis["commit_scopes"]:
            lines.append("## Commit Scopes")
            lines.append("")
            for scope, count in analysis["commit_scopes"].items():
                lines.append(f"- **{scope}**: {count}")
            lines.append("")

        # Breaking changes
        if analysis["breaking_changes"]:
            lines.append("## Breaking Changes ⚠️")
            lines.append("")
            for change in analysis["breaking_changes"]:
                lines.append(f"- `{change['sha']}` - {change['message']}")
                lines.append(f"  - Author: {change['author']}")
                lines.append(f"  - Date: {change['date'][:10]}")
            lines.append("")

        # Issue references
        if analysis["issue_references"]:
            lines.append("## Issues Referenced")
            lines.append("")
            for issue, count in list(analysis["issue_references"].items())[:10]:
                lines.append(f"- #{issue}: {count} commit(s)")
            lines.append("")

        # Authors
        if analysis["authors"]:
            lines.append("## Contributors")
            lines.append("")
            for author, count in analysis["authors"].items():
                lines.append(f"- {author}: {count} commit(s)")
            lines.append("")

        # Activity timeline
        if analysis["daily_commits"]:
            lines.append("## Activity Timeline")
            lines.append("")
            for day, count in list(analysis["daily_commits"].items())[:14]:
                bars = "█" * count
                lines.append(f"{day}: {bars} ({count})")
            lines.append("")

        return "\n".join(lines)
