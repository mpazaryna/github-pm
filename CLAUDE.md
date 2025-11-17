# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GitHub PM is a Python CLI tool that aggregates GitHub issues from multiple repositories and generates comprehensive reports in both markdown and JSON formats. It uses the GitHub CLI (`gh`) as its data source and is designed for project reporting and weekly status updates.

## Key Commands

### Development Setup
```bash
# Install dependencies
uv sync

# Install package in editable mode
uv pip install -e .
```

### Data Collection

#### Using Orchestration Scripts (Recommended)
```bash
# Quick testing collection (small dataset + snapshot)
./scripts/collect.sh --testing

# Production collection (full dataset + snapshot)
./scripts/collect.sh --production

# Custom collection with snapshot
./scripts/collect.sh --config my-config.yaml --snapshot

# Get help
./scripts/collect.sh --help
```

#### Direct CLI Usage
```bash
# Basic usage (generates markdown and JSON reports)
uv run github-pm

# Save timestamped snapshot to data/ directory
uv run github-pm --save-snapshot

# Custom config file
uv run github-pm --config config/collection/testing.yaml

# Custom output file
uv run github-pm --output my-report.md

# Group by different criteria
uv run github-pm --group-by labels
uv run github-pm --group-by milestone
uv run github-pm --group-by assignee

# Specific output format
uv run github-pm --format markdown
uv run github-pm --format json
uv run github-pm --format both
```

### Running Workflows

#### Trend Analysis
```bash
# Compare two snapshots
uv run python workflows/trend_analysis/compare_periods.py 2025-01-17_09-30 2025-01-17_14-15

# Using orchestration script
uv run python scripts/run_workflow.py trend_analysis compare_periods \
  --baseline 2025-01-17_09-30 \
  --current 2025-01-17_14-15

# List available snapshots
uv run python scripts/run_workflow.py trend_analysis compare_periods --list-snapshots
```

#### AI-Powered Repository Comparison
```bash
# Analyze latest snapshot with LangChain + Ollama
uv run python workflows/summarization/repo_comparison.py --model llama3.2

# Using orchestration script
uv run python scripts/run_workflow.py summarization repo_comparison --model llama3.2

# Use different Ollama model
uv run python workflows/summarization/repo_comparison.py --model mistral
```

#### Code Analysis (Commits)
```bash
# Analyze commit messages for a repo
uv run python workflows/code_analysis/commit_report.py \
  --owner mpazaryna \
  --repo chiro \
  --since 2025-01-01 \
  --correlate-issues

# Via orchestration script
uv run python scripts/run_workflow.py code_analysis commit_report \
  --owner mpazaryna \
  --repo chiro \
  --since 2025-01-01
```

#### AI-Powered Weekly Planning
```bash
# Generate AI-powered weekly plan
uv run python workflows/planning/weekly_planner.py

# Look back 14 days for better trends
uv run python workflows/planning/weekly_planner.py --days 14

# Use specific AI model
uv run python workflows/planning/weekly_planner.py --model llama3.2
```

**Note:** Weekly planning works best with status labels. See `workflows/planning/STATUS_LABELS_GUIDE.md` for setup instructions:
```bash
# Quick setup of status labels
gh label create "status:backlog" --color "D4C5F9" --description "Issue is in the backlog"
gh label create "status:ready" --color "0E8A16" --description "Issue is ready to be worked on"
gh label create "status:in progress" --color "FBCA04" --description "Issue is currently being worked on"
gh label create "status:in review" --color "1D76DB" --description "Issue is in review/PR stage"
```

#### Run All Workflows
```bash
# Execute all available workflows on collected data
./scripts/run_all_workflows.sh
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=github_pm --cov-report=html

# Run specific test file
uv run pytest tests/test_github_client.py -v

# Run a single test
uv run pytest tests/test_github_client.py::TestGitHubClient::test_fetch_issues_success -v
```

## Architecture

