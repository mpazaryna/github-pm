#!/usr/bin/env python3
"""
Sync repositories from GitHub using gh CLI and apply filters.

Dynamically discovers repositories and generates/updates collection config
based on filter preferences in config/collection/repo_filters.yaml.

Usage:
    # Generate config from GitHub
    python scripts/sync_repos.py

    # Preview without writing
    python scripts/sync_repos.py --dry-run

    # Write to specific output file
    python scripts/sync_repos.py --output config/collection/auto-generated.yaml

    # Show stats only
    python scripts/sync_repos.py --stats
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


class RepoSyncer:
    """Sync repositories from GitHub with filtering."""

    def __init__(self, filters_path: Path):
        """Initialize syncer with filter config."""
        self.filters_path = filters_path
        self.filters = self._load_filters()

    def _load_filters(self) -> dict:
        """Load filter configuration."""
        if not self.filters_path.exists():
            print(f"Error: {self.filters_path} not found", file=sys.stderr)
            sys.exit(1)

        with open(self.filters_path) as f:
            return yaml.safe_load(f)

    def _run_gh_command(self, cmd: list[str]) -> dict:
        """Run gh CLI command and return JSON output."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error running gh command: {e}", file=sys.stderr)
            print(f"Command: {' '.join(cmd)}", file=sys.stderr)
            print(f"Output: {e.stdout}", file=sys.stderr)
            print(f"Error: {e.stderr}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error parsing gh output as JSON: {e}", file=sys.stderr)
            sys.exit(1)

    def fetch_repos(self, owner: str) -> list[dict]:
        """Fetch all repositories for an owner using gh CLI."""
        print(f"Fetching repositories for {owner}...", file=sys.stderr)

        cmd = [
            "gh",
            "repo",
            "list",
            owner,
            "--json",
            "name,owner,isFork,isArchived,visibility,repositoryTopics,primaryLanguage,pushedAt,createdAt",
            "--limit",
            "1000",
        ]

        repos = self._run_gh_command(cmd)
        print(f"  Found {len(repos)} repositories", file=sys.stderr)
        return repos

    def _matches_topics_filter(
        self, repo_topics: list[dict] | None, include: list[str], exclude: list[str]
    ) -> bool:
        """Check if repo matches topic filters."""
        # Extract topic names
        topics = [t["name"] for t in repo_topics] if repo_topics else []

        # Check exclusions first
        if exclude and any(topic in topics for topic in exclude):
            return False

        # Check inclusions (empty = all allowed)
        if include and not any(topic in topics for topic in include):
            return False

        return True

    def _matches_language_filter(
        self, language: str | None, include: list[str], exclude: list[str]
    ) -> bool:
        """Check if repo matches language filters."""
        if not language:
            # No language set - include if no include filter, exclude if in exclude list
            return len(include) == 0

        # Check exclusions first
        if exclude and language in exclude:
            return False

        # Check inclusions (empty = all allowed)
        if include and language not in include:
            return False

        return True

    def _matches_age_filter(
        self, pushed_at: str, created_at: str, min_days: int, max_age_days: int
    ) -> bool:
        """Check if repo matches age filters."""
        now = datetime.now(timezone.utc)

        # Check last update
        if min_days > 0:
            pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            days_since_update = (now - pushed).days
            if days_since_update > min_days:
                return False

        # Check repo age
        if max_age_days > 0:
            created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            repo_age_days = (now - created).days
            if repo_age_days > max_age_days:
                return False

        return True

    def _is_force_included(self, owner: str, name: str) -> bool:
        """Check if repo is in force_include list."""
        force_include = self.filters.get("overrides", {}).get("force_include", [])
        return any(
            r.get("owner") == owner and r.get("name") == name for r in force_include
        )

    def _is_force_excluded(self, owner: str, name: str) -> bool:
        """Check if repo is in force_exclude list."""
        force_exclude = self.filters.get("overrides", {}).get("force_exclude", [])
        return any(
            r.get("owner") == owner and r.get("name") == name for r in force_exclude
        )

    def filter_repos(self, repos: list[dict]) -> tuple[list[dict], dict]:
        """
        Filter repositories based on filter config.

        Returns:
            Tuple of (filtered_repos, stats)
        """
        filters = self.filters.get("filters", {})

        filtered = []
        stats = {
            "total": len(repos),
            "filtered": 0,
            "excluded_fork": 0,
            "excluded_archived": 0,
            "excluded_visibility": 0,
            "excluded_topics": 0,
            "excluded_language": 0,
            "excluded_age": 0,
            "force_included": 0,
            "force_excluded": 0,
        }

        for repo in repos:
            owner = repo["owner"]["login"]
            name = repo["name"]

            # Check force exclude first
            if self._is_force_excluded(owner, name):
                stats["force_excluded"] += 1
                continue

            # Check force include (skip all other filters)
            if self._is_force_included(owner, name):
                filtered.append(repo)
                stats["force_included"] += 1
                continue

            # Apply filters
            if filters.get("exclude_forks", True) and repo["isFork"]:
                stats["excluded_fork"] += 1
                continue

            if filters.get("exclude_archived", True) and repo["isArchived"]:
                stats["excluded_archived"] += 1
                continue

            visibility_filter = filters.get("visibility", [])
            # Empty list means include all visibility levels
            if visibility_filter and repo["visibility"].lower() not in [v.lower() for v in visibility_filter]:
                stats["excluded_visibility"] += 1
                continue

            topics = repo.get("repositoryTopics", [])
            include_topics = filters.get("include_topics", [])
            exclude_topics = filters.get("exclude_topics", [])
            if not self._matches_topics_filter(topics, include_topics, exclude_topics):
                stats["excluded_topics"] += 1
                continue

            language = (
                repo.get("primaryLanguage", {}).get("name")
                if repo.get("primaryLanguage")
                else None
            )
            include_languages = filters.get("include_languages", [])
            exclude_languages = filters.get("exclude_languages", [])
            if not self._matches_language_filter(
                language, include_languages, exclude_languages
            ):
                stats["excluded_language"] += 1
                continue

            min_days = filters.get("min_days_since_update", 0)
            max_age = filters.get("max_age_days", 0)
            if not self._matches_age_filter(
                repo["pushedAt"], repo["createdAt"], min_days, max_age
            ):
                stats["excluded_age"] += 1
                continue

            # Passed all filters
            filtered.append(repo)

        stats["filtered"] = len(filtered)
        return filtered, stats

    def generate_config(self, repos: list[dict]) -> dict:
        """Generate collection config from filtered repos."""
        collection = self.filters.get("collection", {})

        config = {
            "_generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "repositories": [
                {"owner": repo["owner"]["login"], "name": repo["name"]} for repo in repos
            ],
            "issue_state": collection.get("issue_state", "open"),
            "labels": collection.get("labels", []),
            "limit": collection.get("limit", 100),
        }

        return config

    def sync(self) -> tuple[dict, dict]:
        """
        Sync repositories from GitHub.

        Returns:
            Tuple of (config, stats)
        """
        all_repos = []
        all_stats = {
            "owners": [],
            "total_repos": 0,
            "filtered_repos": 0,
        }

        # Fetch from primary owner
        owner = self.filters.get("owner")
        if not owner:
            print("Error: 'owner' not specified in filters", file=sys.stderr)
            sys.exit(1)

        repos = self.fetch_repos(owner)
        all_repos.extend(repos)
        all_stats["owners"].append(owner)

        # Fetch from additional owners
        additional_owners = self.filters.get("additional_owners", [])
        for add_owner in additional_owners:
            repos = self.fetch_repos(add_owner)
            all_repos.extend(repos)
            all_stats["owners"].append(add_owner)

        # Filter repos
        filtered_repos, filter_stats = self.filter_repos(all_repos)

        # Update stats
        all_stats["total_repos"] = filter_stats["total"]
        all_stats["filtered_repos"] = filter_stats["filtered"]
        all_stats.update(filter_stats)

        # Generate config
        config = self.generate_config(filtered_repos)

        return config, all_stats


