"""Generate visual roadmaps based on GitHub milestones and actual velocity."""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from github_pm.commit_analyzer import CommitAnalyzer


class RoadmapGenerator:
    """Generates roadmaps from GitHub milestones with velocity-based predictions."""

    def __init__(self):
        """Initialize roadmap generator."""
        self.analyzer = CommitAnalyzer()

    def load_config(self, config_path: str) -> dict[str, Any]:
        """Load repository configuration."""
        with open(config_path) as f:
            return yaml.safe_load(f)

    def fetch_milestones(self, owner: str, repo: str) -> list[dict[str, Any]]:
        """
        Fetch milestones from a repository using GitHub CLI.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            List of milestone data
        """
        try:
            # Fetch milestones (both open and closed)
            cmd = [
                "gh",
                "api",
                f"repos/{owner}/{repo}/milestones",
                "--jq",
                ".[] | {number, title, state, due_on, open_issues, closed_issues, description}",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if not result.stdout.strip():
                return []

            # Parse JSONL output (one JSON object per line)
            milestones = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    milestones.append(json.loads(line))

            return milestones

        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not fetch milestones for {owner}/{repo}: {e}")
            return []

    def calculate_velocity(
        self, owner: str, repo: str, days: int = 30
    ) -> dict[str, Any]:
        """
        Calculate recent velocity for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            days: Number of days to look back (default: 30)

        Returns:
            Velocity metrics
        """
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        until = datetime.now().strftime("%Y-%m-%d")

        try:
            commits = self.analyzer.fetch_commits(owner, repo, since, until, limit=200)
            analysis = self.analyzer.analyze_commits(commits)

            issues_per_week = len(analysis["issue_references"]) / (days / 7)
            commits_per_week = analysis["total_commits"] / (days / 7)

            return {
                "issues_per_week": issues_per_week,
                "commits_per_week": commits_per_week,
                "sample_period_days": days,
            }

        except Exception as e:
            print(f"Warning: Could not calculate velocity for {owner}/{repo}: {e}")
            return {"issues_per_week": 1.0, "commits_per_week": 5.0, "sample_period_days": 0}

    def analyze_milestone(
        self, milestone: dict[str, Any], velocity: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Analyze a milestone and predict completion.

        Args:
            milestone: Milestone data from GitHub
            velocity: Velocity metrics

        Returns:
            Milestone analysis with predictions
        """
        total_issues = milestone["open_issues"] + milestone["closed_issues"]
        completed = milestone["closed_issues"]
        remaining = milestone["open_issues"]

        # Calculate progress
        progress = (completed / total_issues * 100) if total_issues > 0 else 0

        # Predict completion date based on velocity
        issues_per_week = max(velocity["issues_per_week"], 0.5)  # Minimum 0.5 to avoid division by zero
        weeks_remaining = remaining / issues_per_week if issues_per_week > 0 else 0
        predicted_completion = datetime.now() + timedelta(weeks=weeks_remaining)

        # Parse due date
        due_date = None
        days_until_due = None
        if milestone.get("due_on"):
            try:
                due_date = datetime.fromisoformat(
                    milestone["due_on"].replace("Z", "+00:00")
                )
                # Make datetime.now() timezone-aware
                from datetime import timezone
                now = datetime.now(timezone.utc)
                days_until_due = (due_date - now).days
            except (ValueError, AttributeError):
                pass

        # Determine health status
        health = "unknown"
        if due_date:
            predicted_days = (predicted_completion - datetime.now()).days
            if milestone["state"] == "closed":
                health = "completed"
            elif days_until_due < 0:
                health = "overdue"
            elif predicted_days > days_until_due * 1.5:
                health = "at_risk"
            elif predicted_days > days_until_due * 1.2:
                health = "behind"
            elif progress > 80:
                health = "on_track"
            else:
                health = "good"
        else:
            if milestone["state"] == "closed":
                health = "completed"
            elif remaining == 0:
                health = "ready_to_close"
            else:
                health = "no_deadline"

        return {
            "title": milestone["title"],
            "state": milestone["state"],
            "description": milestone.get("description", ""),
            "total_issues": total_issues,
            "completed": completed,
            "remaining": remaining,
            "progress_percentage": progress,
            "due_date": due_date.isoformat() if due_date else None,
            "days_until_due": days_until_due,
            "predicted_completion": predicted_completion.isoformat(),
            "predicted_days_remaining": (predicted_completion - datetime.now()).days,
            "velocity": velocity,
            "health": health,
        }

    def generate_roadmap(
        self, config_path: str, velocity_days: int = 30
    ) -> dict[str, Any]:
        """
        Generate roadmap from all repositories.

        Args:
            config_path: Path to collection config YAML
            velocity_days: Days to calculate velocity over (default: 30)

        Returns:
            Roadmap data
        """
        config = self.load_config(config_path)
        repos = config.get("repositories", [])

        print(f"\nGenerating roadmap from {len(repos)} repositories...\n")

        roadmap_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "repositories": len(repos),
                "velocity_sample_days": velocity_days,
            },
            "repositories": {},
            "all_milestones": [],
        }

        for repo_config in repos:
            owner = repo_config["owner"]
            name = repo_config["name"]
            repo_key = f"{owner}/{name}"

            print(f"  Fetching milestones from {repo_key}...")

            milestones = self.fetch_milestones(owner, name)
            if not milestones:
                print(f"    No milestones found")
                continue

            print(f"    Found {len(milestones)} milestone(s)")
            print(f"  Calculating velocity...")
            velocity = self.calculate_velocity(owner, name, velocity_days)

            repo_data = {
                "owner": owner,
                "name": name,
                "velocity": velocity,
                "milestones": [],
            }

            for milestone in milestones:
                analysis = self.analyze_milestone(milestone, velocity)
                analysis["repository"] = repo_key
                repo_data["milestones"].append(analysis)
                roadmap_data["all_milestones"].append(analysis)

            roadmap_data["repositories"][repo_key] = repo_data

        # Sort milestones by due date (None at end)
        roadmap_data["all_milestones"].sort(
            key=lambda m: (
                m["due_date"] is None,
                m["due_date"] if m["due_date"] else "9999",
            )
        )

        return roadmap_data

    def generate_markdown(self, roadmap: dict[str, Any]) -> str:
        """Generate markdown roadmap report."""
        lines = []
        metadata = roadmap["metadata"]

        # Header
        lines.append("# Project Roadmap")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(
            f"**Velocity Sample Period:** Last {metadata['velocity_sample_days']} days"
        )
        lines.append("")

        # Summary statistics
        total_milestones = len(roadmap["all_milestones"])
        open_milestones = sum(
            1 for m in roadmap["all_milestones"] if m["state"] == "open"
        )
        at_risk = sum(
            1 for m in roadmap["all_milestones"] if m["health"] == "at_risk"
        )
        overdue = sum(
            1 for m in roadmap["all_milestones"] if m["health"] == "overdue"
        )

        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total Milestones:** {total_milestones}")
        lines.append(f"- **Open Milestones:** {open_milestones}")
        if at_risk > 0:
            lines.append(f"- **At Risk:** {at_risk} ⚠️")
        if overdue > 0:
            lines.append(f"- **Overdue:** {overdue} ❌")
        lines.append("")

        # Health legend
        lines.append("## Health Status Legend")
        lines.append("")
        lines.append("- ✅ **Good** - On track, progress > 80%")
        lines.append("- 🟢 **On Track** - Making good progress")
        lines.append("- 🟡 **Behind** - Needs attention (20% buffer exceeded)")
        lines.append("- 🟠 **At Risk** - Significant delay predicted (50% buffer exceeded)")
        lines.append("- ❌ **Overdue** - Past due date")
        lines.append("- ✔️ **Completed** - Milestone closed")
        lines.append("")

        # Milestones by health
        critical = [
            m for m in roadmap["all_milestones"] if m["health"] in ["overdue", "at_risk"]
        ]
        if critical:
            lines.append("## ⚠️ Critical Milestones (Need Attention)")
            lines.append("")
            for milestone in critical:
                lines.extend(self._format_milestone(milestone))
            lines.append("")

        # All milestones by repository
        lines.append("## Milestones by Repository")
        lines.append("")

        for repo_key, repo_data in roadmap["repositories"].items():
            if not repo_data["milestones"]:
                continue

            lines.append(f"### {repo_key}")
            lines.append("")
            lines.append(
                f"**Velocity:** {repo_data['velocity']['issues_per_week']:.1f} issues/week, "
                f"{repo_data['velocity']['commits_per_week']:.1f} commits/week"
            )
            lines.append("")

            for milestone in repo_data["milestones"]:
                lines.extend(self._format_milestone(milestone))

            lines.append("")

        # Timeline visualization (Mermaid Gantt)
        lines.append("## Timeline Visualization")
        lines.append("")
        lines.append("```mermaid")
        lines.append("gantt")
        lines.append("    title Project Roadmap Timeline")
        lines.append("    dateFormat YYYY-MM-DD")
        lines.append("")

        # Group by repository
        for repo_key, repo_data in roadmap["repositories"].items():
            if not repo_data["milestones"]:
                continue

            # Clean repo name for section
            section_name = repo_key.replace("/", " / ")
            lines.append(f"    section {section_name}")

            for milestone in repo_data["milestones"]:
                if milestone["due_date"]:
                    # Show progress bar
                    progress = int(milestone["progress_percentage"])
                    due_date = milestone["due_date"][:10]

                    # Determine status for Gantt
                    status = ""
                    if milestone["health"] == "completed":
                        status = "done, "
                    elif milestone["health"] in ["overdue", "at_risk"]:
                        status = "crit, "
                    elif milestone["health"] == "on_track":
                        status = "active, "

                    # Calculate start date (assume started 30 days ago or when created)
                    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

                    title = milestone["title"].replace(":", " -")[:40]
                    lines.append(
                        f"    {title} :{status}{start_date}, {due_date}"
                    )

        lines.append("```")
        lines.append("")

        return "\n".join(lines)

    def _format_milestone(self, milestone: dict[str, Any]) -> list[str]:
        """Format a single milestone for markdown output."""
        lines = []

        # Health emoji
        health_emoji = {
            "good": "✅",
            "on_track": "🟢",
            "behind": "🟡",
            "at_risk": "🟠",
            "overdue": "❌",
            "completed": "✔️",
            "no_deadline": "📋",
            "ready_to_close": "🎯",
        }.get(milestone["health"], "❓")

        lines.append(f"#### {health_emoji} {milestone['title']}")
        lines.append("")

        # Status
        lines.append(f"**Status:** {milestone['state'].title()}")

        # Progress
        lines.append(
            f"**Progress:** {milestone['completed']}/{milestone['total_issues']} issues "
            f"({milestone['progress_percentage']:.0f}%)"
        )

        # Due date and prediction
        if milestone["due_date"]:
            due_str = datetime.fromisoformat(milestone["due_date"]).strftime("%Y-%m-%d")
            lines.append(f"**Due Date:** {due_str}")

            if milestone["days_until_due"] is not None:
                if milestone["days_until_due"] > 0:
                    lines.append(f"**Days Until Due:** {milestone['days_until_due']}")
                else:
                    lines.append(f"**Days Overdue:** {abs(milestone['days_until_due'])}")

        # Prediction
        if milestone["health"] != "completed":
            pred_date = datetime.fromisoformat(milestone["predicted_completion"]).strftime(
                "%Y-%m-%d"
            )
            lines.append(
                f"**Predicted Completion:** {pred_date} "
                f"({milestone['predicted_days_remaining']} days)"
            )

            # Velocity context
            lines.append(
                f"**Current Velocity:** {milestone['velocity']['issues_per_week']:.1f} issues/week"
            )

        # Health explanation
        if milestone["health"] == "at_risk":
            lines.append(
                "**⚠️ Action Needed:** Predicted completion significantly exceeds due date"
            )
        elif milestone["health"] == "behind":
            lines.append("**⚠️ Attention:** Predicted completion may exceed due date")
        elif milestone["health"] == "overdue":
            lines.append("**❌ Overdue:** This milestone is past its due date")

        # Description
        if milestone.get("description"):
            lines.append("")
            lines.append(milestone["description"])

        lines.append("")

        return lines


def main():
    """Main entry point for roadmap generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate project roadmap from GitHub milestones"
    )
    parser.add_argument(
        "--config",
        default="config/collection/production.yaml",
        help="Path to collection config (default: production.yaml)",
    )
    parser.add_argument(
        "--velocity-days",
        type=int,
        default=30,
        help="Days to calculate velocity over (default: 30)",
    )
    parser.add_argument(
        "--output",
        help="Output file path (defaults to reports/planning/roadmap_TIMESTAMP.md)",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "both"],
        default="both",
        help="Output format (default: both)",
    )

    args = parser.parse_args()

    # Generate roadmap
    generator = RoadmapGenerator()
    try:
        roadmap = generator.generate_roadmap(args.config, args.velocity_days)
        markdown = generator.generate_markdown(roadmap)

        # Determine output path
        if args.output:
            output_path = Path(args.output)
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_path = Path("reports/planning") / f"roadmap_{timestamp}.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save markdown
        if args.format in ["markdown", "both"]:
            md_path = (
                output_path
                if args.format == "markdown"
                else output_path.with_suffix(".md")
            )
            md_path.write_text(markdown)
            print(f"\nMarkdown roadmap saved: {md_path}")

        # Save JSON
        if args.format in ["json", "both"]:
            json_path = (
                output_path if args.format == "json" else output_path.with_suffix(".json")
            )
            json_path.write_text(json.dumps(roadmap, indent=2))
            print(f"JSON roadmap saved: {json_path}")

        # Print summary
        print("\n" + "=" * 60)
        print("Roadmap Summary")
        print("=" * 60)
        print(f"Total Milestones: {len(roadmap['all_milestones'])}")

        at_risk = sum(
            1 for m in roadmap["all_milestones"] if m["health"] == "at_risk"
        )
        overdue = sum(
            1 for m in roadmap["all_milestones"] if m["health"] == "overdue"
        )

        if at_risk > 0:
            print(f"⚠️  At Risk: {at_risk}")
        if overdue > 0:
            print(f"❌ Overdue: {overdue}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
