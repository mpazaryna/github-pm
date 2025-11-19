# Portfolio Documentation System

## Overview
A standardized approach to maintaining professional project descriptions that can be easily reused across resumes, LinkedIn, portfolios, and interviews.

## Files

### PROJECT.md
The single source of truth for project description. Lives at repo root, version-controlled, and structured for easy extraction.

**Sections:**
- Elevator Pitch (1-liner for quick descriptions)
- Context & Problem (why this project exists)
- Solution & Approach (your methodology)
- Technical Implementation (architecture, stack, design decisions)
- Key Features (5-10 most important capabilities)
- Outcomes & Metrics (quantifiable results)
- Technical Challenges & Solutions (problem-solving examples)
- Learnings & Growth (what you gained from the project)
- Future Enhancements (roadmap and ideas)
- Project Links (repo, demo, docs)
- Tags (searchable keywords)
- Portfolio Use Cases (extraction guide)

### PROJECT.template.md
Copy this to new projects as `PROJECT.md` and fill out sections. Includes guidance notes and extraction commands.

### scripts/extract_portfolio.py
Python script to extract formatted content for different contexts.

## Usage

### Create PROJECT.md for New Project
```bash
# Copy template to project root
cp PROJECT.template.md /path/to/new-project/PROJECT.md

# Edit with your project details
cd /path/to/new-project
vim PROJECT.md  # or your preferred editor
```

### Extract for Different Contexts

#### Resume Format
```bash
uv run python scripts/extract_portfolio.py resume
```
Output: Elevator pitch + top 3 outcomes + tech stack (plain text, resume-ready)

#### LinkedIn Post
```bash
uv run python scripts/extract_portfolio.py linkedin
```
Output: Elevator pitch + top 5 features + hashtags (social media format)

#### Interview Prep
```bash
uv run python scripts/extract_portfolio.py interview
```
Output: Problem context + solution approach + top 3 technical challenges (discussion format)

#### Portfolio Website
```bash
uv run python scripts/extract_portfolio.py website
```
Output: Full project page with problem, solution, features, tech stack, outcomes (web-ready markdown)

#### Tags Only
```bash
uv run python scripts/extract_portfolio.py tags
```
Output: Comma-separated list of technology and domain tags

### Save to Files
```bash
# Save resume version
uv run python scripts/extract_portfolio.py resume > resume-project.txt

# Save LinkedIn version
uv run python scripts/extract_portfolio.py linkedin > linkedin-project.md

# Save interview prep
uv run python scripts/extract_portfolio.py interview > interview-prep.md
```

## Maintenance Workflow

### Quarterly Review
1. Update outcomes/metrics with latest numbers
2. Add new features to Key Features section
3. Update technical challenges if new ones emerged
4. Refresh learnings based on recent insights
5. Update tags with new technologies used

### When Applying for Jobs
1. Run `extract_portfolio.py resume` for resume bullets
2. Run `extract_portfolio.py tags` to update skill keywords
3. Run `extract_portfolio.py interview` for interview prep doc
4. Customize output for specific job requirements

### When Updating Portfolio Site
1. Run `extract_portfolio.py website` for base content
2. Add screenshots, demos, or visuals
3. Link to GitHub PROJECT.md for full details
4. Update with latest metrics and outcomes

## Benefits

**Version Controlled**: PROJECT.md lives in git, changes tracked over time

**Single Source of Truth**: Update once, extract many times for different uses

**Consistent Format**: Same structure across all projects makes comparison easy

**Easy Automation**: Can build tools to aggregate across all projects

**Context Preservation**: Captures technical decisions and learnings while fresh

**Interview Ready**: Always have talking points prepared for technical discussions

**SEO Friendly**: Tags and structured content improve discoverability

## Replication Strategy

### For Each New Project:
1. Copy `PROJECT.template.md` to project root as `PROJECT.md`
2. Fill out as you build (don't wait until end)
3. Update quarterly or at major milestones
4. Extract when needed for job applications or portfolio updates

### For All Projects:
1. Create aggregation script to collect PROJECT.md from all repos
2. Build master portfolio site that pulls from all PROJECT.md files
3. Generate resume dynamically from latest PROJECT.md files
4. Create skill matrix by aggregating all tags

## Example Aggregation Script

```python
#!/usr/bin/env python3
"""Aggregate PROJECT.md from all repos for portfolio generation."""

import json
from pathlib import Path
from extract_portfolio import PortfolioExtractor

def aggregate_projects(project_dirs: list[Path]) -> dict:
    """Aggregate all PROJECT.md files."""
    projects = []

    for project_dir in project_dirs:
        project_md = project_dir / "PROJECT.md"
        if project_md.exists():
            extractor = PortfolioExtractor(project_md)

            projects.append({
                "name": project_dir.name,
                "elevator_pitch": extractor.extract_elevator_pitch(),
                "outcomes": extractor.extract_outcomes(),
                "tags": extractor.extract_tags(),
                "features": extractor.extract_key_features(),
                "challenges": extractor.extract_challenges(),
            })

    return {"projects": projects, "count": len(projects)}

# Usage
project_dirs = [
    Path("~/workspace/github-pm").expanduser(),
    Path("~/workspace/other-project").expanduser(),
    # Add more projects...
]

portfolio_data = aggregate_projects(project_dirs)
print(json.dumps(portfolio_data, indent=2))
```

## Tips

- **Fill PROJECT.md as you build**, not at the end - context is fresh
- **Use actual metrics** - "reduced time by 50%" better than "improved performance"
- **Keep technical challenges real** - interviewers can spot BS
- **Update tags regularly** - new technologies should be captured
- **Test extractions** - run scripts to verify output looks good
- **Link to PROJECT.md** from your GitHub profile README
- **Quantify everything possible** - numbers tell better stories
- **Review before job applications** - ensure all projects are current

## Future Enhancements

- GitHub Action to validate PROJECT.md structure
- VS Code extension for PROJECT.md editing
- Web service to render PROJECT.md files beautifully
- CLI tool to quickly update metrics across all projects
- Portfolio site generator that pulls from all PROJECT.md files
- Resume builder that auto-generates from PROJECT.md files