def print_stats(stats: dict):
    """Print sync statistics."""
    print()
    print("=" * 60)
    print("Repository Sync Statistics")
    print("=" * 60)
    print(f"Owners scanned: {', '.join(stats['owners'])}")
    print(f"Total repositories: {stats['total_repos']}")
    print(f"After filtering: {stats['filtered_repos']}")
    print()
    print("Exclusions:")
    print(f"  - Forks: {stats['excluded_fork']}")
    print(f"  - Archived: {stats['excluded_archived']}")
    print(f"  - Visibility: {stats['excluded_visibility']}")
    print(f"  - Topics: {stats['excluded_topics']}")
    print(f"  - Language: {stats['excluded_language']}")
    print(f"  - Age: {stats['excluded_age']}")
    print()
    print("Overrides:")
    print(f"  - Force included: {stats['force_included']}")
    print(f"  - Force excluded: {stats['force_excluded']}")
    print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sync repositories from GitHub using gh CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate config from GitHub
  uv run python scripts/sync_repos.py

  # Preview without writing
  uv run python scripts/sync_repos.py --dry-run

  # Write to custom output
  uv run python scripts/sync_repos.py --output config/collection/custom.yaml

  # Show stats only
  uv run python scripts/sync_repos.py --stats

  # Use custom filter config
  uv run python scripts/sync_repos.py --filters config/collection/my-filters.yaml
        """,
    )

    parser.add_argument(
        "--filters",
        type=Path,
        default=Path("config/collection/repo_filters.yaml"),
        help="Path to filter config (default: config/collection/repo_filters.yaml)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("config/collection/production.yaml"),
        help="Output file (default: config/collection/production.yaml)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview config without writing",
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics only (no config generation)",
    )

    args = parser.parse_args()

    # Sync repos
    syncer = RepoSyncer(args.filters)
    config, stats = syncer.sync()

    # Print stats
    print_stats(stats)

    # Stats only mode
    if args.stats:
        sys.exit(0)

    # Print config in dry-run mode
    if args.dry_run:
        print()
        print("Generated config (DRY RUN - not written):")
        print("-" * 60)
        # Remove internal keys for yaml dump
        clean_config = {k: v for k, v in config.items() if not k.startswith("_")}
        print(yaml.dump(clean_config, default_flow_style=False, sort_keys=False))
        sys.exit(0)

    # Write config
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with open(args.output, "w") as f:
        # Write comments manually
        f.write("# Auto-generated by scripts/sync_repos.py\n")
        f.write("# DO NOT EDIT - Run 'uv run python scripts/sync_repos.py' to regenerate\n")
        f.write("# Edit config/collection/repo_filters.yaml to change filtering\n")
        f.write(f"# Generated: {config['_generated']}\n\n")

        # Write yaml (without internal keys)
        clean_config = {k: v for k, v in config.items() if not k.startswith("_")}
        yaml.dump(clean_config, f, default_flow_style=False, sort_keys=False)

    print()
    print(f"✅ Config written to: {args.output}")
    print(f"   Repositories: {stats['filtered_repos']}")
    print()


if __name__ == "__main__":
    main()
