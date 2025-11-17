"""Compare commit activity between two time periods."""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from github_pm.commit_analyzer import CommitAnalyzer


class PeriodComparisonGenerator:
    """Compares commit activity between two time periods."""

    def __init__(self):
        """Initialize period comparison generator."""
        self.analyzer = CommitAnalyzer()

    def load_config(self, config_path: str) -> dict[str, Any]:
        """Load repository configuration."""
        with open(config_path) as f:
            return yaml.safe_load(f)

    def analyze_period(
        self, repos: list[dict], since: str, until: str
    ) -> dict[str, Any]:
        """Analyze commits for a specific time period across all repos."""
        period_data = {
            "commits": 0,
            "conventional_commits": 0,
            "contributors": set(),
            "issues_referenced": set(),
            "breaking_changes": 0,
            "commit_types": {},
            "commit_scopes": {},
            "repositories": {},
        }

        for repo_config in repos:
            owner = repo_config["owner"]
            name = repo_config["name"]
            repo_key = f"{owner}/{name}"

            try:
                commits = self.analyzer.fetch_commits(
                    owner, name, since, until, limit=200
                )

                if not commits:
                    continue

                analysis = self.analyzer.analyze_commits(commits)
                period_data["repositories"][repo_key] = analysis

                # Aggregate
                period_data["commits"] += analysis["total_commits"]
                period_data["conventional_commits"] += analysis["conventional_commits"]
                period_data["contributors"].update(analysis["authors"].keys())
                period_data["issues_referenced"].update(
                    analysis["issue_references"].keys()
                )
                period_data["breaking_changes"] += len(analysis["breaking_changes"])

                for commit_type, count in analysis["commit_types"].items():
                    period_data["commit_types"][commit_type] = (
                        period_data["commit_types"].get(commit_type, 0) + count
                    )

                for scope, count in analysis["commit_scopes"].items():
                    period_data["commit_scopes"][scope] = (
                        period_data["commit_scopes"].get(scope, 0) + count
                    )

            except Exception as e:
                print(f"    Error analyzing {repo_key}: {e}")
                continue

        # Convert sets to lists
        period_data["contributors"] = list(period_data["contributors"])
        period_data["issues_referenced"] = list(period_data["issues_referenced"])

        return period_data

    def compare_periods(
        self,
        config_path: str,
        days: int = 7,
    ) -> dict[str, Any]:
        """
        Compare current period vs previous period.

        Args:
            config_path: Path to collection config YAML
            days: Number of days per period (default: 7)

        Returns:
            Comparison data and markdown report
        """
        config = self.load_config(config_path)
        repos = config.get("repositories", [])

        # Calculate date ranges
        now = datetime.now()
        current_until = now.strftime("%Y-%m-%d")
        current_since = (now - timedelta(days=days)).strftime("%Y-%m-%d")

        previous_until = (now - timedelta(days=days)).strftime("%Y-%m-%d")
        previous_since = (now - timedelta(days=days * 2)).strftime("%Y-%m-%d")

        print(f"\nComparing two {days}-day periods:")
        print(f"  Current:  {current_since} to {current_until}")
        print(f"  Previous: {previous_since} to {previous_until}\n")

        # Analyze both periods
        print("Analyzing current period...")
        current = self.analyze_period(repos, current_since, current_until)

        print("Analyzing previous period...")
        previous = self.analyze_period(repos, previous_since, previous_until)

        # Calculate changes
        comparison = {
            "metadata": {
                "generated_at": now.isoformat(),
                "period_days": days,
                "current_period": {"since": current_since, "until": current_until},
                "previous_period": {"since": previous_since, "until": previous_until},
            },
            "current": current,
            "previous": previous,
            "changes": self._calculate_changes(current, previous),
        }

        return comparison

    def _calculate_changes(
        self, current: dict[str, Any], previous: dict[str, Any]
    ) -> dict[str, Any]:
        """Calculate changes between two periods."""
        changes = {}

        # Numeric changes
        for key in ["commits", "conventional_commits", "breaking_changes"]:
            curr_val = current[key]
            prev_val = previous[key]
            diff = curr_val - prev_val
            pct_change = ((diff / prev_val * 100) if prev_val > 0 else 0) if diff != 0 else 0

            changes[key] = {
                "current": curr_val,
                "previous": prev_val,
                "difference": diff,
                "percent_change": pct_change,
            }

        # Contributors
        curr_contributors = set(current["contributors"])
        prev_contributors = set(previous["contributors"])
        changes["contributors"] = {
            "current": len(curr_contributors),
            "previous": len(prev_contributors),
            "new": list(curr_contributors - prev_contributors),
            "lost": list(prev_contributors - curr_contributors),
        }

        # Issues
        curr_issues = set(current["issues_referenced"])
        prev_issues = set(previous["issues_referenced"])
        changes["issues"] = {
            "current": len(curr_issues),
            "previous": len(prev_issues),
            "new": list(curr_issues - prev_issues),
            "continuing": list(curr_issues & prev_issues),
        }

        # Commit type changes
        all_types = set(current["commit_types"].keys()) | set(
            previous["commit_types"].keys()
        )
        type_changes = {}
        for commit_type in all_types:
            curr = current["commit_types"].get(commit_type, 0)
            prev = previous["commit_types"].get(commit_type, 0)
            diff = curr - prev
            type_changes[commit_type] = {
                "current": curr,
                "previous": prev,
                "difference": diff,
            }
        changes["commit_types"] = type_changes

        # Repository activity changes
        all_repos = set(current["repositories"].keys()) | set(
            previous["repositories"].keys()
        )
        repo_changes = {}
        for repo in all_repos:
            curr_commits = (
                current["repositories"][repo]["total_commits"]
                if repo in current["repositories"]
                else 0
            )
            prev_commits = (
                previous["repositories"][repo]["total_commits"]
                if repo in previous["repositories"]
                else 0
            )
            diff = curr_commits - prev_commits

            repo_changes[repo] = {
                "current": curr_commits,
                "previous": prev_commits,
                "difference": diff,
            }
        changes["repositories"] = repo_changes

        return changes

    def generate_markdown(self, comparison: dict[str, Any]) -> str:
        """Generate markdown report from comparison data."""
        lines = []
        changes = comparison["changes"]
        metadata = comparison["metadata"]

        # Header
        lines.append(f"# Period Comparison Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append(
            f"**Current Period:** {metadata['current_period']['since']} to {metadata['current_period']['until']}"
        )
        lines.append(
            f"**Previous Period:** {metadata['previous_period']['since']} to {metadata['previous_period']['until']}"
        )
        lines.append(f"**Period Length:** {metadata['period_days']} days")
        lines.append("")

        # Executive summary
        lines.append("## Executive Summary")
        lines.append("")

        commit_change = changes["commits"]
        trend = "📈" if commit_change["difference"] > 0 else "📉" if commit_change["difference"] < 0 else "➡️"
        lines.append(
            f"**Commit Activity:** {commit_change['current']} commits ({trend} "
            f"{commit_change['difference']:+d}, {commit_change['percent_change']:+.1f}%)"
        )

        conv_change = changes["conventional_commits"]
        lines.append(
            f"**Conventional Commits:** {conv_change['current']} "
            f"({conv_change['difference']:+d})"
        )

        contrib_change = changes["contributors"]
        lines.append(
            f"**Active Contributors:** {contrib_change['current']} "
            f"(previously {contrib_change['previous']})"
        )

        issue_change = changes["issues"]
        lines.append(
            f"**Issues Worked On:** {issue_change['current']} "
            f"(previously {issue_change['previous']})"
        )

        if changes["breaking_changes"]["current"] > 0:
            lines.append(
                f"**Breaking Changes:** {changes['breaking_changes']['current']} ⚠️"
            )

        lines.append("")

        # Commit activity trend
        lines.append("## Commit Activity Trend")
        lines.append("")
        lines.append("| Metric | Current | Previous | Change |")
        lines.append("|--------|---------|----------|--------|")

        for key in ["commits", "conventional_commits"]:
            data = changes[key]
            trend_emoji = "📈" if data["difference"] > 0 else "📉" if data["difference"] < 0 else "➡️"
            lines.append(
                f"| {key.replace('_', ' ').title()} | {data['current']} | "
                f"{data['previous']} | {trend_emoji} {data['difference']:+d} ({data['percent_change']:+.1f}%) |"
            )
        lines.append("")

        # Work type distribution
        if changes["commit_types"]:
            lines.append("## Work Type Distribution")
            lines.append("")
            lines.append("| Type | Current | Previous | Change |")
            lines.append("|------|---------|----------|--------|")

            for commit_type, data in sorted(
                changes["commit_types"].items(),
                key=lambda x: x[1]["current"],
                reverse=True,
            ):
                trend_emoji = "📈" if data["difference"] > 0 else "📉" if data["difference"] < 0 else "➡️"
                lines.append(
                    f"| {commit_type} | {data['current']} | {data['previous']} | "
                    f"{trend_emoji} {data['difference']:+d} |"
                )
            lines.append("")

        # Repository activity
        if changes["repositories"]:
            lines.append("## Repository Activity")
            lines.append("")
            lines.append("| Repository | Current | Previous | Change |")
            lines.append("|------------|---------|----------|--------|")

            for repo, data in sorted(
                changes["repositories"].items(),
                key=lambda x: abs(x[1]["difference"]),
                reverse=True,
            ):
                if data["current"] > 0 or data["previous"] > 0:
                    trend_emoji = "📈" if data["difference"] > 0 else "📉" if data["difference"] < 0 else "➡️"
                    lines.append(
                        f"| {repo} | {data['current']} | {data['previous']} | "
                        f"{trend_emoji} {data['difference']:+d} |"
                    )
            lines.append("")

        # Contributors
        if changes["contributors"]["new"] or changes["contributors"]["lost"]:
            lines.append("## Contributor Changes")
            lines.append("")
            if changes["contributors"]["new"]:
                lines.append("**New contributors:**")
                for contributor in changes["contributors"]["new"]:
                    lines.append(f"- ✨ {contributor}")
                lines.append("")
            if changes["contributors"]["lost"]:
                lines.append("**No longer active:**")
                for contributor in changes["contributors"]["lost"]:
                    lines.append(f"- 👋 {contributor}")
                lines.append("")

        # Issues
        if changes["issues"]["new"]:
            lines.append("## Issues Worked On")
            lines.append("")
            lines.append(f"**New issues ({len(changes['issues']['new'])}):**")
            for issue in sorted(changes["issues"]["new"]):
                lines.append(f"- #{issue}")
            lines.append("")

            if changes["issues"]["continuing"]:
                lines.append(
                    f"**Continuing from previous period ({len(changes['issues']['continuing'])}):**"
                )
                for issue in sorted(changes["issues"]["continuing"]):
                    lines.append(f"- #{issue}")
                lines.append("")

        # Insights
        lines.append("## Insights")
        lines.append("")

        insights = self._generate_insights(changes)
        for insight in insights:
            lines.append(f"- {insight}")
        lines.append("")

        return "\n".join(lines)

    def _generate_insights(self, changes: dict[str, Any]) -> list[str]:
        """Generate insights from comparison data."""
        insights = []

        # Commit activity
        commit_change = changes["commits"]
        if commit_change["difference"] > 0:
            insights.append(
                f"✅ Productivity increased by {commit_change['percent_change']:.1f}% "
                f"({commit_change['difference']:+d} commits)"
            )
        elif commit_change["difference"] < 0:
            insights.append(
                f"⚠️ Productivity decreased by {abs(commit_change['percent_change']):.1f}% "
                f"({commit_change['difference']} commits)"
            )

        # Conventional commits
        conv_pct_current = (
            (changes["conventional_commits"]["current"] / commit_change["current"] * 100)
            if commit_change["current"] > 0
            else 0
        )
        conv_pct_previous = (
            (changes["conventional_commits"]["previous"] / commit_change["previous"] * 100)
            if commit_change["previous"] > 0
            else 0
        )

        if conv_pct_current > conv_pct_previous:
            insights.append(
                f"✅ Code quality improved: {conv_pct_current:.1f}% conventional commits "
                f"(up from {conv_pct_previous:.1f}%)"
            )

        # Repository focus
        repo_changes = changes["repositories"]
        most_increased = max(
            ((repo, data) for repo, data in repo_changes.items()),
            key=lambda x: x[1]["difference"],
            default=None,
        )
        most_decreased = min(
            ((repo, data) for repo, data in repo_changes.items()),
            key=lambda x: x[1]["difference"],
            default=None,
        )

        if most_increased and most_increased[1]["difference"] > 0:
            insights.append(
                f"📊 Focus shifted to {most_increased[0]}: "
                f"{most_increased[1]['difference']:+d} commits"
            )

        if most_decreased and most_decreased[1]["difference"] < -2:
            insights.append(
                f"📊 Reduced activity in {most_decreased[0]}: "
                f"{most_decreased[1]['difference']} commits"
            )

        # Work type insights
        type_changes = changes["commit_types"]
        if "feat" in type_changes and type_changes["feat"]["difference"] > 0:
            insights.append(
                f"🚀 More feature development: {type_changes['feat']['difference']:+d} feature commits"
            )
        if "fix" in type_changes and type_changes["fix"]["difference"] > 0:
            insights.append(
                f"🔧 More bug fixes: {type_changes['fix']['difference']:+d} fix commits"
            )
        if "docs" in type_changes and type_changes["docs"]["difference"] > 0:
            insights.append(
                f"📝 More documentation: {type_changes['docs']['difference']:+d} doc commits"
            )

        # Issues
        if changes["issues"]["new"]:
            insights.append(
                f"🎯 Started work on {len(changes['issues']['new'])} new issue(s)"
            )

        return insights


