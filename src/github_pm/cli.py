"""Command-line interface for GitHub PM."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from github_pm.data_collector import DataCollector
from github_pm.github_client import GitHubClient
from github_pm.json_exporter import JSONExporter
from github_pm.organizer import IssueOrganizer
from github_pm.report_generator import MarkdownReportGenerator


def load_config(config_path: str) -> dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config YAML file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_file) as f:
        config = yaml.safe_load(f)

    return config


def main() -> int:
    """
    Main entry point for GitHub PM CLI.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="GitHub Project Management - Aggregate issues across repositories"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config/collection/production.yaml",
        help="Path to configuration file (default: config/collection/production.yaml)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="github-issues-report.md",
        help="Output file path (default: github-issues-report.md)",
    )
    parser.add_argument(
        "--group-by",
        choices=["repository", "labels", "milestone", "assignee"],
        default="repository",
        help="How to group issues in the report (default: repository)",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "both"],
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "--save-snapshot",
        action="store_true",
        help="Save timestamped snapshot to data/ directory",
    )
    parser.add_argument(
        "--label",
        default="snapshot",
        help="Snapshot label (e.g., 'sod', 'eod', 'snapshot'). Used with --save-snapshot.",
    )

    args = parser.parse_args()

    try:
        # Load configuration
        print(f"Loading configuration from {args.config}...")
        config = load_config(args.config)

        # Initialize clients
        github_client = GitHubClient()
        organizer = IssueOrganizer()
        report_generator = MarkdownReportGenerator()
        json_exporter = JSONExporter()
        data_collector = DataCollector()

        # Fetch issues from all repositories
        all_issues = []
        repositories = config.get("repositories", [])
        issue_state = config.get("issue_state", "open")
        limit = config.get("limit", 100)

        print(f"\nFetching issues from {len(repositories)} repositories...")
        for repo in repositories:
            owner = repo.get("owner")
            name = repo.get("name")

            if not owner or not name:
                print(f"Warning: Skipping invalid repository config: {repo}")
                continue

            print(f"  - {owner}/{name}")
            try:
                issues = github_client.fetch_issues(
                    owner=owner,
                    repo=name,
                    state=issue_state,
                    limit=limit,
                )
                # Add repository identifier to each issue
                for issue in issues:
                    issue["repository"] = f"{owner}/{name}"
                all_issues.extend(issues)
            except Exception as e:
                print(f"    Error fetching issues: {e}")
                continue

        print(f"\nTotal issues fetched: {len(all_issues)}")

        # Organize issues
        print(f"Organizing issues by {args.group_by}...")
        if args.group_by == "repository":
            organized_issues = organizer.organize_by_repository(all_issues)
        elif args.group_by == "labels":
            organized_issues = organizer.organize_by_labels(all_issues)
        elif args.group_by == "milestone":
            organized_issues = organizer.organize_by_milestone(all_issues)
        elif args.group_by == "assignee":
            organized_issues = organizer.organize_by_assignee(all_issues)
        else:
            organized_issues = organizer.organize_by_repository(all_issues)

        # Save timestamped snapshot if requested
        if args.save_snapshot:
            print(f"Saving {args.label.upper()} snapshot...")
            # Create comprehensive organized data structure
            organized_data = {
                "by_repository": organizer.organize_by_repository(all_issues),
                "by_labels": organizer.organize_by_labels(all_issues),
                "by_milestone": organizer.organize_by_milestone(all_issues),
                "by_assignee": organizer.organize_by_assignee(all_issues),
            }
            snapshot_path = data_collector.create_snapshot(
                all_issues, organized_data, config, label=args.label
            )
            print(f"  Snapshot saved: {snapshot_path}")

        # Generate and save outputs based on format
        output_path = Path(args.output)

        # Generate markdown report if requested
        if args.format in ["markdown", "both"]:
            print(f"Generating markdown report...")
            report = report_generator.generate_report(
                organized_issues, group_by=args.group_by
            )

            # Determine markdown output path
            md_path = output_path if args.format == "markdown" else output_path.with_suffix(".md")
            md_path.write_text(report)
            print(f"  Markdown report: {md_path}")

        # Generate JSON export if requested
        if args.format in ["json", "both"]:
            print(f"Generating JSON export...")

            # Create comprehensive organized data structure
            organized_data = {
                "by_repository": organizer.organize_by_repository(all_issues),
                "by_labels": organizer.organize_by_labels(all_issues),
                "by_milestone": organizer.organize_by_milestone(all_issues),
                "by_assignee": organizer.organize_by_assignee(all_issues),
            }

            json_data = json_exporter.export(all_issues, organized=organized_data)

            # Determine JSON output path
            json_path = output_path if args.format == "json" else output_path.with_suffix(".json")
            json_path.write_text(json.dumps(json_data, indent=2))
            print(f"  JSON export: {json_path}")

        print(f"\nReports generated successfully!")
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except yaml.YAMLError as e:
        print(f"Error parsing config file: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
