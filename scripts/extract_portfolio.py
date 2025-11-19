#!/usr/bin/env python3
"""
Extract portfolio content from PROJECT.md for different contexts.

Usage:
    python scripts/extract_portfolio.py resume
    python scripts/extract_portfolio.py linkedin
    python scripts/extract_portfolio.py interview
    python scripts/extract_portfolio.py website
    python scripts/extract_portfolio.py tags
"""

import argparse
import re
import sys
from pathlib import Path


class PortfolioExtractor:
    """Extract sections from PROJECT.md for different portfolio uses."""

    def __init__(self, project_md_path: Path):
        """Initialize extractor with PROJECT.md content."""
        self.content = project_md_path.read_text()
        self.sections = self._parse_sections()

    def _parse_sections(self) -> dict[str, str]:
        """Parse PROJECT.md into sections."""
        sections = {}
        current_section = None
        current_content = []

        for line in self.content.split("\n"):
            # Check for section headers
            if line.startswith("## "):
                # Save previous section
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()

                # Start new section
                current_section = line[3:].strip()
                current_content = []
            else:
                if current_section:
                    current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def extract_elevator_pitch(self) -> str:
        """Get elevator pitch (1-liner for resume/LinkedIn)."""
        return self.sections.get("Elevator Pitch", "").strip()

    def extract_tech_stack(self) -> list[str]:
        """Get technology stack as list."""
        tech_section = self.sections.get("Technical Implementation", "")

        # Find Technology Stack subsection
        match = re.search(
            r"### Technology Stack\n(.*?)(?:\n###|\Z)", tech_section, re.DOTALL
        )
        if not match:
            return []

        tech_content = match.group(1)

        # Extract technologies from bullet points
        technologies = []
        for line in tech_content.split("\n"):
            line = line.strip()
            if line.startswith("-"):
                # Extract after colon if present
                if ":" in line:
                    tech_list = line.split(":", 1)[1].strip()
                    # Split by comma and clean
                    technologies.extend(
                        [t.strip() for t in tech_list.split(",") if t.strip()]
                    )

        return technologies

    def extract_outcomes(self) -> list[str]:
        """Get outcomes/metrics as bullet list."""
        outcomes_section = self.sections.get("Outcomes & Metrics", "")

        outcomes = []
        for line in outcomes_section.split("\n"):
            line = line.strip()
            if line.startswith("-"):
                # Remove markdown and clean
                clean_line = line[1:].strip()
                # Extract the actual metric part (after **)
                if "**:" in clean_line:
                    clean_line = clean_line.split("**:", 1)[1].strip()
                outcomes.append(clean_line)

        return outcomes

    def extract_challenges(self) -> list[dict[str, str]]:
        """Get technical challenges as structured list."""
        challenges_section = self.sections.get("Technical Challenges & Solutions", "")

        challenges = []
        current_challenge = None
        current_problem = None
        current_solution = None

        for line in challenges_section.split("\n"):
            line = line.strip()

            # Match challenge headers
            if line.startswith("### Challenge"):
                # Save previous challenge
                if current_challenge:
                    challenges.append(
                        {
                            "name": current_challenge,
                            "problem": current_problem,
                            "solution": current_solution,
                        }
                    )

                # Start new challenge
                current_challenge = line.split(":", 1)[1].strip() if ":" in line else ""
                current_problem = None
                current_solution = None

            elif line.startswith("**Problem**:"):
                current_problem = line.split("**Problem**:", 1)[1].strip()

            elif line.startswith("**Solution**:"):
                current_solution = line.split("**Solution**:", 1)[1].strip()

        # Save last challenge
        if current_challenge:
            challenges.append(
                {
                    "name": current_challenge,
                    "problem": current_problem,
                    "solution": current_solution,
                }
            )

        return challenges

    def extract_tags(self) -> list[str]:
        """Get tags as list."""
        tags_section = self.sections.get("Tags", "")
        # Extract content between backticks
        tags = re.findall(r"`([^`]+)`", tags_section)
        return tags

    def extract_key_features(self) -> list[str]:
        """Get key features as list."""
        features_section = self.sections.get("Key Features", "")

        features = []
        for line in features_section.split("\n"):
            line = line.strip()
            if line.startswith("-"):
                # Extract feature name and description
                clean_line = line[1:].strip()
                # Remove markdown bold
                if "**:" in clean_line:
                    feature_name = clean_line.split("**:", 1)[0].replace("**", "").strip()
                    feature_desc = clean_line.split("**:", 1)[1].strip()
                    features.append(f"{feature_name}: {feature_desc}")
                else:
                    features.append(clean_line)

        return features

    def format_for_resume(self) -> str:
        """Format for resume bullet points."""
        output = []

        # Project name
        title_match = re.match(r"^# (.+?) -", self.content)
        if title_match:
            output.append(f"## {title_match.group(1)}")
            output.append("")

        # Elevator pitch
        output.append(self.extract_elevator_pitch())
        output.append("")

        # Key outcomes
        output.append("**Key Outcomes:**")
        for outcome in self.extract_outcomes()[:3]:  # Top 3
            output.append(f"- {outcome}")
        output.append("")

        # Tech stack
        output.append("**Technologies:**")
        tech_list = self.extract_tech_stack()[:10]  # Top 10
        output.append(", ".join(tech_list))

        return "\n".join(output)

    def format_for_linkedin(self) -> str:
        """Format for LinkedIn project post."""
        output = []

        # Title
        title_match = re.match(r"^# (.+?) -", self.content)
        if title_match:
            output.append(f"# {title_match.group(1)}")
            output.append("")

        # Elevator pitch
        output.append(self.extract_elevator_pitch())
        output.append("")

        # Top features
        output.append("Key Features:")
        for feature in self.extract_key_features()[:5]:  # Top 5
            output.append(f"✅ {feature}")
        output.append("")

        # Tags
        tags = self.extract_tags()
        output.append(" ".join([f"#{tag}" for tag in tags[:8]]))  # Top 8 tags

        return "\n".join(output)

    def format_for_interview(self) -> str:
        """Format for technical interview discussion."""
        output = []

        # Title
        title_match = re.match(r"^# (.+?) -", self.content)
        if title_match:
            output.append(f"## {title_match.group(1)}")
            output.append("")

        # Problem context
        output.append("**Problem Context:**")
        context = self.sections.get("Context & Problem", "")
        output.append(context)
        output.append("")

        # Solution approach
        output.append("**Solution Approach:**")
        solution = self.sections.get("Solution & Approach", "")
        output.append(solution)
        output.append("")

        # Technical challenges
        output.append("**Technical Challenges:**")
        challenges = self.extract_challenges()
        for i, challenge in enumerate(challenges[:3], 1):  # Top 3
            output.append(f"{i}. **{challenge['name']}**")
            output.append(f"   - Problem: {challenge['problem']}")
            output.append(f"   - Solution: {challenge['solution']}")
            output.append("")

        return "\n".join(output)

    def format_for_website(self) -> str:
        """Format for portfolio website."""
        output = []

        # Title
        title_match = re.match(r"^# (.+?) -", self.content)
        if title_match:
            output.append(f"# {title_match.group(1)}")
            output.append("")

        # Context & Problem
        output.append("## The Problem")
        context = self.sections.get("Context & Problem", "")
        output.append(context)
        output.append("")

        # Solution
        output.append("## The Solution")
        solution = self.sections.get("Solution & Approach", "")
        output.append(solution)
        output.append("")

        # Key features
        output.append("## Key Features")
        for feature in self.extract_key_features():
            output.append(f"- {feature}")
        output.append("")

        # Tech stack
        output.append("## Technology Stack")
        tech_list = self.extract_tech_stack()
        # Group by 3
        for i in range(0, len(tech_list), 3):
            chunk = tech_list[i : i + 3]
            output.append(f"- {', '.join(chunk)}")
        output.append("")

        # Outcomes
        output.append("## Outcomes")
        for outcome in self.extract_outcomes():
            output.append(f"- {outcome}")

        return "\n".join(output)

    def format_tags_only(self) -> str:
        """Extract tags only."""
        tags = self.extract_tags()
        return ", ".join(tags)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract portfolio content from PROJECT.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Resume format
  python scripts/extract_portfolio.py resume

  # LinkedIn post
  python scripts/extract_portfolio.py linkedin

  # Interview prep
  python scripts/extract_portfolio.py interview

  # Portfolio website
  python scripts/extract_portfolio.py website

  # Tags only
  python scripts/extract_portfolio.py tags
        """,
    )

    parser.add_argument(
        "format",
        choices=["resume", "linkedin", "interview", "website", "tags"],
        help="Output format",
    )

    parser.add_argument(
        "--project-md",
        type=Path,
        default=Path("PROJECT.md"),
        help="Path to PROJECT.md file (default: PROJECT.md)",
    )

    args = parser.parse_args()

    # Check if PROJECT.md exists
    if not args.project_md.exists():
        print(f"Error: {args.project_md} not found", file=sys.stderr)
        print(
            "Create PROJECT.md using PROJECT.template.md as a guide", file=sys.stderr
        )
        sys.exit(1)

    # Extract content
    extractor = PortfolioExtractor(args.project_md)

    # Format based on requested format
    if args.format == "resume":
        print(extractor.format_for_resume())
    elif args.format == "linkedin":
        print(extractor.format_for_linkedin())
    elif args.format == "interview":
        print(extractor.format_for_interview())
    elif args.format == "website":
        print(extractor.format_for_website())
    elif args.format == "tags":
        print(extractor.format_tags_only())


if __name__ == "__main__":
    main()