### System Overview

The system has two main phases:

1. **Data Collection** - Regular snapshots of GitHub issues stored as timestamped datasets
2. **Agentic Workflows** - Analysis workflows that process collected data to generate insights

### Core Components

#### Data Collection Pipeline

1. **GitHubClient** (`github_client.py`) - Wraps the GitHub CLI (`gh`) to fetch issues. Uses subprocess to execute `gh issue list` commands with JSON output.

2. **IssueOrganizer** (`organizer.py`) - Provides multiple organization strategies:
   - `organize_by_repository()` - Groups by repo name
   - `organize_by_labels()` - Groups by issue labels (issues can appear in multiple groups)
   - `organize_by_milestone()` - Groups by milestone (includes "No Milestone" group)
   - `organize_by_assignee()` - Groups by assignee (includes "Unassigned" group)

3. **DataCollector** (`data_collector.py`) - Manages timestamped data snapshots:
   - Creates timestamped directories in `data/`
   - Saves complete JSON snapshot with metadata
   - Maintains `latest` symlink to most recent snapshot
   - Provides `list_snapshots()` and `load_snapshot()` for workflow access

4. **MarkdownReportGenerator** (`report_generator.py`) - Generates human-readable markdown reports with summary statistics and grouped issues.

5. **JSONExporter** (`json_exporter.py`) - Exports structured JSON containing:
   - Metadata (timestamp, version, total count)
   - Complete issues array
   - Summary statistics (counts by state, repo, label, milestone, assignee)
   - Organized data (pre-grouped by all criteria)

6. **StatusAnalyzer** (`status_analyzer.py`) - Analyzes issue status and workflow health:
   - Extracts status from label patterns (backlog, ready, in progress, in review, done)
   - Analyzes flow health and detects bottlenecks
   - Identifies grooming needs and WIP limit violations
   - Tracks milestone progress with velocity calculations
   - Calculates health indicators (overdue, at_risk, behind, on_track, good)
   - Prioritizes issues by milestone, labels, and recency

