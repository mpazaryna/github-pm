"""Generate commit analysis reports for repositories."""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from github_pm.commit_analyzer import CommitAnalyzer


class CommitReportGenerator:
    """Generates detailed commit analysis reports."""

    def __init__(self):
        """Initialize commit report generator."""
        self.analyzer = CommitAnalyzer()

    def generate_report(
        self,
        owner: str,
        repo: str,
        since: str | None = None,
        until: str | None = None,
        limit: int = 100,
        snapshot_data: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate a comprehensive commit report.

        Args:
            owner: Repository owner
            repo: Repository name
            since: Start date (YYYY-MM-DD)
            until: End date (YYYY-MM-DD)
            limit: Maximum commits to analyze
            snapshot_data: Optional issue snapshot data for correlation

        Returns:
            Markdown-formatted report
        """
        # Fetch commits
        print(f"Fetching commits from {owner}/{repo}...")
        commits = self.analyzer.fetch_commits(owner, repo, since, until, limit)
        print(f"  Found {len(commits)} commits")

        # Analyze commits
        print("Analyzing commit messages...")
        analysis = self.analyzer.analyze_commits(commits)

        # Generate report
        lines = []
        lines.append(f"# Commit Analysis: {owner}/{repo}")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if since:
            lines.append(f"**Period:** {since} to {until or 'now'}")
        lines.append("")

        # Summary statistics
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total Commits:** {analysis['total_commits']}")
        lines.append(
            f"- **Conventional Commits:** {analysis['conventional_commits']} "
            f"({analysis['conventional_percentage']:.1f}%)"
        )
        lines.append(f"- **Contributors:** {len(analysis['authors'])}")
        lines.append(
            f"- **Issues Referenced:** {len(analysis['issue_references'])}"
        )
        if analysis["breaking_changes"]:
            lines.append(
                f"- **Breaking Changes:** {len(analysis['breaking_changes'])} ⚠️"
            )
        lines.append("")

        # Work breakdown by type
        if analysis["commit_types"]:
            lines.append("## Work Breakdown")
            lines.append("")
            lines.append("| Type | Count | Percentage |")
            lines.append("|------|-------|------------|")
            total = analysis["total_commits"]
            for commit_type, count in analysis["commit_types"].items():
                pct = (count / total * 100) if total > 0 else 0
                lines.append(f"| {commit_type} | {count} | {pct:.1f}% |")
            lines.append("")

            # Add type descriptions
            lines.append("**Commit Types:**")
            type_descriptions = {
                "feat": "New features",
                "fix": "Bug fixes",
                "docs": "Documentation changes",
                "style": "Code style changes (formatting, etc.)",
                "refactor": "Code refactoring",
                "perf": "Performance improvements",
                "test": "Test additions or changes",
                "chore": "Build process or auxiliary tool changes",
                "ci": "CI/CD changes",
                "build": "Build system changes",
                "revert": "Reverts previous commits",
            }
            for commit_type in analysis["commit_types"].keys():
                desc = type_descriptions.get(commit_type, "Other changes")
                lines.append(f"- `{commit_type}:` - {desc}")
            lines.append("")

        # Scopes (areas of codebase)
        if analysis["commit_scopes"]:
            lines.append("## Areas of Focus")
            lines.append("")
            lines.append("Top scopes worked on:")
            lines.append("")
            for scope, count in list(analysis["commit_scopes"].items())[:10]:
                lines.append(f"- **{scope}**: {count} commit(s)")
            lines.append("")

        # Breaking changes
        if analysis["breaking_changes"]:
            lines.append("## Breaking Changes ⚠️")
            lines.append("")
            for change in analysis["breaking_changes"]:
                lines.append(f"### `{change['sha']}`")
                lines.append(f"**{change['message']}**")
                lines.append("")
                lines.append(f"- Author: {change['author']}")
                lines.append(f"- Date: {change['date'][:10]}")
                lines.append("")

        # Issue correlation
        if analysis["issue_references"] and snapshot_data:
            lines.append("## Issue Correlation")
            lines.append("")
            lines.append("Commits referencing issues:")
            lines.append("")

            # Get issues from snapshot
            issues_by_number = {}
            for issue in snapshot_data.get("issues", []):
                issues_by_number[issue.get("number")] = issue

            for issue_num, commit_count in list(
                analysis["issue_references"].items()
            )[:15]:
                issue = issues_by_number.get(issue_num)
                if issue:
                    title = issue.get("title", "Unknown")
                    state = issue.get("state", "UNKNOWN")
                    lines.append(
                        f"- #{issue_num}: {title} ({state}) - {commit_count} commit(s)"
                    )
                else:
                    lines.append(f"- #{issue_num} - {commit_count} commit(s)")
            lines.append("")

        elif analysis["issue_references"]:
            lines.append("## Issues Referenced")
            lines.append("")
            for issue, count in list(analysis["issue_references"].items())[:15]:
                lines.append(f"- #{issue}: {count} commit(s)")
            lines.append("")

        # Contributors
        if analysis["authors"]:
            lines.append("## Contributors")
            lines.append("")
            for author, count in analysis["authors"].items():
                pct = (
                    (count / analysis["total_commits"] * 100)
                    if analysis["total_commits"] > 0
                    else 0
                )
                lines.append(f"- **{author}**: {count} commit(s) ({pct:.1f}%)")
            lines.append("")

        # Activity timeline
        if analysis["daily_commits"]:
            lines.append("## Activity Timeline")
            lines.append("")
            max_commits = max(analysis["daily_commits"].values())
            for day, count in analysis["daily_commits"].items():
                # Simple bar chart
                bar_length = int((count / max_commits) * 40) if max_commits > 0 else 0
                bars = "█" * bar_length
                lines.append(f"{day}: {bars} ({count})")
            lines.append("")

        # Recent commits sample
        lines.append("## Recent Commits (Sample)")
        lines.append("")
        for commit in analysis["commits"][:20]:
            lines.append(f"### `{commit['sha']}` - {commit['author']}")
            lines.append(f"**{commit['message']}**")
            if commit["conventional"]:
                conv = commit["conventional"]
                scope_str = f"({conv['scope']})" if conv["scope"] else ""
                lines.append(
                    f"- Type: `{conv['type']}{scope_str}`"
                )
            if commit["issues"]:
                issues_str = ", ".join([f"#{num}" for num in commit["issues"]])
                lines.append(f"- References: {issues_str}")
            lines.append(f"- Date: {commit['date'][:10]}")
            lines.append("")

        return "\n".join(lines)


def main():
    """Main entry point for commit report generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate commit analysis report for a repository"
    )
    parser.add_argument("--owner", required=True, help="Repository owner")
    parser.add_argument("--repo", required=True, help="Repository name")
    parser.add_argument(
        "--since",
        help="Start date (YYYY-MM-DD), defaults to 7 days ago",
    )
    parser.add_argument(
        "--until",
        help="End date (YYYY-MM-DD), defaults to today",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum commits to analyze (default: 100)",
    )
    parser.add_argument(
        "--correlate-issues",
        action="store_true",
        help="Correlate with issues from latest snapshot",
    )
    parser.add_argument(
        "--output",
        help="Output file path (defaults to reports/adhoc/commit_report_REPO_TIMESTAMP.md)",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "both"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    args = parser.parse_args()

    # Set default dates
    if not args.since:
        since_date = datetime.now() - timedelta(days=7)
        args.since = since_date.strftime("%Y-%m-%d")
    if not args.until:
        args.until = datetime.now().strftime("%Y-%m-%d")

    # Load snapshot data if correlating with issues
    snapshot_data = None
    if args.correlate_issues:
        latest_snapshot = Path("data/latest")
        if latest_snapshot.exists():
            raw_path = latest_snapshot / "raw.json"
            if raw_path.exists():
                with open(raw_path) as f:
                    snapshot_data = json.load(f)
                print(f"Loaded issue snapshot for correlation")

    # Generate report
    generator = CommitReportGenerator()
    try:
        report = generator.generate_report(
            args.owner,
            args.repo,
            args.since,
            args.until,
            args.limit,
            snapshot_data,
        )

        # Determine output path
        if args.output:
            output_path = Path(args.output)
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_path = (
                Path("reports/adhoc")
                / f"commit_report_{args.repo}_{timestamp}.md"
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save report based on format
        if args.format in ["markdown", "both"]:
            md_path = output_path if args.format == "markdown" else output_path.with_suffix(".md")
            md_path.write_text(report)
            print(f"\nMarkdown report saved: {md_path}")

        if args.format in ["json", "both"]:
            # Generate JSON output
            json_output = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "repository": f"{args.owner}/{args.repo}",
                    "period": {
                        "since": args.since,
                        "until": args.until,
                    },
                },
                "analysis": generator.analyzer.analyze_commits(
                    generator.analyzer.fetch_commits(
                        args.owner, args.repo, args.since, args.until, args.limit
                    )
                ),
            }

            json_path = output_path if args.format == "json" else output_path.with_suffix(".json")
            json_path.write_text(json.dumps(json_output, indent=2))
            print(f"JSON report saved: {json_path}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
