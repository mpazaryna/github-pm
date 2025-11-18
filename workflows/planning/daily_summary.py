#!/usr/bin/env python3
"""
Daily Summary Generator - Compares SOD vs EOD snapshots.

Generates a summary report showing:
- What was accomplished today
- Issues that changed status
- Flow health analysis
- Recommendations for tomorrow
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.github_pm.data_collector import DataCollector


def compare_snapshots(sod_data: dict, eod_data: dict) -> dict:
    """
    Compare SOD and EOD snapshots to identify changes.

    Args:
        sod_data: Start of day snapshot data
        eod_data: End of day snapshot data

    Returns:
        Dictionary with comparison results
    """
    sod_issues = {issue["number"]: issue for issue in sod_data.get("issues", [])}
    eod_issues = {issue["number"]: issue for issue in eod_data.get("issues", [])}

    # Find status changes
    status_changes = []

    for issue_num in set(sod_issues.keys()) & set(eod_issues.keys()):
        sod_issue = sod_issues[issue_num]
        eod_issue = eod_issues[issue_num]

        sod_state = sod_issue.get("state")
        eod_state = eod_issue.get("state")

        if sod_state != eod_state:
            status_changes.append({
                "number": issue_num,
                "title": eod_issue.get("title"),
                "repository": eod_issue.get("repository"),
                "old_state": sod_state,
                "new_state": eod_state,
            })

    # Count new and closed issues
    new_issues = [
        eod_issues[num] for num in set(eod_issues.keys()) - set(sod_issues.keys())
    ]

    closed_issues = [
        issue for issue in status_changes if issue["new_state"] == "CLOSED"
    ]

    return {
        "status_changes": status_changes,
        "new_issues": new_issues,
        "closed_issues": closed_issues,
        "total_sod": len(sod_issues),
        "total_eod": len(eod_issues),
    }


def extract_status_from_labels(issue: dict) -> str:
    """
    Extract workflow status from issue labels.

    Note: "done" is determined by CLOSED state, not labels.
    Only OPEN issues have workflow status labels.
    """
    # Closed issues are always "done"
    if issue.get("state") == "CLOSED":
        return "done"

    # Only OPEN issues can be in workflow states
    labels = [l.get("name", "").lower() for l in issue.get("labels", [])]

    # Support multiple label formats
    if any("status:review" in l or "status:in review" in l or "in review" in l for l in labels):
        return "in_review"
    if any("status:progress" in l or "status:in progress" in l or "status:wip" in l or "in progress" in l or "wip" in l for l in labels):
        return "in_progress"
    if any("status:ready" in l or "ready" in l for l in labels):
        return "ready"
    if any("status:backlog" in l or "backlog" in l for l in labels):
        return "backlog"

    # Open issues without status labels = backlog
    return "backlog"


def analyze_flow(sod_data: dict, eod_data: dict) -> dict:
    """Analyze workflow health and flow."""
    def count_by_status(issues):
        counts = {"backlog": 0, "ready": 0, "in_progress": 0, "in_review": 0, "done": 0}
        for issue in issues:
            status = extract_status_from_labels(issue)
            counts[status] += 1
        return counts

    sod_counts = count_by_status(sod_data.get("issues", []))
    eod_counts = count_by_status(eod_data.get("issues", []))

    return {
        "sod": sod_counts,
        "eod": eod_counts,
        "changes": {
            status: eod_counts[status] - sod_counts[status]
            for status in sod_counts.keys()
        },
    }


def generate_recommendations(flow_analysis: dict, comparison: dict) -> list[str]:
    """Generate recommendations for tomorrow based on today's analysis."""
    recommendations = []

    eod_counts = flow_analysis["eod"]
    changes = flow_analysis["changes"]

    # Check for bottlenecks
    if eod_counts["in_review"] > 5:
        recommendations.append(
            f"🔴 **Review Bottleneck**: {eod_counts['in_review']} items waiting for review. "
            "Prioritize code reviews tomorrow."
        )

    if eod_counts["in_progress"] > 8:
        recommendations.append(
            f"⚠️ **WIP Overload**: {eod_counts['in_progress']} items in progress. "
            "Focus on completing existing work before starting new tasks."
        )

    if eod_counts["ready"] < 3:
        recommendations.append(
            f"📋 **Grooming Needed**: Only {eod_counts['ready']} items ready. "
            "Spend time grooming backlog items tomorrow."
        )

    # Check for progress
    completed_today = comparison["closed_issues"]
    if len(completed_today) >= 3:
        recommendations.append(
            f"✅ **Great Progress**: Completed {len(completed_today)} issues today. "
            "Keep up the momentum!"
        )
    elif len(completed_today) == 0 and changes.get("in_progress", 0) <= 0:
        recommendations.append(
            "⏸️ **Low Activity**: No issues completed or started today. "
            "Consider setting clearer daily goals."
        )

    # Flow health
    if changes.get("backlog", 0) > 5:
        recommendations.append(
            f"📥 **Backlog Growing**: {abs(changes['backlog'])} new items added to backlog. "
            "Schedule grooming session to triage."
        )

    return recommendations