7. **CommitAnalyzer** (`commit_analyzer.py`) - Analyzes commit messages and work patterns:
   - Parses Conventional Commits format (type(scope): description)
   - Extracts issue references (#123, fixes #456)
   - Tracks breaking changes
   - Generates activity timelines
   - Calculates work type distribution

8. **CLI** (`cli.py`) - Orchestrates the collection pipeline:
   - Loads YAML configuration from `config/collection/`
   - Fetches issues from all configured repos
   - Adds `repository` field to each issue for tracking
   - Organizes issues based on `--group-by` flag
   - Optionally saves timestamped snapshot via `--save-snapshot`
   - Generates reports based on `--format` flag

#### Workflow System

Located in `workflows/` directory, organized by analysis type:

1. **Trend Analysis** (`workflows/trend_analysis/`)
   - `compare_periods.py` - Compares two snapshots to identify trends
   - Analyzes changes in issue counts, states, labels, repositories, assignees
   - Generates insights about significant changes
   - Outputs markdown reports to `reports/adhoc/`

2. **Summarization** (`workflows/summarization/`)
   - `repo_comparison.py` - AI-powered repository comparison using LangChain + Ollama
   - Analyzes differences between repositories
   - Generates natural language insights
   - Outputs reports to `reports/daily/`

3. **Code Analysis** (`workflows/code_analysis/`)
   - `commit_report.py` - Analyze commit messages and work patterns
   - Parses Conventional Commits format
   - Correlates commits with issues
   - Shows work breakdown by type, activity timeline, breaking changes
   - Outputs reports to `reports/adhoc/`

4. **Weekly Planning** (`workflows/planning/`)
   - `weekly_planner.py` - AI-powered weekly planning and work balancing
   - Analyzes commit distribution across repositories
   - Tracks status flow (backlog → ready → in progress → in review → done)
   - Monitors milestone progress with velocity calculations
   - Identifies flow bottlenecks and WIP issues
   - Generates balanced work recommendations
   - Outputs reports to `reports/weekly/`
   - Requires: LangChain + Ollama for AI analysis
   - See: `STATUS_LABELS_GUIDE.md` for setup instructions

5. **Anomaly Detection** (`workflows/anomaly_detection/`) - Coming soon
6. **Custom Reports** (`workflows/custom_reports/`) - Coming soon

Workflows read configuration from `config/workflows/workflow_config.yaml` for thresholds and parameters.

### Data Flow

#### Collection Flow
```
Config YAML → GitHubClient → Raw Issues → IssueOrganizer → Organized Issues
                                     ↓                            ↓
                              DataCollector (if --save-snapshot)  |
                                     ↓                            |
                              data/YYYY-MM-DD_HH-MM-SS/          |
                                                                  ↓
                                                    Reports (markdown/JSON)
```

#### Workflow Flow
```
data/snapshot1/ ──┐
                  ├──→ Workflow → Analysis → reports/
data/snapshot2/ ──┘
```

### Directory Structure

```
github-pm/
├── data/                          # Timestamped data snapshots
│   ├── 2025-01-17_09-30/
│   │   ├── raw.json              # Complete snapshot data
│   │   └── metadata.json         # Quick-access metadata
│   ├── 2025-01-17_14-15/
│   └── latest -> 2025-01-17_14-15  # Symlink to most recent
│
├── reports/                       # Generated reports
│   ├── daily/                    # Daily reports
│   ├── weekly/                   # Weekly reports
│   └── adhoc/                    # Ad-hoc analysis reports
│
├── workflows/                     # Analysis workflows
│   ├── trend_analysis/           # Compare snapshots over time
│   ├── summarization/            # Generate summaries
│   ├── code_analysis/            # Commit analysis and work patterns
│   ├── planning/                 # Weekly planning and work balancing
│   │   ├── weekly_planner.py    # AI-powered weekly planning
│   │   └── STATUS_LABELS_GUIDE.md  # Setup guide for status labels
│   ├── anomaly_detection/        # Detect unusual patterns
│   └── custom_reports/           # Stakeholder-specific reports
│
├── config/
│   ├── collection/               # Data collection configs
│   │   ├── default.yaml         # Production config
│   │   └── testing.yaml         # Testing config (smaller dataset)
│   └── workflows/
│       └── workflow_config.yaml  # Workflow parameters
│
├── scripts/                      # Orchestration scripts
│   ├── collect.sh               # Run data collection
│   ├── run_workflow.py          # Execute specific workflow
│   └── run_all_workflows.sh     # Run full analysis suite
│
└── src/github_pm/               # Core collection modules
```

### Configuration Structure

#### Collection Config (`config/collection/*.yaml`)
```yaml
repositories:
  - owner: org-name
    name: repo-name

issue_state: open  # open, closed, or all
labels: []         # Optional label filter
limit: 100         # Max issues per repo
```

#### Workflow Config (`config/workflows/workflow_config.yaml`)
```yaml
trend_analysis:
  significant_change_threshold: 0.20  # 20% change threshold
  lookback_periods: 3

anomaly_detection:
  stale_threshold_days: 30
  spike_threshold: 0.50

summarization:
  max_top_items: 5
  priority_labels: [critical, high-priority, urgent, bug]
```

## Important Implementation Details

### Issue Data Structure
Issues fetched from GitHub CLI include these fields (defined in `github_client.py:46`):
- `number`, `title`, `state`, `labels`, `assignees`, `milestone`, `url`, `createdAt`, `updatedAt`
- The CLI adds a `repository` field to each issue for tracking

### Data Snapshots
- Created via `--save-snapshot` flag or orchestration scripts
- Timestamped directories: `YYYY-MM-DD_HH-MM-SS` format
- Each snapshot contains:
  - `raw.json` - Complete data with metadata, issues, summary, and all organization views
  - `metadata.json` - Quick-access metadata for listing/filtering
- `latest` symlink always points to most recent snapshot
- Snapshots are immutable - never modified after creation
- Historical snapshots enable trend analysis

### Error Handling
- The CLI continues if individual repos fail to fetch (logs error but doesn't exit)
- GitHubClient raises `RuntimeError` for CLI failures and `ValueError` for JSON parsing errors
- Config loading raises `FileNotFoundError` and `yaml.YAMLError`
- Workflows should handle missing snapshots gracefully

### Output Behavior
- When `--format both` is used, the output filename is used as a base:
  - Markdown: `output.md`
  - JSON: `output.json`
- JSON export always includes all organization strategies, regardless of `--group-by` selection
- Markdown report only uses the selected `--group-by` strategy
- Snapshots always include all organization views for workflow flexibility

### Workflow Patterns
- Workflows load data from `data/` directory using `DataCollector.load_snapshot()`
- Output reports to appropriate `reports/` subdirectory
- Read configuration from `config/workflows/workflow_config.yaml`
- Should be runnable independently or via orchestration scripts
- Trend analysis requires at least 2 snapshots to compare

### Status Flow and Milestone Tracking

The system tracks issue flow through status labels and milestone progress:

#### Status Labels
Status is extracted from issue labels using `StatusAnalyzer.extract_status()`:
- **Backlog**: Issues not yet ready to be worked on
- **Ready**: Groomed issues ready to start
- **In Progress**: Currently being worked on
- **In Review**: PR created, awaiting review
- **Done**: Completed (closed issues)

**Label Patterns Recognized:**
- Case-insensitive matching
- Multiple patterns per status (e.g., "wip", "work in progress", "status:in progress")
- Falls back to: open → backlog, closed → done

#### Flow Health Analysis
`StatusAnalyzer.analyze_flow_health()` identifies bottlenecks:
- **Ready Pileup**: Too many ready but not in progress (suggests need to start work)
- **Review Bottleneck**: Too many in review (suggests need for reviews)
- **Grooming Needed**: Too many backlog but not enough ready (suggests need for grooming)
- **WIP Overload**: Too many items in progress + in review (suggests need to finish work)

#### Milestone Progress Tracking
`StatusAnalyzer.analyze_milestone_progress()` calculates:
- **Progress percentage**: (done / total) * 100
- **Velocity estimation**: Rough current velocity (1.5 issues/week default)
- **Needed velocity**: remaining_issues / weeks_remaining
- **Health indicators**:
  - `overdue`: Past due date
  - `at_risk`: Needed velocity > 2x current velocity
  - `behind`: Needed velocity > 1.5x current velocity
  - `on_track`: Progress > 80%
  - `good`: On track
  - `no_deadline`: No due date set

#### Weekly Planning Integration
The weekly planner (`weekly_planner.py`) uses StatusAnalyzer to:
1. Show status distribution per repository
2. Identify flow bottlenecks
3. Track milestone progress and risks
4. Recommend process improvements
5. Prioritize issues by status, milestone, and labels

**Setup:** See `workflows/planning/STATUS_LABELS_GUIDE.md` for complete setup instructions.

## Testing Approach

Tests use pytest with mocking via `pytest-mock`. Key patterns:
- Mock subprocess calls to GitHub CLI in `GitHubClient` tests
- Use fixture data representing GitHub API responses
- Test both success and error conditions
- Verify JSON structure and summary calculations in exporter tests

## Dependencies

- **Runtime**: `pyyaml`, `python-dateutil`, `langchain`, `langchain-ollama`
- **Dev**: `pytest`, `pytest-cov`, `pytest-mock`
- **External**:
  - GitHub CLI (`gh`) must be installed and authenticated
  - Ollama (optional, for AI-powered summarization workflows)
- **Python**: Requires 3.11+ (uses modern type hints like `dict[str, Any]`)
