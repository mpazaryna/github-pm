# GitHub Project Management

A Python-based GitHub CLI tool that retrieves and organizes issues from multiple repositories, generating comprehensive markdown reports for project reporting and weekly status updates for stakeholders, developers, and decision makers.

## Features

- **Data Collection**:
  - Fetch issues from multiple GitHub repositories using GitHub CLI
  - Timestamped snapshots for historical tracking
  - Organize issues by repository, labels, milestones, or assignees
  - Multiple output formats (Markdown reports and JSON export)

- **Agentic Workflow Analysis**:
  - **Trend Analysis** - Compare snapshots to identify patterns and changes
  - **AI-Powered Summarization** - LangChain + Ollama for repository comparisons and insights
  - **Anomaly Detection** - Flag unusual patterns and stale issues (coming soon)
  - **Custom Reports** - Stakeholder-specific reports (coming soon)

- **Rich Data Structure**:
  - Complete issue data (all fields preserved)
  - Summary statistics (counts by state, repo, label, milestone, assignee)
  - Pre-organized data views (by repo, labels, milestones, assignees)
  - Perfect for dashboards, calendars, and custom analytics

- **Developer Experience**:
  - Easy-to-use orchestration scripts
  - Configurable via YAML
  - Test-driven development with pytest

## Prerequisites

