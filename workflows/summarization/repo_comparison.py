"""Repository comparison workflow using LangChain + Ollama."""

import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate


class RepoComparator:
    """Compares repositories using LLM analysis."""

    def __init__(self, model: str = "llama3.2"):
        """
        Initialize repository comparator.

        Args:
            model: Ollama model name (default: llama3.2)
        """
        self.model_name = model
        try:
            self.llm = OllamaLLM(model=model)
        except Exception as e:
            raise RuntimeError(
                f"Failed to connect to Ollama. Make sure Ollama is running and "
                f"the model '{model}' is available. Error: {e}"
            )

    def analyze_snapshot(self, snapshot_data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze a snapshot and extract repository comparisons.

        Args:
            snapshot_data: Complete snapshot data

        Returns:
            Dictionary with analysis results
        """
        issues = snapshot_data.get("issues", [])
        summary = snapshot_data.get("summary", {})
        organized = snapshot_data.get("organized", {})

        # Extract repository data
        repo_data = {}
        by_repo = organized.get("by_repository", {})

        for repo_name, repo_issues in by_repo.items():
            # Get label distribution
            label_counter = Counter()
            for issue in repo_issues:
                labels = issue.get("labels", [])
                for label in labels:
                    label_counter[label.get("name", "unknown")] += 1

            # Get assignee distribution
            assignee_counter = Counter()
            for issue in repo_issues:
                assignees = issue.get("assignees", [])
                if not assignees:
                    assignee_counter["Unassigned"] += 1
                else:
                    for assignee in assignees:
                        assignee_counter[assignee.get("login", "unknown")] += 1

            # Get milestone distribution
            milestone_counter = Counter()
            for issue in repo_issues:
                milestone = issue.get("milestone")
                if milestone:
                    milestone_counter[milestone.get("title", "unknown")] += 1
                else:
                    milestone_counter["No Milestone"] += 1

            # Sample issue titles
            sample_titles = [issue.get("title", "") for issue in repo_issues[:10]]

            repo_data[repo_name] = {
                "total_issues": len(repo_issues),
                "top_labels": dict(label_counter.most_common(5)),
                "assignees": dict(assignee_counter.most_common(5)),
                "milestones": dict(milestone_counter.most_common(3)),
                "sample_titles": sample_titles,
            }

        return {
            "metadata": snapshot_data.get("metadata", {}),
            "total_issues": summary.get("total_issues", 0),
            "repositories": repo_data,
        }

    def generate_comparison_report(self, analysis: dict[str, Any]) -> str:
        """
        Generate a natural language comparison report using LLM.

        Args:
            analysis: Analysis results from analyze_snapshot

        Returns:
            Natural language report
        """
        # Create prompt
        prompt_template = PromptTemplate(
            input_variables=["total_issues", "repo_summaries"],
            template="""You are analyzing GitHub issues across multiple repositories.
Provide a concise, insightful comparison of these repositories based on their issues.

Total Issues: {total_issues}

Repository Data:
{repo_summaries}

Please provide:
1. A brief overview of each repository based on its issues
2. Key differences between the repositories
3. Notable patterns or themes in each repository
4. Any insights about workload distribution or focus areas

Keep your response clear, concise, and focused on actionable insights. Use markdown formatting.
""",
        )

        # Format repository summaries
        repo_summaries = []
        for repo_name, data in analysis["repositories"].items():
            summary = f"""
**{repo_name}**
- Total Issues: {data['total_issues']}
- Top Labels: {', '.join([f"{k} ({v})" for k, v in data['top_labels'].items()])}
- Assignees: {', '.join([f"{k} ({v})" for k, v in data['assignees'].items()])}
- Milestones: {', '.join([f"{k} ({v})" for k, v in data['milestones'].items()])}
- Sample Issue Titles:
{chr(10).join([f"  - {title}" for title in data['sample_titles'][:5]])}
"""
            repo_summaries.append(summary)

        # Generate analysis
        prompt = prompt_template.format(
            total_issues=analysis["total_issues"],
            repo_summaries="\n".join(repo_summaries),
        )

        print("Generating AI analysis with Ollama...")
        print(f"Using model: {self.model_name}")
        print()

        try:
            response = self.llm.invoke(prompt)
            return response
        except Exception as e:
            return f"Error generating analysis: {e}\n\nPlease ensure Ollama is running with model '{self.model_name}'."

    def create_report(
        self, snapshot_data: dict[str, Any], output_path: Path
    ) -> None:
        """
        Create a complete comparison report.

        Args:
            snapshot_data: Complete snapshot data
            output_path: Path to save the report
        """
        # Analyze snapshot
        analysis = self.analyze_snapshot(snapshot_data)

        # Generate LLM analysis
        llm_analysis = self.generate_comparison_report(analysis)

        # Create report
        lines = []
        lines.append("# Repository Comparison Report")
        lines.append("")
        lines.append(
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        lines.append(f"**AI Model:** {self.model_name}")
        lines.append(
            f"**Data Snapshot:** {analysis['metadata'].get('collected_at', 'Unknown')}"
        )
        lines.append("")

        # Add statistics section
        lines.append("## Summary Statistics")
        lines.append("")
        lines.append(f"**Total Issues:** {analysis['total_issues']}")
        lines.append("")
        lines.append("| Repository | Issues | Top Labels |")
        lines.append("|------------|--------|------------|")
        for repo_name, data in analysis["repositories"].items():
            top_labels = ", ".join(list(data["top_labels"].keys())[:3])
            lines.append(f"| {repo_name} | {data['total_issues']} | {top_labels} |")
        lines.append("")

        # Add LLM analysis
        lines.append("## AI-Powered Analysis")
        lines.append("")
        lines.append(llm_analysis)
        lines.append("")

        # Add detailed breakdown
        lines.append("## Detailed Repository Breakdown")
        lines.append("")
        for repo_name, data in analysis["repositories"].items():
            lines.append(f"### {repo_name}")
            lines.append("")
            lines.append(f"**Total Issues:** {data['total_issues']}")
            lines.append("")

            if data["top_labels"]:
                lines.append("**Top Labels:**")
                for label, count in data["top_labels"].items():
                    lines.append(f"- {label}: {count}")
                lines.append("")

            if data["assignees"]:
                lines.append("**Assignees:**")
                for assignee, count in data["assignees"].items():
                    lines.append(f"- {assignee}: {count}")
                lines.append("")

            if data["milestones"]:
                lines.append("**Milestones:**")
                for milestone, count in data["milestones"].items():
                    lines.append(f"- {milestone}: {count}")
                lines.append("")

        report = "\n".join(lines)
        output_path.write_text(report)


def main():
    """Main entry point for repository comparison."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate AI-powered repository comparison"
    )
    parser.add_argument(
        "--snapshot",
        help="Snapshot timestamp (defaults to latest)",
    )
    parser.add_argument(
        "--model",
        default="llama3.2",
        help="Ollama model to use (default: llama3.2)",
    )
    parser.add_argument(
        "--output",
        help="Output file path (defaults to reports/daily/repo_comparison_TIMESTAMP.md)",
    )

    args = parser.parse_args()

    # Determine snapshot path
    if args.snapshot:
        snapshot_path = Path("data") / args.snapshot
    else:
        latest_link = Path("data") / "latest"
        if latest_link.exists():
            snapshot_path = latest_link.resolve()
        else:
            print("Error: No snapshots found in data/")
            sys.exit(1)

    # Load snapshot
    print(f"Loading snapshot: {snapshot_path}")
    raw_path = snapshot_path / "raw.json"
    if not raw_path.exists():
        print(f"Error: Snapshot not found at {snapshot_path}")
        sys.exit(1)

    with open(raw_path) as f:
        snapshot_data = json.load(f)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_path = Path("reports/daily") / f"repo_comparison_{timestamp}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate report
    try:
        comparator = RepoComparator(model=args.model)
        comparator.create_report(snapshot_data, output_path)
        print(f"\nReport saved: {output_path}")
    except RuntimeError as e:
        print(f"\nError: {e}")
        print("\nTo use this workflow:")
        print("1. Install Ollama: https://ollama.ai")
        print(f"2. Pull the model: ollama pull {args.model}")
        print("3. Ensure Ollama is running")
        sys.exit(1)


if __name__ == "__main__":
    main()
