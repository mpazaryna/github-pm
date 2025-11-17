"""Local web dashboard for GitHub PM analytics."""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, render_template, request

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from workflows.code_analysis.daily_activity import DailyActivityReportGenerator
from workflows.code_analysis.period_comparison import PeriodComparisonGenerator
from workflows.metrics.velocity_tracker import VelocityTracker
from workflows.planning.roadmap_generator import RoadmapGenerator

app = Flask(__name__)


class DashboardDataCollector:
    """Collects data from all workflows for dashboard display."""

    def __init__(self, config_path: str = "config/collection/production.yaml"):
        """Initialize dashboard data collector."""
        self.config_path = config_path
        self.activity_generator = DailyActivityReportGenerator()
        self.comparison_generator = PeriodComparisonGenerator()
        self.velocity_tracker = VelocityTracker()
        self.roadmap_generator = RoadmapGenerator()

    def get_activity(self, since: str = None, until: str = None, days: int = 1) -> dict:
        """
        Get activity summary for a date range.

        Args:
            since: Start date (YYYY-MM-DD)
            until: End date (YYYY-MM-DD)
            days: Number of days (if since/until not provided)
        """
        try:
            # If since/until not provided, calculate from days
            if not since or not until:
                until_date = datetime.now()
                since_date = until_date - timedelta(days=days)
                since = since_date.strftime("%Y-%m-%d")
                until = until_date.strftime("%Y-%m-%d")

            # Calculate days for the range
            since_dt = datetime.strptime(since, "%Y-%m-%d")
            until_dt = datetime.strptime(until, "%Y-%m-%d")
            range_days = (until_dt - since_dt).days

            data = self.activity_generator.generate_report(
                self.config_path, days=max(range_days, 1), format_type="both"
            )

            return {
                "status": "success",
                "period": {"since": since, "until": until},
                "data": {
                    "commits": data["totals"]["commits"],
                    "issues": len(data["totals"]["issues_referenced"]),
                    "repos_active": len(data["repositories"]),
                    "conventional_pct": (
                        (data["totals"]["conventional_commits"] / data["totals"]["commits"] * 100)
                        if data["totals"]["commits"] > 0
                        else 0
                    ),
                    "repositories": data["repositories"],
                    "commit_types": data["totals"]["commit_types"],
                },
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_comparison(self, days: int = 7, since: str = None, until: str = None) -> dict:
        """
        Get period comparison.

        Args:
            days: Period length in days
            since: Optional custom current period start
            until: Optional custom current period end
        """
        try:
            # For custom date range comparison, we need to calculate both periods
            if since and until:
                # Custom range - compare to previous period of same length
                since_dt = datetime.strptime(since, "%Y-%m-%d")
                until_dt = datetime.strptime(until, "%Y-%m-%d")
                period_days = (until_dt - since_dt).days

                # Calculate previous period
                prev_until = since_dt
                prev_since = prev_until - timedelta(days=period_days)

                comparison = self.comparison_generator.compare_periods(
                    self.config_path, days=period_days
                )
            else:
                comparison = self.comparison_generator.compare_periods(
                    self.config_path, days=days
                )

            return {
                "status": "success",
                "data": {
                    "current_commits": comparison["changes"]["commits"]["current"],
                    "previous_commits": comparison["changes"]["commits"]["previous"],
                    "commit_change": comparison["changes"]["commits"]["difference"],
                    "commit_change_pct": comparison["changes"]["commits"]["percent_change"],
                    "current_issues": comparison["changes"]["issues"]["current"],
                    "previous_issues": comparison["changes"]["issues"]["previous"],
                    "repo_changes": comparison["changes"]["repositories"],
                    "type_changes": comparison["changes"]["commit_types"],
                },
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_velocity(self, cycles: int = 6, cycle_length: int = 7) -> dict:
        """Get velocity metrics."""
        try:
            report = self.velocity_tracker.generate_velocity_report(
                self.config_path, cycles=cycles, cycle_length=cycle_length
            )
            return {
                "status": "success",
                "data": {
                    "avg_issues": report["averages"]["issues_per_cycle"],
                    "avg_commits": report["averages"]["commits_per_cycle"],
                    "quality_pct": report["averages"]["conventional_percentage"],
                    "trend": report["trends"]["velocity"]["trend"] if report.get("trends") else "unknown",
                    "cycles": report["cycles"],
                },
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_roadmap(self, velocity_days: int = 30) -> dict:
        """Get roadmap data."""
        try:
            roadmap = self.roadmap_generator.generate_roadmap(
                self.config_path, velocity_days=velocity_days
            )

            # Extract critical milestones
            critical = [
                m for m in roadmap["all_milestones"]
                if m["health"] in ["overdue", "at_risk"]
            ]

            # Count by health
            health_counts = {}
            for milestone in roadmap["all_milestones"]:
                health = milestone["health"]
                health_counts[health] = health_counts.get(health, 0) + 1

            return {
                "status": "success",
                "data": {
                    "total_milestones": len(roadmap["all_milestones"]),
                    "open_milestones": sum(
                        1 for m in roadmap["all_milestones"] if m["state"] == "open"
                    ),
                    "critical_count": len(critical),
                    "critical_milestones": critical,
                    "health_counts": health_counts,
                    "repositories": roadmap["repositories"],
                },
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_all_data(
        self,
        preset: str = "today",
        since: str = None,
        until: str = None,
    ) -> dict:
        """
        Collect all dashboard data based on date selection.

        Args:
            preset: Preset period (today, yesterday, week, month, etc.)
            since: Custom start date
            until: Custom end date
        """
        print(f"Collecting dashboard data (preset={preset}, since={since}, until={until})...")

        # Calculate dates based on preset or custom range
        if since and until:
            activity_since = since
            activity_until = until
            comp_days = (datetime.strptime(until, "%Y-%m-%d") -
                        datetime.strptime(since, "%Y-%m-%d")).days
        else:
            # Use presets
            until_dt = datetime.now()
            if preset == "today":
                since_dt = until_dt - timedelta(days=1)
                comp_days = 1
            elif preset == "yesterday":
                until_dt = until_dt - timedelta(days=1)
                since_dt = until_dt - timedelta(days=1)
                comp_days = 1
            elif preset == "week":
                since_dt = until_dt - timedelta(days=7)
                comp_days = 7
            elif preset == "two_weeks":
                since_dt = until_dt - timedelta(days=14)
                comp_days = 14
            elif preset == "month":
                since_dt = until_dt - timedelta(days=30)
                comp_days = 30
            elif preset == "quarter":
                since_dt = until_dt - timedelta(days=90)
                comp_days = 90
            else:  # Default to today
                since_dt = until_dt - timedelta(days=1)
                comp_days = 1

            activity_since = since_dt.strftime("%Y-%m-%d")
            activity_until = until_dt.strftime("%Y-%m-%d")

        print(f"  - Activity ({activity_since} to {activity_until})...")
        activity = self.get_activity(since=activity_since, until=activity_until)

        print(f"  - Comparison (last {comp_days} days vs previous {comp_days} days)...")
        comparison = self.get_comparison(days=comp_days, since=activity_since, until=activity_until)

        print("  - Velocity metrics...")
        velocity = self.get_velocity()

        print("  - Roadmap data...")
        roadmap = self.get_roadmap()

        return {
            "generated_at": datetime.now().isoformat(),
            "preset": preset,
            "date_range": {"since": activity_since, "until": activity_until},
            "activity": activity,
            "comparison": comparison,
            "velocity": velocity,
            "roadmap": roadmap,
        }


# Initialize data collector
collector = DashboardDataCollector()


@app.route("/")
def index():
    """Main dashboard page."""
    return render_template("dashboard.html")


@app.route("/api/data")
def get_data():
    """
    API endpoint to get all dashboard data.

    Query params:
        preset: today, yesterday, week, two_weeks, month, quarter
        since: YYYY-MM-DD (custom start date)
        until: YYYY-MM-DD (custom end date)
    """
    preset = request.args.get("preset", "today")
    since = request.args.get("since")
    until = request.args.get("until")

    data = collector.get_all_data(preset=preset, since=since, until=until)
    return jsonify(data)


@app.route("/api/activity")
def get_activity():
    """
    API endpoint for activity.

    Query params:
        since: YYYY-MM-DD
        until: YYYY-MM-DD
        days: number of days (if since/until not provided)
    """
    since = request.args.get("since")
    until = request.args.get("until")
    days = int(request.args.get("days", 1))

    data = collector.get_activity(since=since, until=until, days=days)
    return jsonify(data)


@app.route("/api/comparison")
def get_comparison():
    """
    API endpoint for period comparison.

    Query params:
        days: period length in days
        since: optional custom period start
        until: optional custom period end
    """
    days = int(request.args.get("days", 7))
    since = request.args.get("since")
    until = request.args.get("until")

    data = collector.get_comparison(days=days, since=since, until=until)
    return jsonify(data)


@app.route("/api/velocity")
def get_velocity():
    """
    API endpoint for velocity metrics.

    Query params:
        cycles: number of cycles to analyze
        cycle_length: length of each cycle in days
    """
    cycles = int(request.args.get("cycles", 6))
    cycle_length = int(request.args.get("cycle_length", 7))

    data = collector.get_velocity(cycles=cycles, cycle_length=cycle_length)
    return jsonify(data)


@app.route("/api/roadmap")
def get_roadmap():
    """
    API endpoint for roadmap data.

    Query params:
        velocity_days: days to calculate velocity over
    """
    velocity_days = int(request.args.get("velocity_days", 30))

    data = collector.get_roadmap(velocity_days=velocity_days)
    return jsonify(data)


def main():
    """Run the dashboard server."""
    import argparse

    parser = argparse.ArgumentParser(description="GitHub PM Dashboard Server")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to bind to (default: 5000)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    parser.add_argument(
        "--config",
        default="config/collection/production.yaml",
        help="Path to collection config (default: production.yaml)",
    )

    args = parser.parse_args()

    # Update config path
    global collector
    collector = DashboardDataCollector(args.config)

    print("\n" + "=" * 60)
    print("Dashboard Server")
    print("=" * 60)
    print(f"Server running at: http://{args.host}:{args.port}")
    print(f"Config: {args.config}")
    print("\nPress Ctrl+C to stop\n")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