- Python 3.11 or higher
- [GitHub CLI (gh)](https://cli.github.com/) installed and authenticated
- [uv](https://github.com/astral-sh/uv) for Python package management
- [Ollama](https://ollama.ai) (optional, for AI-powered analysis)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd github-pm
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Install the package in editable mode:
```bash
uv pip install -e .
```

## Configuration

1. Create your production configuration:
```bash
cp config.example.yaml config/collection/production.yaml
```

2. Edit `config/collection/production.yaml` to add your repositories:
```yaml
repositories:
  - owner: your-org
    name: your-repo
  - owner: your-org
    name: another-repo

# Optional: Filter issues by state
issue_state: open  # open, closed, or all

# Optional: Limit number of issues per repo
limit: 100
```

**Available configurations:**
- `config/collection/production.yaml` - Your actual repositories (gitignored)
- `config/collection/testing.yaml` - Small dataset for testing
- `config/collection/default.yaml` - Template with examples

## Usage

### Basic Usage

Generate both markdown and JSON reports (default):
```bash
uv run github-pm
```

This generates:
- `github-issues-report.md` - Human-readable markdown report
- `github-issues-report.json` - Structured data for programmatic access

### Custom Configuration File

Specify a custom configuration file:
```bash
uv run github-pm --config my-config.yaml
```

### Custom Output File

Specify a custom output file:
```bash
uv run github-pm --output my-report.md
```

### Organize by Different Criteria

Organize issues by labels:
```bash
uv run github-pm --group-by labels
```

Organize issues by milestones:
```bash
uv run github-pm --group-by milestone
```

Organize issues by assignees:
```bash
uv run github-pm --group-by assignee
```

### Output Formats

Generate only markdown:
```bash
uv run github-pm --format markdown
```

Generate only JSON:
```bash
uv run github-pm --format json
```

Generate both (default):
```bash
uv run github-pm --format both
```

### Complete Example

```bash
uv run github-pm \
  --config config/collection/production.yaml \
  --output weekly-report \
  --group-by milestone \
  --format both
```

## Data Collection & Trend Analysis

For regular monitoring and trend analysis, use the **timestamped snapshot system** and **agentic workflows**.

### Quick Start with Orchestration Scripts

The easiest way to collect data and run analysis:

```bash
# 1. Collect data from your repositories (saves timestamped snapshot)
./scripts/collect.sh --production

# 2. Wait some time (hours, days, or weeks)
# 3. Collect again to capture changes
./scripts/collect.sh --production

# 4. Run all workflows to analyze trends
./scripts/run_all_workflows.sh
```

### Data Collection Options

```bash
# Production collection (uses config/collection/production.yaml)
./scripts/collect.sh --production

# Testing with small dataset (uses config/collection/testing.yaml)
./scripts/collect.sh --testing

# Custom configuration
./scripts/collect.sh --config path/to/config.yaml --snapshot

# Get help
./scripts/collect.sh --help
```

### Running Workflows

#### Trend Analysis

Compare two snapshots to identify trends and changes:

```bash
# Automatically compare the two most recent snapshots
./scripts/run_all_workflows.sh

# Or compare specific snapshots
uv run python scripts/run_workflow.py trend_analysis compare_periods \
  --baseline 2025-11-17_09-30 \
  --current 2025-11-17_14-15

# List available snapshots
uv run python scripts/run_workflow.py trend_analysis compare_periods --list-snapshots
```

**Trend analysis provides:**
- Overall issue count changes
- State transitions (open/closed)
- Repository-specific trends
- Label usage patterns
- Assignee workload changes
- Automatic insights about significant changes

#### AI-Powered Repository Comparison

Use LangChain + Ollama for natural language insights comparing your repositories:

```bash
# Analyze latest snapshot
uv run python workflows/summarization/repo_comparison.py --model llama3.2

# Or via orchestration script
uv run python scripts/run_workflow.py summarization repo_comparison --model llama3.2

# Use different model
uv run python workflows/summarization/repo_comparison.py --model mistral
```

**Prerequisites:**
1. Install [Ollama](https://ollama.ai)
2. Pull a model: `ollama pull llama3.2`
3. Ensure Ollama is running

**AI analysis provides:**
- Overview of each repository's focus and patterns
- Key differences between repositories
- Workload distribution insights
- Notable themes and trends
- Actionable recommendations

#### Example Trend Report

After running workflows, you'll find reports in `reports/adhoc/`:

```markdown
# Trend Analysis Report

**Baseline:** 2025-11-17T09:30:00
**Current:** 2025-11-17T14:15:00

## Key Insights
- Total issues increased by 15 (12.5%)
- Open issues increased by 12
- Repository 'your-org/your-repo' increased by 8 issues
- Label 'bug' grew most (+5 issues)
- Unassigned issues decreased by 3

## Overall Changes
- Baseline Total: 120
- Current Total: 135
- Change: +15 (+12.5%)
```

### Regular Workflow Example

Establish a regular cadence for monitoring:

```bash
# Daily collection (e.g., via cron at 9am)
0 9 * * * cd /path/to/github-pm && ./scripts/collect.sh --production

# Weekly analysis (e.g., via cron on Monday at 10am)
0 10 * * 1 cd /path/to/github-pm && ./scripts/run_all_workflows.sh
```

### Understanding the Data Directory

Each collection creates a timestamped snapshot:

```
data/
├── 2025-11-17_09-30-00/
│   ├── raw.json              # Complete snapshot data
│   └── metadata.json         # Quick-access metadata
├── 2025-11-17_14-15-30/
│   ├── raw.json
│   └── metadata.json
└── latest -> 2025-11-17_14-15-30  # Symlink to most recent
```

**Benefits:**
- Historical data preserved for trend analysis
- Compare any two time periods
- Build custom dashboards from timestamped data
- Immutable snapshots (never modified after creation)

## Working with JSON Data

The JSON export provides structured data perfect for building dashboards, calendars, and custom reports. The JSON file contains:

### JSON Structure

```json
{
  "metadata": {
    "generated_at": "2025-11-17T07:45:57.762632",
    "version": "0.1.0",
    "total_issues": 48
  },
  "issues": [
    // Array of all issues with complete data
  ],
  "summary": {
    "total_issues": 48,
    "by_state": { "OPEN": 45, "CLOSED": 3 },
    "by_repository": { "owner/repo": 15, ... },
    "by_label": { "bug": 10, "enhancement": 5, ... },
    "by_milestone": { "v1.0": 8, "v2.0": 12, ... },
    "by_assignee": { "user1": 20, "Unassigned": 10, ... }
  },
  "organized": {
    "by_repository": { /* issues grouped by repo */ },
    "by_labels": { /* issues grouped by labels */ },
    "by_milestone": { /* issues grouped by milestone */ },
    "by_assignee": { /* issues grouped by assignee */ }
  }
}
```

### Programmatic Access Example

```python
import json
from datetime import datetime
from collections import Counter

# Load the JSON data
with open('github-issues-report.json') as f:
    data = json.load(f)

# Access summary statistics
print(f"Total issues: {data['summary']['total_issues']}")
print(f"Open issues: {data['summary']['by_state']['OPEN']}")

# Get issues by repository
repo_issues = data['organized']['by_repository']
for repo, issues in repo_issues.items():
    print(f"{repo}: {len(issues)} issues")

# Find issues created this week
from datetime import datetime, timedelta
week_ago = datetime.now() - timedelta(days=7)

recent_issues = [
    issue for issue in data['issues']
    if datetime.fromisoformat(issue['createdAt'].replace('Z', '+00:00')) > week_ago
]

print(f"Issues created this week: {len(recent_issues)}")

# Build a calendar view
issues_by_date = {}
for issue in data['issues']:
    date = issue['createdAt'][:10]  # Get YYYY-MM-DD
    issues_by_date.setdefault(date, []).append(issue)

# Most active labels
label_counts = data['summary']['by_label']
top_labels = sorted(label_counts.items(), key=lambda x: x[1], reverse=True)[:5]
print("Top 5 labels:", top_labels)
```

### Use Cases for JSON Data

- **Dashboard Creation**: Use the summary statistics to create visual dashboards
- **Calendar Views**: Group issues by creation/update dates for calendar displays
- **Trend Analysis**: Track issue counts over time, by label, or by repository
- **Custom Reports**: Generate custom reports filtered by specific criteria
- **Integration**: Feed data into project management tools or databases
- **Metrics**: Calculate team velocity, response times, and other KPIs

## Development

### Running Tests

Run all tests:
```bash
uv run pytest
```

Run tests with coverage:
```bash
uv run pytest --cov=github_pm --cov-report=html
```

Run specific test file:
```bash
uv run pytest tests/test_github_client.py -v
```

### Project Structure

```
github-pm/
├── src/
│   └── github_pm/
│       ├── __init__.py
│       ├── cli.py              # Main CLI entry point
│       ├── data_collector.py   # Timestamped snapshot manager
│       ├── github_client.py    # GitHub CLI wrapper
│       ├── organizer.py        # Issue organizer
│       ├── report_generator.py # Markdown report generator
│       └── json_exporter.py    # JSON export functionality
├── workflows/                  # Agentic analysis workflows
│   ├── trend_analysis/
│   │   └── compare_periods.py  # Compare two snapshots
│   ├── summarization/          # Coming soon
│   ├── anomaly_detection/      # Coming soon
│   └── custom_reports/         # Coming soon
├── scripts/                    # Orchestration scripts
│   ├── collect.sh             # Data collection wrapper
│   ├── run_workflow.py        # Workflow execution
│   └── run_all_workflows.sh   # Run all workflows
├── config/
│   ├── collection/            # Data collection configs
│   │   ├── production.yaml   # Your repos (gitignored)
│   │   ├── testing.yaml      # Small test dataset
│   │   └── default.yaml      # Template
│   └── workflows/
│       └── workflow_config.yaml  # Workflow parameters
├── data/                      # Timestamped snapshots (gitignored)
├── reports/                   # Generated reports (gitignored)
│   ├── daily/
│   ├── weekly/
│   └── adhoc/
├── tests/
│   ├── test_github_client.py
│   ├── test_data_collector.py
│   ├── test_organizer.py
│   └── test_report_generator.py
├── config.example.yaml
├── pyproject.toml
└── README.md
```

## How It Works

### Data Collection Pipeline

1. **Configuration**: Reads repository list from YAML config
2. **Fetching**: Uses GitHub CLI (`gh`) to fetch issues from each repository
3. **Organization**: Groups issues by specified criteria (repo, labels, milestones, assignees)
4. **Snapshot Creation**: Saves timestamped data to `data/YYYY-MM-DD_HH-MM-SS/`
5. **Report Generation**: Creates formatted markdown and JSON reports

### Workflow Analysis Pipeline

1. **Data Loading**: Loads two or more snapshots from `data/` directory
2. **Comparison**: Analyzes differences between snapshots
3. **Insight Generation**: Identifies significant trends and patterns
4. **Report Creation**: Generates detailed analysis reports in `reports/`

## Example Output

The generated markdown report includes:
- Report header with generation timestamp
- Summary statistics (total issues, total repositories/groups)
- Issues grouped by chosen criteria
- For each issue:
  - Issue number and title
  - State (open/closed)
  - Labels
  - Assignees
  - Milestone
  - Creation date
  - Link to issue

## License

MIT

