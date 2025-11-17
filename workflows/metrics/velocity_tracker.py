"""Track team velocity and productivity metrics over time."""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from github_pm.commit_analyzer import CommitAnalyzer
from github_pm.data_collector import DataCollector


class VelocityTracker:
    """Tracks velocity and productivity metrics across cycles."""

    def __init__(self):
        """Initialize velocity tracker."""
        self.analyzer = CommitAnalyzer()
        self.collector = DataCollector()

    def load_config(self, config_path: str) -> dict[str, Any]:
        """Load repository configuration."""
        with open(config_path) as f:
            return yaml.safe_load(f)

    def analyze_cycle(
        self, repos: list[dict], since: str, until: str, cycle_name: str
    ) -> dict[str, Any]:
        """
        Analyze a single cycle/sprint.

        Args:
            repos: List of repository configurations
            since: Cycle start date (YYYY-MM-DD)
            until: Cycle end date (YYYY-MM-DD)
            cycle_name: Human-readable cycle name (e.g., "W47", "Sprint 12")

        Returns:
            Cycle metrics
        """
        cycle_data = {
            "cycle_name": cycle_name,
            "period": {"since": since, "until": until},
            "commits": 0,
            "conventional_commits": 0,
            "issues_referenced": set(),
            "breaking_changes": 0,
            "commit_types": {},
            "contributors": {},
            "repositories": {},
            "daily_commits": {},
        }

        print(f"  Analyzing {cycle_name} ({since} to {until})...")

        for repo_config in repos:
            owner = repo_config["owner"]
            name = repo_config["name"]
            repo_key = f"{owner}/{name}"

            try:
                commits = self.analyzer.fetch_commits(
                    owner, name, since, until, limit=500
                )

                if not commits:
                    continue

                analysis = self.analyzer.analyze_commits(commits)

                # Store repo-specific data
                cycle_data["repositories"][repo_key] = {
                    "commits": analysis["total_commits"],
                    "conventional_commits": analysis["conventional_commits"],
                }

                # Aggregate totals
                cycle_data["commits"] += analysis["total_commits"]
                cycle_data["conventional_commits"] += analysis["conventional_commits"]
                cycle_data["issues_referenced"].update(
                    analysis["issue_references"].keys()
                )
                cycle_data["breaking_changes"] += len(analysis["breaking_changes"])

                # Aggregate commit types
                for commit_type, count in analysis["commit_types"].items():
                    cycle_data["commit_types"][commit_type] = (
                        cycle_data["commit_types"].get(commit_type, 0) + count
                    )

                # Aggregate contributors
                for author, count in analysis["authors"].items():
                    cycle_data["contributors"][author] = (
                        cycle_data["contributors"].get(author, 0) + count
                    )

                # Aggregate daily commits
                for day, count in analysis["daily_commits"].items():
                    cycle_data["daily_commits"][day] = (
                        cycle_data["daily_commits"].get(day, 0) + count
                    )

            except Exception as e:
                print(f"    Error analyzing {repo_key}: {e}")
                continue

        # Convert sets to counts
        cycle_data["issues_completed"] = len(cycle_data["issues_referenced"])
        cycle_data["issues_referenced"] = list(cycle_data["issues_referenced"])

        # Calculate quality metrics
        cycle_data["conventional_percentage"] = (
            (cycle_data["conventional_commits"] / cycle_data["commits"] * 100)
            if cycle_data["commits"] > 0
            else 0
        )

        print(
            f"    {cycle_data['commits']} commits, {cycle_data['issues_completed']} issues"
        )

        return cycle_data

    def generate_velocity_report(
        self, config_path: str, cycles: int = 6, cycle_length: int = 7
    ) -> dict[str, Any]:
        """
        Generate velocity report over multiple cycles.

        Args:
            config_path: Path to collection config YAML
            cycles: Number of cycles to analyze
            cycle_length: Length of each cycle in days (default: 7 for weekly)

        Returns:
            Velocity data and analysis
        """
        config = self.load_config(config_path)
        repos = config.get("repositories", [])

        print(f"\nAnalyzing velocity over {cycles} cycles ({cycle_length} days each)\n")

        # Calculate cycle date ranges
        cycle_data_list = []
        now = datetime.now()

        for i in range(cycles):
            cycle_num = cycles - i
            cycle_end = now - timedelta(days=i * cycle_length)
            cycle_start = cycle_end - timedelta(days=cycle_length)

            # Determine cycle name based on length
            if cycle_length == 7:
                cycle_name = f"W{cycle_start.strftime('%U')}"
            elif cycle_length == 14:
                cycle_name = f"Sprint {cycle_num}"
            else:
                cycle_name = f"Cycle {cycle_num}"

            cycle = self.analyze_cycle(
                repos,
                cycle_start.strftime("%Y-%m-%d"),
                cycle_end.strftime("%Y-%m-%d"),
                cycle_name,
            )
            cycle_data_list.append(cycle)

        # Calculate trends
        trends = self._calculate_trends(cycle_data_list)

        # Calculate averages
        total_commits = sum(c["commits"] for c in cycle_data_list)
        total_issues = sum(c["issues_completed"] for c in cycle_data_list)
        avg_commits = total_commits / cycles if cycles > 0 else 0
        avg_issues = total_issues / cycles if cycles > 0 else 0

        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "cycles_analyzed": cycles,
                "cycle_length_days": cycle_length,
            },
            "cycles": list(reversed(cycle_data_list)),  # Chronological order
            "averages": {
                "commits_per_cycle": avg_commits,
                "issues_per_cycle": avg_issues,
                "conventional_percentage": (
                    sum(c["conventional_percentage"] for c in cycle_data_list) / cycles
                    if cycles > 0
                    else 0
                ),
            },
            "trends": trends,
        }

        return report

    def _calculate_trends(self, cycles: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate trends from cycle data."""
        if len(cycles) < 2:
            return {}

        # Reverse to chronological order
        cycles = list(reversed(cycles))

        # Calculate trends
        recent = cycles[-1]
        previous = cycles[-2]

        trends = {
            "commits": {
                "direction": "up"
                if recent["commits"] > previous["commits"]
                else "down"
                if recent["commits"] < previous["commits"]
                else "stable",
                "change": recent["commits"] - previous["commits"],
            },
            "issues": {
                "direction": "up"
                if recent["issues_completed"] > previous["issues_completed"]
                else "down"
                if recent["issues_completed"] < previous["issues_completed"]
                else "stable",
                "change": recent["issues_completed"] - previous["issues_completed"],
            },
            "quality": {
                "direction": "up"
                if recent["conventional_percentage"] > previous["conventional_percentage"]
                else "down"
                if recent["conventional_percentage"] < previous["conventional_percentage"]
                else "stable",
                "change": recent["conventional_percentage"]
                - previous["conventional_percentage"],
            },
        }

        # Overall velocity (last 3 cycles)
        recent_cycles = cycles[-3:] if len(cycles) >= 3 else cycles
        avg_recent_commits = sum(c["commits"] for c in recent_cycles) / len(
            recent_cycles
        )
        avg_recent_issues = sum(c["issues_completed"] for c in recent_cycles) / len(
            recent_cycles
        )

        trends["velocity"] = {
            "avg_commits": avg_recent_commits,
            "avg_issues": avg_recent_issues,
            "trend": "improving"
            if trends["commits"]["direction"] == "up"
            and trends["quality"]["direction"] == "up"
            else "declining"
            if trends["commits"]["direction"] == "down"
            else "stable",
        }

        return trends

    def generate_markdown(self, report: dict[str, Any]) -> str:
        """Generate markdown report from velocity data."""
        lines = []
        metadata = report["metadata"]
        cycles = report["cycles"]
        averages = report["averages"]
        trends = report["trends"]

        # Header
        cycle_type = "Weekly" if metadata["cycle_length_days"] == 7 else f"{metadata['cycle_length_days']}-Day"
        lines.append(f"# Velocity Report - Last {metadata['cycles_analyzed']} Cycles")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Cycle Type:** {cycle_type}")
        lines.append("")

        # Executive summary
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(
            f"**Average Velocity:** {averages['issues_per_cycle']:.1f} issues/cycle, {averages['commits_per_cycle']:.1f} commits/cycle"
        )
        lines.append(
            f"**Code Quality:** {averages['conventional_percentage']:.1f}% conventional commits"
        )

        if trends:
            velocity_emoji = (
                "📈" if trends["velocity"]["trend"] == "improving" else "📉" if trends["velocity"]["trend"] == "declining" else "➡️"
            )
            lines.append(
                f"**Trend:** {velocity_emoji} {trends['velocity']['trend'].title()}"
            )

        lines.append("")

        # Cycle-by-cycle breakdown
        lines.append("## Velocity Trend")
        lines.append("")
        lines.append(
            "| Cycle | Issues | Commits | Quality | Breaking Changes | Contributors |"
        )
        lines.append(
            "|-------|--------|---------|---------|------------------|--------------|"
        )

        for cycle in cycles:
            lines.append(
                f"| {cycle['cycle_name']} | {cycle['issues_completed']} | "
                f"{cycle['commits']} | {cycle['conventional_percentage']:.0f}% | "
                f"{cycle['breaking_changes']} | {len(cycle['contributors'])} |"
            )

        lines.append("")

        # Trend indicators
        if trends:
            lines.append("## Trend Indicators")
            lines.append("")

            commit_trend = trends["commits"]
            trend_emoji = "📈" if commit_trend["direction"] == "up" else "📉" if commit_trend["direction"] == "down" else "➡️"
            lines.append(
                f"**Commit Volume:** {trend_emoji} {commit_trend['direction'].title()} "
                f"({commit_trend['change']:+d} vs previous cycle)"
            )

            issue_trend = trends["issues"]
            trend_emoji = "📈" if issue_trend["direction"] == "up" else "📉" if issue_trend["direction"] == "down" else "➡️"
            lines.append(
                f"**Issue Completion:** {trend_emoji} {issue_trend['direction'].title()} "
                f"({issue_trend['change']:+d} vs previous cycle)"
            )

            quality_trend = trends["quality"]
            trend_emoji = "📈" if quality_trend["direction"] == "up" else "📉" if quality_trend["direction"] == "down" else "➡️"
            lines.append(
                f"**Code Quality:** {trend_emoji} {quality_trend['direction'].title()} "
                f"({quality_trend['change']:+.1f}% vs previous cycle)"
            )

            lines.append("")

        # Work distribution (recent cycle)
        recent_cycle = cycles[-1]
        if recent_cycle["commit_types"]:
            lines.append(f"## Work Distribution ({recent_cycle['cycle_name']})")
            lines.append("")
            lines.append("| Type | Count | Percentage |")
            lines.append("|------|-------|------------|")

            total = recent_cycle["commits"]
            for commit_type, count in sorted(
                recent_cycle["commit_types"].items(), key=lambda x: x[1], reverse=True
            ):
                pct = (count / total * 100) if total > 0 else 0
                lines.append(f"| {commit_type} | {count} | {pct:.1f}% |")

            lines.append("")

        # Repository distribution (recent cycle)
        if recent_cycle["repositories"]:
            lines.append(f"## Repository Activity ({recent_cycle['cycle_name']})")
            lines.append("")
            lines.append("| Repository | Commits | Quality |")
            lines.append("|------------|---------|---------|")

            for repo, data in sorted(
                recent_cycle["repositories"].items(),
                key=lambda x: x[1]["commits"],
                reverse=True,
            ):
                quality = (
                    (data["conventional_commits"] / data["commits"] * 100)
                    if data["commits"] > 0
                    else 0
                )
                lines.append(f"| {repo} | {data['commits']} | {quality:.0f}% |")

            lines.append("")

        # Contributor activity (recent cycle)
        if recent_cycle["contributors"]:
            lines.append(f"## Contributors ({recent_cycle['cycle_name']})")
            lines.append("")

            for contributor, commits in sorted(
                recent_cycle["contributors"].items(), key=lambda x: x[1], reverse=True
            ):
                pct = (
                    (commits / recent_cycle["commits"] * 100)
                    if recent_cycle["commits"] > 0
                    else 0
                )
                lines.append(f"- **{contributor}**: {commits} commits ({pct:.1f}%)")

            lines.append("")

        # Insights
        lines.append("## Insights")
        lines.append("")

        insights = self._generate_insights(report)
        for insight in insights:
            lines.append(f"- {insight}")

        lines.append("")

        return "\n".join(lines)

    def _generate_insights(self, report: dict[str, Any]) -> list[str]:
        """Generate insights from velocity data."""
        insights = []
        trends = report["trends"]
        averages = report["averages"]
        cycles = report["cycles"]

        if not trends:
            return insights

        # Velocity insights
        if trends["velocity"]["trend"] == "improving":
            insights.append(
                f"✅ Velocity improving: {trends['velocity']['avg_commits']:.1f} commits/cycle average"
            )
        elif trends["velocity"]["trend"] == "declining":
            insights.append(
                f"⚠️ Velocity declining: {trends['velocity']['avg_commits']:.1f} commits/cycle average"
            )

        # Quality insights
        if averages["conventional_percentage"] > 70:
            insights.append(
                f"✅ Excellent code quality: {averages['conventional_percentage']:.1f}% conventional commits"
            )
        elif averages["conventional_percentage"] < 50:
            insights.append(
                f"⚠️ Code quality needs attention: {averages['conventional_percentage']:.1f}% conventional commits"
            )

        if trends["quality"]["direction"] == "up":
            insights.append(
                f"📈 Code quality improving: +{trends['quality']['change']:.1f}% conventional commits"
            )

        # Issue completion insights
        recent = cycles[-1]
        if recent["issues_completed"] > averages["issues_per_cycle"] * 1.2:
            insights.append(
                f"🚀 High productivity this cycle: {recent['issues_completed']} issues (above average)"
            )
        elif recent["issues_completed"] < averages["issues_per_cycle"] * 0.8:
            insights.append(
                f"⚠️ Lower productivity this cycle: {recent['issues_completed']} issues (below average)"
            )

        # Breaking changes
        total_breaking = sum(c["breaking_changes"] for c in cycles)
        if total_breaking > 0:
            avg_breaking = total_breaking / len(cycles)
            insights.append(
                f"⚠️ Breaking changes: {avg_breaking:.1f} per cycle (handle with care)"
            )

        # Consistency
        commit_variance = sum(
            abs(c["commits"] - averages["commits_per_cycle"]) for c in cycles
        ) / len(cycles)
        if commit_variance < averages["commits_per_cycle"] * 0.2:
            insights.append("✅ Consistent velocity across cycles")
        elif commit_variance > averages["commits_per_cycle"] * 0.5:
            insights.append("⚠️ High variance in velocity - consider more consistent pacing")

        return insights


def main():
    """Main entry point for velocity tracking."""
    import argparse

    parser = argparse.ArgumentParser(description="Track velocity over time")
    parser.add_argument(
        "--config",
        default="config/collection/production.yaml",
        help="Path to collection config (default: production.yaml)",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=6,
        help="Number of cycles to analyze (default: 6)",
    )
    parser.add_argument(
        "--cycle-length",
        type=int,
        default=7,
        help="Length of each cycle in days (default: 7 for weekly)",
    )
    parser.add_argument(
        "--output",
        help="Output file path (defaults to reports/metrics/velocity_TIMESTAMP.md)",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "both"],
        default="both",
        help="Output format (default: both)",
    )

    args = parser.parse_args()

    # Generate report
    tracker = VelocityTracker()
    try:
        report = tracker.generate_velocity_report(
            args.config, args.cycles, args.cycle_length
        )
        markdown = tracker.generate_markdown(report)

        # Determine output path
        if args.output:
            output_path = Path(args.output)
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_path = Path("reports/metrics") / f"velocity_{timestamp}.md"
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
            json_path.write_text(json.dumps(report, indent=2))
            print(f"JSON report saved: {json_path}")

        # Print summary
        print("\n" + "=" * 60)
        print(f"Velocity Summary - Last {args.cycles} Cycles")
        print("=" * 60)
        print(
            f"Average: {report['averages']['issues_per_cycle']:.1f} issues/cycle, "
            f"{report['averages']['commits_per_cycle']:.1f} commits/cycle"
        )
        print(f"Quality: {report['averages']['conventional_percentage']:.1f}% conventional")
        if report["trends"]:
            print(f"Trend: {report['trends']['velocity']['trend'].title()}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
