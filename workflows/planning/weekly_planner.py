"""AI-powered weekly planning workflow."""

import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

from github_pm.commit_analyzer import CommitAnalyzer
from github_pm.status_analyzer import StatusAnalyzer


class WeeklyPlanner:
    """AI-powered weekly planning assistant."""

    def __init__(self, model: str = "llama3.2"):
        """
        Initialize weekly planner.

        Args:
            model: Ollama model name
        """
        self.model_name = model
        try:
            self.llm = OllamaLLM(model=model)
        except Exception as e:
            raise RuntimeError(
                f"Failed to connect to Ollama. Error: {e}"
            )
        self.analyzer = CommitAnalyzer()
        self.status_analyzer = StatusAnalyzer()

    def analyze_last_week(
        self, repos: list[dict[str, str]], days: int = 7
    ) -> dict[str, Any]:
        """
        Analyze work distribution from last week's commits.

        Args:
            repos: List of {'owner': ..., 'repo': ...} dicts
            days: Number of days to look back

        Returns:
            Analysis of work distribution
        """
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        until = datetime.now().strftime("%Y-%m-%d")

        repo_analyses = {}
        total_commits = 0

        print(f"Analyzing last {days} days ({since} to {until})...")
        print()

        for repo in repos:
            owner = repo["owner"]
            repo_name = repo["repo"]
            repo_key = f"{owner}/{repo_name}"

            print(f"  Fetching commits from {repo_key}...")
            try:
                commits = self.analyzer.fetch_commits(
                    owner, repo_name, since, until, limit=200
                )
                analysis = self.analyzer.analyze_commits(commits)

                repo_analyses[repo_key] = {
                    "commits": len(commits),
                    "types": analysis["commit_types"],
                    "authors": analysis["authors"],
                    "conventional_percentage": analysis["conventional_percentage"],
                }
                total_commits += len(commits)
            except Exception as e:
                print(f"    Warning: {e}")
                repo_analyses[repo_key] = {
                    "commits": 0,
                    "types": {},
                    "authors": {},
                    "conventional_percentage": 0,
                }

        # Calculate percentages
        for repo_key, data in repo_analyses.items():
            data["percentage"] = (
                (data["commits"] / total_commits * 100) if total_commits > 0 else 0
            )

        return {
            "period": {"since": since, "until": until, "days": days},
            "total_commits": total_commits,
            "by_repository": repo_analyses,
        }

    def analyze_current_backlog(
        self, snapshot_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Analyze current issue backlog from snapshot with status and milestone tracking.

        Args:
            snapshot_data: Issue snapshot data

        Returns:
            Comprehensive backlog analysis by repository
        """
        organized = snapshot_data.get("organized", {})
        by_repo = organized.get("by_repository", {})
        all_issues = snapshot_data.get("issues", [])

        backlog = {}
        for repo_name, issues in by_repo.items():
            open_issues = [i for i in issues if i.get("state") == "OPEN"]

            # Status distribution analysis
            status_dist = self.status_analyzer.analyze_status_distribution(open_issues)
            flow_health = self.status_analyzer.analyze_flow_health(status_dist)

            # Milestone analysis for this repo
            repo_issues_all = [i for i in all_issues if i.get("repository") == repo_name]
            milestones = self.status_analyzer.analyze_milestone_progress(repo_issues_all)

            # Get priority issues by status
            ready_issues = self.status_analyzer.get_priority_issues_by_status(
                open_issues, "ready", limit=5
            )
            in_progress_issues = self.status_analyzer.get_priority_issues_by_status(
                open_issues, "in_progress", limit=5
            )

            # Get unassigned issues
            unassigned = [i for i in open_issues if not i.get("assignees")]

            backlog[repo_name] = {
                "total_open": len(open_issues),
                "status_distribution": status_dist["counts"],
                "flow_health": flow_health,
                "milestones": milestones,
                "unassigned_count": len(unassigned),
                "ready_to_work": [
                    {
                        "number": i.get("number"),
                        "title": i.get("title"),
                        "milestone": i.get("milestone", {}).get("title") if i.get("milestone") else None,
                    }
                    for i in ready_issues
                ],
                "currently_in_progress": [
                    {
                        "number": i.get("number"),
                        "title": i.get("title"),
                        "milestone": i.get("milestone", {}).get("title") if i.get("milestone") else None,
                    }
                    for i in in_progress_issues
                ],
            }

        return backlog

    def generate_plan(
        self,
        last_week_analysis: dict[str, Any],
        backlog_analysis: dict[str, Any],
    ) -> str:
        """
        Generate AI-powered weekly plan.

        Args:
            last_week_analysis: Work distribution from last week
            backlog_analysis: Current backlog state

        Returns:
            Natural language weekly plan
        """
        # Create prompt
        prompt_template = PromptTemplate(
            input_variables=["last_week", "backlog"],
            template="""You are an engineering manager's AI planning assistant. Analyze last week's work distribution and the current backlog (with status and milestone tracking) to suggest a balanced plan for next week.

LAST WEEK'S WORK DISTRIBUTION:
{last_week}

CURRENT BACKLOG (with Status & Milestones):
{backlog}

Please provide:

1. **Work Distribution Analysis**
   - Which repositories got attention last week
   - Which repositories were neglected
   - Any concerning imbalances

2. **Status Flow Analysis**
   - Comment on the Ready → In Progress → In Review flow
   - Identify any bottlenecks (too many Ready but not In Progress, etc.)
   - WIP (Work In Progress) health

3. **Milestone Progress Review**
   - Which milestones are at risk
   - Which need more focus
   - Timeline concerns

4. **Recommended Distribution for Next Week**
   - Suggested percentage allocation across repositories
   - Consider both neglected repos AND milestone deadlines
   - Rationale for the rebalancing

5. **Priority Issues to Address**
   - Specific issue recommendations per repository
   - Prioritize "Ready" issues and milestone-critical work
   - Why these issues should be prioritized

6. **Strategic Recommendations**
   - Any patterns or concerns
   - Suggestions for maintaining balance AND hitting milestones
   - Process improvements (grooming, WIP limits, etc.)

Keep your response actionable, specific, and focused on helping the team balance concurrent work streams while hitting milestone deadlines. Use markdown formatting.
""",
        )

        # Format last week data
        last_week_str = f"""
Period: {last_week_analysis['period']['since']} to {last_week_analysis['period']['until']} ({last_week_analysis['period']['days']} days)
Total Commits: {last_week_analysis['total_commits']}

Repository Distribution:
"""
        for repo, data in last_week_analysis["by_repository"].items():
            last_week_str += f"\n- **{repo}**: {data['commits']} commits ({data['percentage']:.1f}%)"
            if data["types"]:
                types_str = ", ".join(
                    [f"{t}: {c}" for t, c in list(data["types"].items())[:3]]
                )
                last_week_str += f"\n  - Types: {types_str}"

        # Format backlog data with status and milestones
        backlog_str = "\nCurrent Backlog:\n"
        for repo, data in backlog_analysis.items():
            backlog_str += f"\n- **{repo}**:"
            backlog_str += f"\n  - Total Open: {data['total_open']}"

            # Status distribution
            status = data.get("status_distribution", {})
            backlog_str += f"\n  - Status Breakdown:"
            backlog_str += f"\n    - Backlog: {status.get('backlog', 0)}"
            backlog_str += f"\n    - Ready: {status.get('ready', 0)}"
            backlog_str += f"\n    - In Progress: {status.get('in_progress', 0)}"
            backlog_str += f"\n    - In Review: {status.get('in_review', 0)}"

            # Flow health
            flow = data.get("flow_health", {})
            if flow.get("bottlenecks"):
                backlog_str += "\n  - ⚠️ Bottlenecks:"
                for bottleneck in flow["bottlenecks"]:
                    backlog_str += f"\n    - {bottleneck['message']}"

            # Milestones
            milestones = data.get("milestones", {})
            active_milestones = {k: v for k, v in milestones.items()
                               if k != "No Milestone" and v.get("total", 0) > 0}
            if active_milestones:
                backlog_str += "\n  - Milestones:"
                for ms_name, ms_data in list(active_milestones.items())[:3]:
                    progress = ms_data.get("progress_pct", 0)
                    health = ms_data.get("health", "unknown")
                    backlog_str += f"\n    - {ms_name}: {progress}% ({ms_data['done']}/{ms_data['total']}) - {health}"

            # Ready to work issues
            if data.get("ready_to_work"):
                backlog_str += "\n  - Ready to Work (Top 3):"
                for issue in data["ready_to_work"][:3]:
                    ms = f" [{issue['milestone']}]" if issue['milestone'] else ""
                    backlog_str += f"\n    - #{issue['number']}: {issue['title']}{ms}"

        # Generate plan
        prompt = prompt_template.format(
            last_week=last_week_str, backlog=backlog_str
        )

        print("Generating AI-powered weekly plan...")
        print(f"Using model: {self.model_name}")
        print()

        try:
            response = self.llm.invoke(prompt)
            return response
        except Exception as e:
            return f"Error generating plan: {e}"

    def create_weekly_plan(
        self,
        repos: list[dict[str, str]],
        snapshot_data: dict[str, Any],
        output_path: Path,
        lookback_days: int = 7,
    ) -> None:
        """
        Create complete weekly plan.

        Args:
            repos: List of repositories to analyze
            snapshot_data: Issue snapshot data
            output_path: Path to save the plan
            lookback_days: Days to look back for commit analysis
        """
        # Analyze last week
        last_week = self.analyze_last_week(repos, lookback_days)

        # Analyze backlog
        backlog = self.analyze_current_backlog(snapshot_data)

        # Generate AI plan
        ai_plan = self.generate_plan(last_week, backlog)

        # Create report
        lines = []
        lines.append("# Weekly Planning Report")
        lines.append("")
        lines.append(
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        lines.append(f"**AI Model:** {self.model_name}")
        lines.append(
            f"**Analysis Period:** {last_week['period']['since']} to {last_week['period']['until']}"
        )
        lines.append("")

        # Last week summary
        lines.append("## Last Week's Delivery")
        lines.append("")
        lines.append(f"**Total Commits:** {last_week['total_commits']}")
        lines.append("")
        lines.append("| Repository | Commits | Percentage |")
        lines.append("|------------|---------|------------|")
        for repo, data in last_week["by_repository"].items():
            lines.append(
                f"| {repo} | {data['commits']} | {data['percentage']:.1f}% |"
            )
        lines.append("")

        # Backlog summary with status
        lines.append("## Current Backlog")
        lines.append("")
        lines.append("| Repository | Open | Backlog | Ready | In Progress | In Review |")
        lines.append("|------------|------|---------|-------|-------------|-----------|")
        for repo, data in backlog.items():
            status = data.get("status_distribution", {})
            lines.append(
                f"| {repo} | {data['total_open']} | "
                f"{status.get('backlog', 0)} | {status.get('ready', 0)} | "
                f"{status.get('in_progress', 0)} | {status.get('in_review', 0)} |"
            )
        lines.append("")

        # Flow health warnings
        lines.append("## Flow Health")
        lines.append("")
        has_bottlenecks = False
        for repo, data in backlog.items():
            flow = data.get("flow_health", {})
            if flow.get("bottlenecks"):
                has_bottlenecks = True
                lines.append(f"### {repo}")
                for bottleneck in flow["bottlenecks"]:
                    severity = "⚠️" if bottleneck["severity"] == "high" else "ℹ️"
                    lines.append(f"{severity} **{bottleneck['type']}**: {bottleneck['message']}")
                if flow.get("recommendations"):
                    lines.append("\n**Recommendations:**")
                    for rec in flow["recommendations"]:
                        lines.append(f"- {rec}")
                lines.append("")

        if not has_bottlenecks:
            lines.append("✅ No major bottlenecks detected - flow looks healthy!")
            lines.append("")

        # Milestone progress
        lines.append("## Milestone Progress")
        lines.append("")
        has_milestones = False
        for repo, data in backlog.items():
            milestones = data.get("milestones", {})
            active_milestones = {
                k: v for k, v in milestones.items()
                if k != "No Milestone" and v.get("total", 0) > 0
            }
            if active_milestones:
                has_milestones = True
                lines.append(f"### {repo}")
                lines.append("")
                for ms_name, ms_data in active_milestones.items():
                    health = ms_data.get("health", "unknown")
                    progress = ms_data.get("progress_pct", 0)
                    done = ms_data.get("done", 0)
                    total = ms_data.get("total", 0)

                    # Health indicator
                    if health == "overdue":
                        indicator = "🚨"
                    elif health == "at_risk":
                        indicator = "⚠️"
                    elif health == "behind":
                        indicator = "⚡"
                    elif health == "on_track":
                        indicator = "✅"
                    else:
                        indicator = "📊"

                    lines.append(f"{indicator} **{ms_name}**")
                    lines.append(f"- Progress: {progress}% ({done}/{total} issues)")

                    if ms_data.get("due_date"):
                        lines.append(f"- Due: {ms_data['due_date']} ({ms_data.get('days_remaining', 0)} days)")
                        if ms_data.get("needed_velocity"):
                            lines.append(f"- Needed velocity: {ms_data['needed_velocity']} issues/week")

                    lines.append(f"- Status: {health}")
                    lines.append("")

        if not has_milestones:
            lines.append("No active milestones with deadlines")
            lines.append("")

        # Ready to work issues
        lines.append("## Ready to Work")
        lines.append("")
        for repo, data in backlog.items():
            if data.get("ready_to_work"):
                lines.append(f"### {repo}")
                for issue in data["ready_to_work"]:
                    ms_tag = f" `{issue['milestone']}`" if issue['milestone'] else ""
                    lines.append(f"- #{issue['number']}: {issue['title']}{ms_tag}")
                lines.append("")
        lines.append("")

        # AI-generated plan
        lines.append("## AI-Powered Weekly Plan")
        lines.append("")
        lines.append(ai_plan)
        lines.append("")

        # Save also as JSON
        json_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "model": self.model_name,
            },
            "last_week": last_week,
            "backlog": backlog,
            "ai_plan": ai_plan,
        }

        report = "\n".join(lines)
        output_path.write_text(report)

        json_path = output_path.with_suffix(".json")
        json_path.write_text(json.dumps(json_data, indent=2))

        print(f"Markdown plan saved: {output_path}")
        print(f"JSON data saved: {json_path}")


def main():
    """Main entry point for weekly planner."""
    import argparse
    import yaml

    parser = argparse.ArgumentParser(
        description="Generate AI-powered weekly plan"
    )
    parser.add_argument(
        "--config",
        default="config/collection/production.yaml",
        help="Configuration file with repositories",
    )
    parser.add_argument(
        "--model",
        default="llama3.2",
        help="Ollama model to use (default: llama3.2)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Days to look back for commit analysis (default: 7)",
    )
    parser.add_argument(
        "--output",
        help="Output file path (defaults to reports/weekly/plan_TIMESTAMP.md)",
    )

    args = parser.parse_args()

    # Load config
    with open(args.config) as f:
        config = yaml.safe_load(f)

    repos = [
        {"owner": r["owner"], "repo": r["name"]}
        for r in config.get("repositories", [])
    ]

    if not repos:
        print("Error: No repositories found in config")
        sys.exit(1)

    # Load latest snapshot
    latest_snapshot = Path("data/latest")
    if not latest_snapshot.exists():
        print("Error: No issue snapshot found. Run ./scripts/collect.sh first")
        sys.exit(1)

    raw_path = latest_snapshot / "raw.json"
    with open(raw_path) as f:
        snapshot_data = json.load(f)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_path = Path("reports/weekly") / f"plan_{timestamp}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate plan
    try:
        planner = WeeklyPlanner(model=args.model)
        planner.create_weekly_plan(repos, snapshot_data, output_path, args.days)
        print("\nWeekly plan generated successfully!")
    except RuntimeError as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
