---
title: GitHub PM - Feature Catalog
type: feature-moc
generated: 2025-11-20
last_updated: 2025-11-20
project: github-pm
---

# Feature Catalog

> Complete reference of all implemented features in GitHub PM

[← Back to MOC](./README.md)

## Table of Contents

- [Data Collection Features](#data-collection-features)
- [Workflow Analysis Features](#workflow-analysis-features)
- [Dashboard & Visualization](#dashboard--visualization)
- [Configuration & Orchestration](#configuration--orchestration)
- [Testing Infrastructure](#testing-infrastructure)

---

## Data Collection Features

### 1. Multi-Repository Issue Fetching

**Status**: ✅ Implemented

**Description**: Fetch issues from multiple GitHub repositories in a single collection run using the GitHub CLI.

**Implementation**: [src/github_pm/github_client.py:11](../../src/github_pm/github_client.py)

**Key Capabilities**:
- Uses `gh issue list` CLI command via subprocess
- Filters by state (open, closed, all)
- Configurable limit per repository
- Returns structured JSON with all issue fields
- Error handling for CLI failures

**Configuration**:
```yaml
repositories:
  - owner: org-name
    name: repo-name
issue_state: open  # open, closed, or all
limit: 100
```

**CLI Usage**:
```bash
uv run github-pm --config config/collection/production.yaml
```

---

### 2. Timestamped Snapshot System

**Status**: ✅ Implemented

**Description**: Create immutable, timestamped snapshots of collected issue data for historical tracking and trend analysis.

**Implementation**: [src/github_pm/data_collector.py:22](../../src/github_pm/data_collector.py)

**Key Capabilities**:
- Timestamped directory structure: `YYYY-MM-DD_HH-MM-SS/`
- Immutable snapshots (never modified after creation)
- Symlink to latest snapshot for easy access
- Comprehensive snapshot data:
  - Complete issue list with all fields
  - Metadata (timestamp, version, repo list)
  - Summary statistics
  - Pre-organized views (by repo, label, milestone, assignee)

**Data Structure**:
```
data/
├── 2025-11-20_09-30-00/
│   ├── raw.json           # Complete snapshot
│   └── metadata.json      # Quick-access metadata
├── 2025-11-20_14-15-00/
└── latest -> 2025-11-20_14-15-00
```

**CLI Usage**:
```bash
# Create snapshot during collection
uv run github-pm --save-snapshot

# Or use orchestration script
./scripts/collect.sh --production
```

---

### 3. SOD/EOD Snapshot Workflow

**Status**: ✅ Implemented

**Description**: Start-of-day (SOD) and end-of-day (EOD) snapshot system for tracking daily progress.

**Implementation**: [src/github_pm/data_collector.py:22](../../src/github_pm/data_collector.py)

**Key Capabilities**:
- Label-based snapshots (`--label sod` or `--label eod`)
- Separate symlinks: `latest-sod.json`, `latest-eod.json`
- Filename format: `YYYY-MM-DD-sod.json`
- Dashboard integration for viewing SOD/EOD data

**CLI Usage**:
```bash
# Morning snapshot
uv run github-pm --save-snapshot --label sod

# Evening snapshot
uv run github-pm --save-snapshot --label eod

# Dashboard with SOD/EOD support
uv run dashboard start --sod
```

---

### 4. Issue Organization Strategies

**Status**: ✅ Implemented

**Description**: Multiple strategies for organizing and grouping issues in reports.

**Implementation**: [src/github_pm/organizer.py](../../src/github_pm/organizer.py)

**Strategies**:

1. **By Repository** - Group issues by source repository
2. **By Labels** - Group by labels (issues can appear in multiple groups)
3. **By Milestone** - Group by milestone (includes "No Milestone")
4. **By Assignee** - Group by assignee (includes "Unassigned")

**CLI Usage**:
```bash
uv run github-pm --group-by repository  # Default
uv run github-pm --group-by labels
uv run github-pm --group-by milestone
uv run github-pm --group-by assignee
```

**Key Implementation**:
- All strategies pre-computed during collection
- JSON export includes all organization views
- Markdown report uses selected strategy

---

### 5. Markdown Report Generation

**Status**: ✅ Implemented

**Description**: Human-readable markdown reports with summary statistics and organized issue listings.

**Implementation**: [src/github_pm/report_generator.py](../../src/github_pm/report_generator.py)

**Output Includes**:
- Generation timestamp
- Summary statistics (total issues, groups)
- Issues grouped by selected strategy
- Complete issue details:
  - Number, title, state
  - Labels, assignees, milestone
  - Creation date
  - GitHub URL

**CLI Usage**:
```bash
uv run github-pm --format markdown --output report.md
```

---

### 6. JSON Export

**Status**: ✅ Implemented

**Description**: Structured JSON export containing complete issue data, summaries, and all organization views.

**Implementation**: [src/github_pm/json_exporter.py](../../src/github_pm/json_exporter.py)

**JSON Structure**:
```json
{
  "metadata": {
    "generated_at": "2025-11-20T10:30:00",
    "version": "0.1.0",
    "total_issues": 48
  },
  "issues": [ /* complete issue array */ ],
  "summary": {
    "total_issues": 48,
    "by_state": {},
    "by_repository": {},
    "by_label": {},
    "by_milestone": {},
    "by_assignee": {}
  },
  "organized": {
    "by_repository": {},
    "by_labels": {},
    "by_milestone": {},
    "by_assignee": {}
  }
}
```

**Use Cases**:
- Dashboard data source
- Custom analytics
- Integration with other tools
- Programmatic access

---

## Workflow Analysis Features

### 7. Trend Analysis

**Status**: ✅ Implemented

**Description**: Compare two snapshots to identify trends, changes, and patterns over time.

**Implementation**: [workflows/trend_analysis/compare_periods.py](../../workflows/trend_analysis/compare_periods.py)

**Analyzes**:
- Overall issue count changes
- State transitions (open → closed)
- Repository-specific trends
- Label usage patterns
- Milestone progress
- Assignee workload changes

**CLI Usage**:
```bash
# Compare two specific snapshots
uv run python workflows/trend_analysis/compare_periods.py \
  2025-11-20_09-30 2025-11-20_14-15

# List available snapshots
uv run python workflows/trend_analysis/compare_periods.py --list-snapshots
```

**Output**: Markdown report in `reports/adhoc/` with insights and percentage changes

---

### 8. AI-Powered Weekly Planning

**Status**: ✅ Implemented

**Description**: LangChain + Ollama powered weekly planning that analyzes work distribution and recommends balanced allocation.

**Implementation**: [workflows/planning/weekly_planner.py](../../workflows/planning/weekly_planner.py)

**Key Features**:

1. **Work Distribution Analysis**
   - Analyzes commit percentages per repository
   - Identifies neglected repositories (< 10% commits)
   - Flags overworked repositories (> 60% commits)

2. **Backlog Analysis**
   - Current open issue counts per repository
   - Status distribution (backlog, ready, in progress, in review)
   - Unassigned issue tracking

3. **Status Flow Analysis**
   - Identifies bottlenecks (e.g., too many Ready but none In Progress)
   - WIP (Work In Progress) health monitoring
   - Grooming needs detection

4. **Milestone Progress Tracking**
   - Progress percentage (done / total)
   - Days remaining until deadline
   - Velocity calculations (needed vs current)
   - Health indicators: overdue, at_risk, behind, on_track, good

5. **AI Recommendations**
   - Suggested work distribution percentages
   - Specific priority issues per repository
   - Process improvements (CI/CD, grooming sessions)
   - Flow optimization suggestions

**CLI Usage**:
```bash
# Generate weekly plan (last 7 days)
uv run python workflows/planning/weekly_planner.py

# Look back 14 days for better trend data
uv run python workflows/planning/weekly_planner.py --days 14

# Use different Ollama model
uv run python workflows/planning/weekly_planner.py --model mistral
```

**Output**:
- Markdown report in `reports/weekly/plan_TIMESTAMP.md`
- JSON data in `reports/weekly/plan_TIMESTAMP.json`

**Requirements**:
- Ollama installed and running
- LLM model pulled (e.g., `ollama pull llama3.2`)

---

### 9. Status Flow Analysis

**Status**: ✅ Implemented

**Description**: Track issue flow through workflow stages using status labels, identify bottlenecks, and recommend process improvements.

**Implementation**: [src/github_pm/status_analyzer.py](../../src/github_pm/status_analyzer.py)

**Status Patterns Recognized**:
- **Backlog**: `status:backlog`, `backlog`
- **Ready**: `status:ready`, `ready`, `todo`
- **In Progress**: `status:in progress`, `wip`, `work in progress`
- **In Review**: `status:in review`, `review`
- **Done**: `status:done`, `done`, `completed` (or CLOSED state)

**Flow Health Metrics**:
- Ready pileup detection (many ready, few in progress)
- Review bottleneck detection (too many in review)
- Grooming need detection (many backlog, few ready)
- WIP overload detection (too many items active)

**Recommendations Generated**:
- "Pick up more 'Ready' work - you have X groomed issues waiting"
- "Review bottleneck - prioritize reviewing the X pending PRs"
- "Need grooming session - move backlog issues to 'Ready'"
- "WIP too high (X items) - focus on finishing before starting new work"

**Integration**:
- Used by weekly planner
- Used by dashboard for flow visualization
- Can be used standalone for workflow health checks

---

### 10. Milestone Progress Tracking

**Status**: ✅ Implemented

**Description**: Track milestone progress with velocity calculations, health indicators, and deadline risk assessment.

**Implementation**: [src/github_pm/status_analyzer.py:183](../../src/github_pm/status_analyzer.py)

**Tracks**:
- Total issues vs done issues
- Progress percentage
- Days remaining until due date
- Needed velocity (issues/week to complete on time)
- Current velocity estimate

**Health Indicators**:
- **Overdue**: Past due date
- **At Risk**: Needed velocity > 2x current velocity
- **Behind**: Needed velocity > 1.5x current velocity
- **On Track**: Progress > 80%
- **Good**: On track to complete
- **No Deadline**: No due date set

**Integration**:
- Weekly planner shows milestone health
- Dashboard displays milestone progress
- Roadmap generator uses for timeline predictions

---

### 11. Commit Analysis

**Status**: ✅ Implemented

**Description**: Analyze commit messages to understand actual work delivered, track conventions, and correlate with issues.

**Implementation**: [src/github_pm/commit_analyzer.py](../../src/github_pm/commit_analyzer.py)

**Parses**:
- Conventional Commits format: `type(scope): description`
- Issue references: `#123`, `fixes #456`, `closes #789`
- Breaking changes: `BREAKING CHANGE:` in commit body
- Author and timestamp

**Analyzes**:
- Work breakdown by type (feat, fix, docs, refactor, etc.)
- Conventional Commits compliance percentage
- Issue correlation (which commits reference which issues)
- Breaking changes count
- Author activity
- Daily commit timeline

**CLI Usage**:
```bash
# Analyze single repository
uv run python workflows/code_analysis/commit_report.py \
  --owner mpazaryna \
  --repo chiro \
  --since 2025-01-01 \
  --correlate-issues

# Daily activity across all repos
uv run python workflows/code_analysis/daily_activity.py --days 1

# Period comparison (this week vs last week)
uv run python workflows/code_analysis/period_comparison.py --days 7
```

**Output**: Reports in `reports/adhoc/` or `reports/daily/`

---

### 12. Velocity Tracking

**Status**: ✅ Implemented

**Description**: Track team velocity and productivity metrics over multiple cycles (weeks/sprints).

**Implementation**: [workflows/metrics/velocity_tracker.py](../../workflows/metrics/velocity_tracker.py)

**Tracks Per Cycle**:
- Commits count
- Issues completed (via issue references in commits)
- Conventional Commits percentage
- Breaking changes
- Contributors
- Work distribution by type
- Daily commit patterns

**Calculates**:
- Average velocity (commits/cycle, issues/cycle)
- Trend indicators (improving, declining, stable)
- Quality metrics (conventional commit %)
- Consistency (variance across cycles)

**CLI Usage**:
```bash
# Last 6 weeks (default)
uv run python workflows/metrics/velocity_tracker.py

# Last 4 two-week sprints
uv run python workflows/metrics/velocity_tracker.py --cycles 4 --cycle-length 14

# Last 12 months
uv run python workflows/metrics/velocity_tracker.py --cycles 12 --cycle-length 30
```

**Output**:
- Markdown report with tables and trend indicators
- JSON data for programmatic access
- Insights (improving velocity, quality trends, consistency)

---

### 13. Roadmap Generation

**Status**: ✅ Implemented

**Description**: Generate roadmap from GitHub milestones with velocity-based completion predictions and visual timeline.

**Implementation**: [workflows/planning/roadmap_generator.py](../../workflows/planning/roadmap_generator.py)

**Features**:
- All milestones with due dates
- Progress tracking (completed/total issues)
- Predicted completion dates based on actual velocity
- Health status (on track, at risk, overdue)
- Visual Mermaid Gantt chart
- Critical milestones requiring attention

**CLI Usage**:
```bash
# Generate roadmap
uv run python workflows/planning/roadmap_generator.py

# Use 60-day velocity sample
uv run python workflows/planning/roadmap_generator.py --velocity-days 60
```

**Output**: Markdown report with Mermaid diagram in `reports/planning/`

---

### 14. AI Repository Comparison

**Status**: ✅ Implemented

**Description**: Use LangChain + Ollama to generate natural language insights comparing repositories.

**Implementation**: [workflows/summarization/repo_comparison.py](../../workflows/summarization/repo_comparison.py)

**Analyzes**:
- Repository focus and patterns
- Key differences between repositories
- Workload distribution insights
- Notable themes and trends

**CLI Usage**:
```bash
# Analyze latest snapshot
uv run python workflows/summarization/repo_comparison.py --model llama3.2
```

**Requirements**: Ollama with LLM model

---

## Dashboard & Visualization

### 15. Interactive Streamlit Dashboard

**Status**: ✅ Implemented

**Description**: Web-based dashboard for visualizing issue data, status flow, and repository activity.

**Implementation**: [workflows/dashboard/app.py](../../workflows/dashboard/app.py)

**Features**:

1. **Snapshot Selection**
   - Load SOD, EOD, or specific date snapshots
   - Sidebar navigation
   - Refresh button

2. **Metrics Overview**
   - Total issues, open/closed counts
   - Active repositories count
   - Snapshot metadata

3. **Status Flow Visualization**
   - 5-stage flow: Backlog → Ready → In Progress → In Review → Done
   - Automatic status extraction from labels
   - Help text for label setup

4. **Tabbed Interface**:
   - **Overview Tab**: Label distribution chart, repository pie chart
   - **Repository Activity Tab**: Detailed repo table with search/filter, drill-down details
   - **Issues Tab**: Full issue list with filtering, pagination

5. **Interactive Features**:
   - Search and filter
   - Repository drill-down
   - Issue expandable cards
   - GitHub links
   - Auto-caching (5 min TTL)

**CLI Usage**:
```bash
# Start dashboard
uv run dashboard start

# Start on custom port
uv run dashboard start --port 8080

# View dashboard status
uv run dashboard status

# View logs
uv run dashboard logs

# Stop dashboard
uv run dashboard stop
```

**Access**: http://localhost:5000 (default)

---

### 16. Dashboard Management CLI

**Status**: ✅ Implemented

**Description**: CLI for managing dashboard lifecycle (start, stop, restart, status, logs).

**Implementation**: [src/github_pm/dashboard_cli.py](../../src/github_pm/dashboard_cli.py), [workflows/dashboard/dashboard_manager.py](../../workflows/dashboard/dashboard_manager.py)

**Commands**:
- `dashboard start` - Start dashboard in background
- `dashboard status` - Check if dashboard is running
- `dashboard logs` - View dashboard logs
- `dashboard logs --follow` - Live log tail
- `dashboard restart` - Restart dashboard
- `dashboard stop` - Stop dashboard

**Features**:
- Background process management
- PID file tracking
- Log file rotation
- Port conflict detection
- Clean shutdown handling

---

## Configuration & Orchestration

### 17. YAML Configuration System

**Status**: ✅ Implemented

**Description**: Flexible YAML-based configuration for collection and workflow settings.

**Implementation**: [config/collection/](../../config/collection/), [config/workflows/](../../config/workflows/)

**Configuration Types**:

1. **Collection Config** (`config/collection/*.yaml`)
   ```yaml
   repositories:
     - owner: org-name
       name: repo-name
   issue_state: open
   limit: 100
   ```

2. **Workflow Config** (`config/workflows/workflow_config.yaml`)
   ```yaml
   trend_analysis:
     significant_change_threshold: 0.20
   anomaly_detection:
     stale_threshold_days: 30
   ```

**Predefined Configs**:
- `production.yaml` - Your repositories (gitignored)
- `testing.yaml` - Small test dataset
- `default.yaml` - Template with examples

---

### 18. Orchestration Scripts

**Status**: ✅ Implemented

**Description**: Shell scripts to simplify common workflows and batch operations.

**Implementation**: [scripts/](../../scripts/)

**Scripts**:

1. **collect.sh** - Data collection wrapper
   ```bash
   ./scripts/collect.sh --production
   ./scripts/collect.sh --testing
   ./scripts/collect.sh --config my-config.yaml --snapshot
   ```

2. **run_workflow.py** - Execute specific workflow
   ```bash
   uv run python scripts/run_workflow.py trend_analysis compare_periods \
     --baseline 2025-11-20_09-30 \
     --current 2025-11-20_14-15
   ```

3. **run_all_workflows.sh** - Run full analysis suite
   ```bash
   ./scripts/run_all_workflows.sh
   ```

---

## Testing Infrastructure

### 19. Pytest Test Suite

**Status**: ✅ Implemented

**Description**: Comprehensive test coverage using pytest with mocking.

**Implementation**: [tests/](../../tests/)

**Test Files**:
- `test_github_client.py` - GitHub CLI wrapper tests
- `test_data_collector.py` - Snapshot system tests
- `test_organizer.py` - Issue organization tests
- `test_report_generator.py` - Report generation tests
- `test_json_exporter.py` - JSON export tests

**Features**:
- Subprocess mocking for GitHub CLI calls
- Fixture data representing GitHub API responses
- Success and error condition testing
- Coverage reporting

**CLI Usage**:
```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=github_pm --cov-report=html

# Specific test file
uv run pytest tests/test_github_client.py -v
```

---

## Summary Statistics

**Total Features Implemented**: 19

**By Category**:
- Data Collection: 6 features
- Workflow Analysis: 8 features
- Dashboard & Visualization: 2 features
- Configuration & Orchestration: 2 features
- Testing Infrastructure: 1 feature

**Key Technologies**:
- Python 3.11+
- GitHub CLI (gh)
- LangChain + Ollama
- Streamlit + Plotly
- pytest

---

[← Back to MOC](./README.md) | [Architecture →](./architecture.md) | [Components →](./components.md)
