#!/usr/bin/env python3
"""Orchestration script for running workflows."""

import argparse
import subprocess
import sys
from pathlib import Path


def list_snapshots():
    """List available data snapshots."""
    data_dir = Path("data")
    snapshots = sorted(
        [d.name for d in data_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    )
    return snapshots


def get_latest_snapshot():
    """Get the most recent snapshot."""
    snapshots = list_snapshots()
    return snapshots[-1] if snapshots else None


def run_trend_analysis(workflow: str, baseline: str, current: str):
    """Run trend analysis workflow."""
    if workflow == "compare_periods":
        cmd = [
            "uv",
            "run",
            "python",
            "workflows/trend_analysis/compare_periods.py",
            baseline,
            current,
        ]
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    else:
        print(f"Unknown trend analysis workflow: {workflow}")
        sys.exit(1)


def run_summarization(workflow: str, snapshot: str | None, model: str):
    """Run summarization workflow."""
    if workflow == "repo_comparison":
        cmd = [
            "uv",
            "run",
            "python",
            "workflows/summarization/repo_comparison.py",
            "--model",
            model,
        ]
        if snapshot:
            cmd.extend(["--snapshot", snapshot])
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    else:
        print(f"Unknown summarization workflow: {workflow}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run GitHub PM workflows")
    parser.add_argument(
        "category",
        choices=["trend_analysis", "summarization", "anomaly_detection", "custom_reports"],
        help="Workflow category",
    )
    parser.add_argument(
        "workflow",
        help="Workflow name (e.g., compare_periods)",
    )
    parser.add_argument(
        "--baseline",
        help="Baseline snapshot timestamp (required for trend analysis)",
    )
    parser.add_argument(
        "--current",
        help="Current snapshot timestamp (defaults to latest)",
    )
    parser.add_argument(
        "--list-snapshots",
        action="store_true",
        help="List available snapshots",
    )
    parser.add_argument(
        "--model",
        default="llama3.2",
        help="Ollama model to use for summarization workflows (default: llama3.2)",
    )

    args = parser.parse_args()

    # List snapshots if requested
    if args.list_snapshots:
        snapshots = list_snapshots()
        print("Available snapshots:")
        for snapshot in snapshots:
            print(f"  - {snapshot}")
        sys.exit(0)

    # Run workflow based on category
    if args.category == "trend_analysis":
        if not args.baseline:
            print("Error: --baseline is required for trend analysis")
            sys.exit(1)

        current = args.current or get_latest_snapshot()
        if not current:
            print("Error: No snapshots found in data/")
            sys.exit(1)

        print(f"Comparing {args.baseline} → {current}")
        run_trend_analysis(args.workflow, args.baseline, current)

    elif args.category == "summarization":
        snapshot = args.baseline or get_latest_snapshot()
        if not snapshot:
            print("Error: No snapshots found in data/")
            sys.exit(1)

        print(f"Analyzing snapshot: {snapshot}")
        run_summarization(args.workflow, snapshot, args.model)

    elif args.category == "anomaly_detection":
        print("Anomaly detection workflows coming soon!")
        sys.exit(1)

    elif args.category == "custom_reports":
        print("Custom report workflows coming soon!")
        sys.exit(1)


if __name__ == "__main__":
    main()
