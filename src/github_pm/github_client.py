"""GitHub CLI wrapper for fetching issues."""

import json
import subprocess
from typing import Any


class GitHubClient:
    """Client for interacting with GitHub via the gh CLI."""

    def fetch_issues(
        self,
        owner: str,
        repo: str,
        state: str = "open",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Fetch issues from a GitHub repository using gh CLI.

        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state filter (open, closed, all)
            limit: Maximum number of issues to fetch

        Returns:
            List of issue dictionaries

        Raises:
            RuntimeError: If gh CLI command fails
            ValueError: If response is not valid JSON
        """
        # Build gh CLI command
        cmd = [
            "gh",
            "issue",
            "list",
            "--repo",
            f"{owner}/{repo}",
            "--state",
            state,
            "--limit",
            str(limit),
            "--json",
            "number,title,state,labels,assignees,milestone,url,createdAt,updatedAt",
        ]

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
            issues = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from gh CLI: {e}") from e

        return issues