def generate_report(date: str, sod_data: dict, eod_data: dict) -> str:
    """Generate markdown report comparing SOD and EOD."""
    comparison = compare_snapshots(sod_data, eod_data)
    flow_analysis = analyze_flow(sod_data, eod_data)
    recommendations = generate_recommendations(flow_analysis, comparison)

    sod_meta = sod_data.get("metadata", {})
    eod_meta = eod_data.get("metadata", {})

    report = f"""# Daily Summary - {date}

## Session Window
- **SOD**: {sod_meta.get('timestamp', 'Unknown')}
- **EOD**: {eod_meta.get('timestamp', 'Unknown')}
- **Repositories**: {len(sod_meta.get('repositories', []))}

## Today's Accomplishments ✅

### Issues Closed
"""

    if comparison["closed_issues"]:
        for issue in comparison["closed_issues"]:
            report += f"- **#{issue['number']}** - {issue['title']} ({issue['repository']})\n"
    else:
        report += "_No issues closed today_\n"

    report += f"""
### Status Changes
"""

    if comparison["status_changes"]:
        for change in comparison["status_changes"]:
            report += f"- **#{change['number']}** - {change['title']}: {change['old_state']} → {change['new_state']}\n"
    else:
        report += "_No status changes_\n"

    report += f"""
### New Issues
"""

    if comparison["new_issues"]:
        for issue in comparison["new_issues"][:5]:  # Limit to 5
            report += f"- **#{issue['number']}** - {issue['title']} ({issue.get('repository', 'Unknown')})\n"
        if len(comparison["new_issues"]) > 5:
            report += f"\n_...and {len(comparison['new_issues']) - 5} more_\n"
    else:
        report += "_No new issues_\n"

    report += f"""
## Status Flow 🔄

| Status | SOD | EOD | Change |
|--------|-----|-----|--------|
| Backlog | {flow_analysis['sod']['backlog']} | {flow_analysis['eod']['backlog']} | {flow_analysis['changes']['backlog']:+d} |
| Ready | {flow_analysis['sod']['ready']} | {flow_analysis['eod']['ready']} | {flow_analysis['changes']['ready']:+d} |
| In Progress | {flow_analysis['sod']['in_progress']} | {flow_analysis['eod']['in_progress']} | {flow_analysis['changes']['in_progress']:+d} |
| In Review | {flow_analysis['sod']['in_review']} | {flow_analysis['eod']['in_review']} | {flow_analysis['changes']['in_review']:+d} |
| Done | {flow_analysis['sod']['done']} | {flow_analysis['eod']['done']} | {flow_analysis['changes']['done']:+d} |

## Recommendations for Tomorrow 📋

"""

    if recommendations:
        for rec in recommendations:
            report += f"{rec}\n\n"
    else:
        report += "_No specific recommendations - steady as she goes! ⛵_\n"

    report += f"""
---
_Generated by GitHub PM SOD/EOD Workflow on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_
"""

    return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate daily summary from SOD/EOD snapshots"
    )
    parser.add_argument(
        "--date",
        help="Date to generate summary for (YYYY-MM-DD). Defaults to today.",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/daily",
        help="Output directory for reports (default: reports/daily)",
    )

    args = parser.parse_args()

    # Determine date
    if args.date:
        date = args.date
    else:
        date = datetime.now().strftime("%Y-%m-%d")

    # Initialize data collector
    collector = DataCollector()

    # Load snapshots
    try:
        print(f"Loading SOD snapshot for {date}...")
        sod_data = collector.load_snapshot(f"{date}-sod")
    except FileNotFoundError:
        print(f"❌ Error: SOD snapshot not found for {date}")
        print(f"   Run: uv run dashboard start --sod")
        sys.exit(1)

    try:
        print(f"Loading EOD snapshot for {date}...")
        eod_data = collector.load_snapshot(f"{date}-eod")
    except FileNotFoundError:
        print(f"❌ Error: EOD snapshot not found for {date}")
        print(f"   Run: uv run dashboard eod")
        sys.exit(1)

    # Generate report
    print("Generating daily summary...")
    report = generate_report(date, sod_data, eod_data)

    # Save report
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{date}-summary.md"
    output_file.write_text(report)

    print(f"✅ Report saved: {output_file}")
    print()
    print("Summary Preview:")
    print("=" * 60)
    print(report[:500] + "..." if len(report) > 500 else report)


if __name__ == "__main__":
    main()
