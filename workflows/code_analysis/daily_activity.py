"""Generate multi-repo daily/weekly activity reports."""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from github_pm.commit_analyzer import CommitAnalyzer


class DailyActivityReportGenerator:
    """Generates activity reports across multiple repositories."""

    def __init__(self):
        """Initialize daily activity report generator."""
        self.analyzer = CommitAnalyzer()

    def load_config(self, config_path: str) -> dict[str, Any]:
        """Load repository configuration."""
        with open(config_path) as f:
            return yaml.safe_load(f)

    def generate_report(
        self,
        config_path: str,
        days: int = 1,
        format_type: str = "markdown",
    ) -> dict[str, Any]:
        """
        Generate activity report across all configured repositories.

        Args:
            config_path: Path to collection config YAML
            days: Number of days to look back (default: 1 for today)
            format_type: Output format (markdown or json)

        Returns:
            Dict with markdown report and analysis data
        """
        # Load configuration
        config = self.load_config(config_path)
        repos = config.get("repositories", [])

        # Calculate date range
        since_date = datetime.now() - timedelta(days=days)
        since = since_date.strftime("%Y-%m-%d")
        until = datetime.now().strftime("%Y-%m-%d")

        # Collect data from all repos
        all_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "period": {"days": days, "since": since, "until": until},
                "repositories": len(repos),
            },
            "repositories": {},
            "totals": {
                "commits": 0,
                "conventional_commits": 0,
                "contributors": set(),
                "issues_referenced": set(),
                "breaking_changes": 0,
                "commit_types": {},
                "commit_scopes": {},
            },
        }

        print(f"\nFetching commits from {len(repos)} repositories...")
        print(f"Period: Last {days} day(s) ({since} to {until})\n")

        for repo_config in repos:
            owner = repo_config["owner"]
            name = repo_config["name"]
            repo_key = f"{owner}/{name}"

            try:
                print(f"  Analyzing {repo_key}...")
                commits = self.analyzer.fetch_commits(
                    owner, name, since, until, limit=100
                )

                if not commits:
                    print(f"    No commits found")
                    continue

                analysis = self.analyzer.analyze_commits(commits)
                print(f"    Found {len(commits)} commits")

                # Store repo-specific data
                all_data["repositories"][repo_key] = analysis

                # Aggregate totals
                all_data["totals"]["commits"] += analysis["total_commits"]
                all_data["totals"]["conventional_commits"] += analysis[
                    "conventional_commits"
                ]
                all_data["totals"]["contributors"].update(analysis["authors"].keys())
                all_data["totals"]["issues_referenced"].update(
                    analysis["issue_references"].keys()
                )
                all_data["totals"]["breaking_changes"] += len(
                    analysis["breaking_changes"]
                )

                # Aggregate commit types
                for commit_type, count in analysis["commit_types"].items():
                    all_data["totals"]["commit_types"][commit_type] = (
                        all_data["totals"]["commit_types"].get(commit_type, 0) + count
                    )

                # Aggregate scopes
                for scope, count in analysis["commit_scopes"].items():
                    all_data["totals"]["commit_scopes"][scope] = (
                        all_data["totals"]["commit_scopes"].get(scope, 0) + count
                    )

            except Exception as e:
                print(f"    Error: {e}")
                continue

        # Convert sets to lists for JSON serialization
        all_data["totals"]["contributors"] = list(all_data["totals"]["contributors"])
        all_data["totals"]["issues_referenced"] = list(
            all_data["totals"]["issues_referenced"]
        )

        # Generate markdown report
        if format_type in ["markdown", "both"]:
            markdown = self._generate_markdown(all_data, days)
            all_data["markdown"] = markdown

        return all_data

    def _generate_markdown(self, data: dict[str, Any], days: int) -> str:
        """Generate markdown report from analysis data."""
        lines = []
        totals = data["totals"]
        metadata = data["metadata"]

        # Header
        period_str = "Today" if days == 1 else f"Last {days} Days"
        lines.append(f"# Activity Report: {period_str}")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(
            f"**Period:** {metadata['period']['since']} to {metadata['period']['until']}"
        )
        lines.append("")

        # Overall summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total Commits:** {totals['commits']}")
        conv_pct = (
            (totals["conventional_commits"] / totals["commits"] * 100)
            if totals["commits"] > 0
            else 0
        )
        lines.append(
            f"- **Conventional Commits:** {totals['conventional_commits']} ({conv_pct:.1f}%)"
        )
        lines.append(f"- **Contributors:** {len(totals['contributors'])}")
        lines.append(f"- **Issues Referenced:** {len(totals['issues_referenced'])}")
        lines.append(f"- **Repositories Active:** {len(data['repositories'])}")
        if totals["breaking_changes"] > 0:
            lines.append(f"- **Breaking Changes:** {totals['breaking_changes']} ⚠️")
        lines.append("")

        # Work distribution by type
        if totals["commit_types"]:
            lines.append("## Work Distribution")
            lines.append("")
            lines.append("| Type | Count | Percentage |")
            lines.append("|------|-------|------------|")
            total_commits = totals["commits"]
            for commit_type, count in sorted(
                totals["commit_types"].items(), key=lambda x: x[1], reverse=True
            ):
                pct = (count / total_commits * 100) if total_commits > 0 else 0
                lines.append(f"| {commit_type} | {count} | {pct:.1f}% |")
            lines.append("")

        # Repository breakdown
        if data["repositories"]:
            lines.append("## Repository Breakdown")
            lines.append("")
            lines.append("| Repository | Commits | Types | Issues |")
            lines.append("|------------|---------|-------|--------|")

            for repo_name, repo_data in sorted(
                data["repositories"].items(),
                key=lambda x: x[1]["total_commits"],
                reverse=True,
            ):
                commits = repo_data["total_commits"]
                types = ", ".join(list(repo_data["commit_types"].keys())[:3])
                issues = len(repo_data["issue_references"])
                lines.append(f"| {repo_name} | {commits} | {types} | {issues} |")
            lines.append("")

        # Top areas of focus (scopes)
        if totals["commit_scopes"]:
            lines.append("## Top Areas of Focus")
            lines.append("")
            top_scopes = sorted(
                totals["commit_scopes"].items(), key=lambda x: x[1], reverse=True
            )[:10]
            for scope, count in top_scopes:
                lines.append(f"- **{scope}**: {count} commit(s)")
            lines.append("")

        # Issues worked on
        if totals["issues_referenced"]:
            lines.append("## Issues Worked On")
            lines.append("")
            for issue in sorted(totals["issues_referenced"]):
                lines.append(f"- #{issue}")
            lines.append("")

        # Detailed repository activity
        lines.append("## Detailed Activity by Repository")
        lines.append("")

        for repo_name, repo_data in sorted(
            data["repositories"].items(),
            key=lambda x: x[1]["total_commits"],
            reverse=True,
        ):
            lines.append(f"### {repo_name}")
            lines.append("")
            lines.append(f"**{repo_data['total_commits']} commit(s)**")
            lines.append("")

            # Types
            if repo_data["commit_types"]:
                type_str = ", ".join(
                    [f"`{t}` ({c})" for t, c in repo_data["commit_types"].items()]
                )
                lines.append(f"Types: {type_str}")
                lines.append("")

            # Recent commits (last 5)
            if repo_data["commits"]:
                lines.append("Recent commits:")
                for commit in repo_data["commits"][:5]:
                    msg = commit["message"].split("\n")[0][:80]
                    lines.append(f"- `{commit['sha'][:7]}` {msg}")
                lines.append("")

        return "\n".join(lines)


