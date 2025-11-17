"""Compare two data collection periods to identify trends."""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class PeriodComparator:
    """Compares two data snapshots to identify trends and changes."""

    def __init__(self, workflow_config: dict[str, Any] | None = None):
        """
        Initialize period comparator.

        Args:
            workflow_config: Optional workflow configuration
        """
        self.config = workflow_config or {}
        self.trend_config = self.config.get("trend_analysis", {})
        self.threshold = self.trend_config.get("significant_change_threshold", 0.20)

    def compare(
        self, baseline: dict[str, Any], current: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Compare two snapshots and identify trends.

        Args:
            baseline: Earlier snapshot data
            current: More recent snapshot data

        Returns:
            Dictionary containing comparison results
        """
        baseline_summary = baseline.get("summary", {})
        current_summary = current.get("summary", {})

        results = {
            "metadata": {
                "baseline_date": baseline.get("metadata", {}).get("collected_at"),
                "current_date": current.get("metadata", {}).get("collected_at"),
                "analysis_date": datetime.now().isoformat(),
            },
            "overall_changes": self._compare_overall(baseline_summary, current_summary),
            "state_changes": self._compare_states(baseline_summary, current_summary),
            "repository_changes": self._compare_repositories(
                baseline_summary, current_summary
            ),
            "label_changes": self._compare_labels(baseline_summary, current_summary),
            "assignee_changes": self._compare_assignees(
                baseline_summary, current_summary
            ),
            "insights": [],
        }

        # Generate insights
        results["insights"] = self._generate_insights(results)

        return results

    def _compare_overall(
        self, baseline: dict[str, Any], current: dict[str, Any]
    ) -> dict[str, Any]:
        """Compare overall statistics."""
        baseline_total = baseline.get("total_issues", 0)
        current_total = current.get("total_issues", 0)
        change = current_total - baseline_total
        pct_change = (
            (change / baseline_total * 100) if baseline_total > 0 else 0.0
        )

        return {
            "baseline_total": baseline_total,
            "current_total": current_total,
            "absolute_change": change,
            "percent_change": round(pct_change, 2),
            "is_significant": abs(pct_change / 100) >= self.threshold,
        }

    def _compare_states(
        self, baseline: dict[str, Any], current: dict[str, Any]
    ) -> dict[str, Any]:
        """Compare issue states."""
        baseline_states = baseline.get("by_state", {})
        current_states = current.get("by_state", {})

        all_states = set(baseline_states.keys()) | set(current_states.keys())
        changes = {}

        for state in all_states:
            baseline_count = baseline_states.get(state, 0)
            current_count = current_states.get(state, 0)
            change = current_count - baseline_count
            pct_change = (
                (change / baseline_count * 100) if baseline_count > 0 else 0.0
            )

            changes[state] = {
                "baseline": baseline_count,
                "current": current_count,
                "change": change,
                "percent_change": round(pct_change, 2),
            }

        return changes

    def _compare_repositories(
        self, baseline: dict[str, Any], current: dict[str, Any]
    ) -> dict[str, Any]:
        """Compare repository statistics."""
        baseline_repos = baseline.get("by_repository", {})
        current_repos = current.get("by_repository", {})

        all_repos = set(baseline_repos.keys()) | set(current_repos.keys())
        changes = {}

        for repo in all_repos:
            baseline_count = baseline_repos.get(repo, 0)
            current_count = current_repos.get(repo, 0)
            change = current_count - baseline_count
            pct_change = (
                (change / baseline_count * 100) if baseline_count > 0 else 0.0
            )

            changes[repo] = {
                "baseline": baseline_count,
                "current": current_count,
                "change": change,
                "percent_change": round(pct_change, 2),
                "is_significant": abs(pct_change / 100) >= self.threshold,
            }

        return changes

    def _compare_labels(
        self, baseline: dict[str, Any], current: dict[str, Any]
    ) -> dict[str, Any]:
        """Compare label usage."""
        baseline_labels = baseline.get("by_label", {})
        current_labels = current.get("by_label", {})

        # Focus on labels that exist in current snapshot
        changes = {}
        for label in current_labels:
            baseline_count = baseline_labels.get(label, 0)
            current_count = current_labels.get(label, 0)
            change = current_count - baseline_count
            pct_change = (
                (change / baseline_count * 100) if baseline_count > 0 else 100.0
            )

            if baseline_count > 0 or current_count >= 3:  # Filter noise
                changes[label] = {
                    "baseline": baseline_count,
                    "current": current_count,
                    "change": change,
                    "percent_change": round(pct_change, 2),
                }

        # Sort by absolute change
        return dict(
            sorted(changes.items(), key=lambda x: abs(x[1]["change"]), reverse=True)
        )

    def _compare_assignees(
        self, baseline: dict[str, Any], current: dict[str, Any]
    ) -> dict[str, Any]:
        """Compare assignee workloads."""
        baseline_assignees = baseline.get("by_assignee", {})
        current_assignees = current.get("by_assignee", {})

        all_assignees = set(baseline_assignees.keys()) | set(
            current_assignees.keys()
        )
        changes = {}

        for assignee in all_assignees:
            baseline_count = baseline_assignees.get(assignee, 0)
            current_count = current_assignees.get(assignee, 0)
            change = current_count - baseline_count

            changes[assignee] = {
                "baseline": baseline_count,
                "current": current_count,
                "change": change,
            }

        return dict(
            sorted(changes.items(), key=lambda x: x[1]["current"], reverse=True)
        )

    def _generate_insights(self, results: dict[str, Any]) -> list[str]:
        """Generate human-readable insights from comparison."""
        insights = []

        # Overall trend
        overall = results["overall_changes"]
        if overall["is_significant"]:
            direction = "increased" if overall["absolute_change"] > 0 else "decreased"
            insights.append(
                f"Total issues {direction} by {abs(overall['absolute_change'])} "
                f"({abs(overall['percent_change'])}%)"
            )

        # State changes
        state_changes = results["state_changes"]
        if "OPEN" in state_changes:
            open_change = state_changes["OPEN"]["change"]
            if abs(open_change) >= 5:  # Significant threshold
                direction = "increased" if open_change > 0 else "decreased"
                insights.append(
                    f"Open issues {direction} by {abs(open_change)}"
                )

        # Repository hot spots
        repo_changes = results["repository_changes"]
        significant_repos = [
            (repo, data)
            for repo, data in repo_changes.items()
            if data.get("is_significant", False)
        ]
        if significant_repos:
            for repo, data in significant_repos[:3]:  # Top 3
                direction = "increased" if data["change"] > 0 else "decreased"
                insights.append(
                    f"Repository '{repo}' {direction} by {abs(data['change'])} issues"
                )

        # Label trends
        label_changes = results["label_changes"]
        top_growing_labels = [
            (label, data)
            for label, data in list(label_changes.items())[:5]
            if data["change"] > 0
        ]
        if top_growing_labels:
            top_label, top_data = top_growing_labels[0]
            insights.append(
                f"Label '{top_label}' grew most (+{top_data['change']} issues)"
            )

        # Workload changes
        assignee_changes = results["assignee_changes"]
        if "Unassigned" in assignee_changes:
            unassigned = assignee_changes["Unassigned"]
            if unassigned["change"] > 5:
                insights.append(
                    f"Unassigned issues increased by {unassigned['change']}"
                )

        return insights

    def generate_report(self, comparison_results: dict[str, Any]) -> str:
        """
        Generate a markdown report from comparison results.

        Args:
            comparison_results: Results from compare()

        Returns:
            Markdown-formatted report
        """
        lines = []

        lines.append("# Trend Analysis Report")
        lines.append("")
        lines.append(
            f"**Baseline:** {comparison_results['metadata']['baseline_date']}"
        )
        lines.append(
            f"**Current:** {comparison_results['metadata']['current_date']}"
        )
        lines.append("")

        # Key Insights
        lines.append("## Key Insights")
        lines.append("")
        for insight in comparison_results["insights"]:
            lines.append(f"- {insight}")
        lines.append("")

        # Overall Changes
        overall = comparison_results["overall_changes"]
        lines.append("## Overall Changes")
        lines.append("")
        lines.append(f"- Baseline Total: {overall['baseline_total']}")
        lines.append(f"- Current Total: {overall['current_total']}")
        lines.append(
            f"- Change: {overall['absolute_change']:+d} ({overall['percent_change']:+.1f}%)"
        )
        lines.append("")

        # State Changes
        lines.append("## State Changes")
        lines.append("")
        for state, data in comparison_results["state_changes"].items():
            lines.append(f"### {state}")
            lines.append(f"- Baseline: {data['baseline']}")
            lines.append(f"- Current: {data['current']}")
            lines.append(f"- Change: {data['change']:+d} ({data['percent_change']:+.1f}%)")
            lines.append("")

        # Top Repository Changes
        lines.append("## Repository Changes (Top 5)")
        lines.append("")
        repo_changes = sorted(
            comparison_results["repository_changes"].items(),
            key=lambda x: abs(x[1]["change"]),
            reverse=True,
        )
        for repo, data in repo_changes[:5]:
            lines.append(f"### {repo}")
            lines.append(f"- Change: {data['change']:+d} ({data['percent_change']:+.1f}%)")
            lines.append(f"- Baseline: {data['baseline']} → Current: {data['current']}")
            lines.append("")

        # Top Label Changes
        lines.append("## Label Changes (Top 10)")
        lines.append("")
        for label, data in list(comparison_results["label_changes"].items())[:10]:
            lines.append(
                f"- **{label}**: {data['change']:+d} ({data['baseline']} → {data['current']})"
            )
        lines.append("")

        return "\n".join(lines)


def main():
    """Main entry point for period comparison."""
    if len(sys.argv) < 3:
        print("Usage: uv run python compare_periods.py <baseline_snapshot> <current_snapshot>")
        print("Example: uv run python compare_periods.py 2025-01-17_09-30 2025-01-17_14-15")
        sys.exit(1)

    baseline_path = Path("data") / sys.argv[1]
    current_path = Path("data") / sys.argv[2]

    # Load snapshots
    print(f"Loading baseline: {baseline_path}")
    with open(baseline_path / "raw.json") as f:
        baseline = json.load(f)

    print(f"Loading current: {current_path}")
    with open(current_path / "raw.json") as f:
        current = json.load(f)

    # Load workflow config
    config_path = Path("config/workflows/workflow_config.yaml")
    workflow_config = {}
    if config_path.exists():
        import yaml

        with open(config_path) as f:
            workflow_config = yaml.safe_load(f)

    # Compare periods
    print("\nAnalyzing trends...")
    comparator = PeriodComparator(workflow_config)
    results = comparator.compare(baseline, current)

    # Generate report
    report = comparator.generate_report(results)

    # Save report
    output_path = Path("reports/adhoc") / f"trend_analysis_{sys.argv[1]}_to_{sys.argv[2]}.md"
    output_path.write_text(report)

    print(f"\nReport saved: {output_path}")
    print("\nKey Insights:")
    for insight in results["insights"]:
        print(f"  - {insight}")


if __name__ == "__main__":
    main()