def main():
    """Main entry point for period comparison."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compare commit activity between two time periods"
    )
    parser.add_argument(
        "--config",
        default="config/collection/production.yaml",
        help="Path to collection config (default: production.yaml)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days per period (default: 7)",
    )
    parser.add_argument(
        "--output",
        help="Output file path (defaults to reports/adhoc/period_comparison_TIMESTAMP.md)",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "both"],
        default="both",
        help="Output format (default: both)",
    )

    args = parser.parse_args()

    # Generate comparison
    generator = PeriodComparisonGenerator()
    try:
        comparison = generator.compare_periods(args.config, args.days)
        markdown = generator.generate_markdown(comparison)

        # Determine output path
        if args.output:
            output_path = Path(args.output)
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_path = (
                Path("reports/adhoc") / f"period_comparison_{args.days}d_{timestamp}.md"
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save markdown
        if args.format in ["markdown", "both"]:
            md_path = (
                output_path
                if args.format == "markdown"
                else output_path.with_suffix(".md")
            )
            md_path.write_text(markdown)
            print(f"\nMarkdown report saved: {md_path}")

        # Save JSON
        if args.format in ["json", "both"]:
            json_path = (
                output_path if args.format == "json" else output_path.with_suffix(".json")
            )
            json_path.write_text(json.dumps(comparison, indent=2))
            print(f"JSON report saved: {json_path}")

        # Print summary
        print("\n" + "=" * 60)
        print(f"Period Comparison - {args.days} Days")
        print("=" * 60)
        changes = comparison["changes"]
        print(
            f"Commits: {changes['commits']['current']} (prev: {changes['commits']['previous']}, "
            f"{changes['commits']['difference']:+d})"
        )
        print(
            f"Contributors: {changes['contributors']['current']} "
            f"(prev: {changes['contributors']['previous']})"
        )
        print(
            f"Issues: {changes['issues']['current']} "
            f"(prev: {changes['issues']['previous']})"
        )

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