def main():
    """Main entry point for daily activity report generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate multi-repo activity report"
    )
    parser.add_argument(
        "--config",
        default="config/collection/production.yaml",
        help="Path to collection config (default: production.yaml)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Number of days to look back (default: 1 for today)",
    )
    parser.add_argument(
        "--output",
        help="Output file path (defaults to reports/daily/activity_TIMESTAMP.md)",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "both"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    args = parser.parse_args()

    # Generate report
    generator = DailyActivityReportGenerator()
    try:
        data = generator.generate_report(
            args.config,
            args.days,
            args.format,
        )

        # Determine output path
        if args.output:
            output_path = Path(args.output)
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            period_str = f"{args.days}day" if args.days == 1 else f"{args.days}days"
            output_path = Path("reports/daily") / f"activity_{period_str}_{timestamp}.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save markdown report
        if args.format in ["markdown", "both"]:
            md_path = (
                output_path
                if args.format == "markdown"
                else output_path.with_suffix(".md")
            )
            md_path.write_text(data["markdown"])
            print(f"\nMarkdown report saved: {md_path}")

        # Save JSON data
        if args.format in ["json", "both"]:
            json_path = (
                output_path if args.format == "json" else output_path.with_suffix(".json")
            )
            # Remove markdown from JSON output
            json_data = {k: v for k, v in data.items() if k != "markdown"}
            json_path.write_text(json.dumps(json_data, indent=2))
            print(f"JSON report saved: {json_path}")

        # Print summary
        print("\n" + "=" * 60)
        print(f"Activity Summary - Last {args.days} Day(s)")
        print("=" * 60)
        print(f"Total Commits: {data['totals']['commits']}")
        print(f"Active Repositories: {len(data['repositories'])}")
        print(f"Contributors: {len(data['totals']['contributors'])}")
        print(f"Issues Referenced: {len(data['totals']['issues_referenced'])}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
