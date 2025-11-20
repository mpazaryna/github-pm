---
title: GitHub PM - Component Reference
type: component-moc
generated: 2025-11-20
last_updated: 2025-11-20
project: github-pm
---

# Component Reference

> Detailed documentation of all core components and modules

[← Back to MOC](./README.md)

## Table of Contents

- [Core Collection Components](#core-collection-components)
- [Analyzer Components](#analyzer-components)
- [Workflow Modules](#workflow-modules)
- [Dashboard Components](#dashboard-components)
- [CLI Interfaces](#cli-interfaces)
- [Utilities](#utilities)

---

## Core Collection Components

### GitHubClient

**Location**: [src/github_pm/github_client.py](../../src/github_pm/github_client.py)

**Purpose**: Wrapper for GitHub CLI to fetch issues from repositories

**Key Methods**:

```python
def fetch_issues(
    self,
    owner: str,
    repo: str,
    state: str = "open",
    limit: int = 100,
) -> list[dict[str, Any]]
```

**Implementation Details**:
- Uses `subprocess.run()` to execute `gh issue list` commands
- JSON output format: `--json number,title,state,labels,assignees,milestone,url,createdAt,updatedAt`
- Error handling: Raises `RuntimeError` for CLI failures, `ValueError` for JSON parsing errors
- No caching (intentional - always fetch fresh data)

**Dependencies**:
- External: GitHub CLI (`gh`) must be installed and authenticated
- Internal: None (leaf component)

**Usage Example**:
```python
client = GitHubClient()
issues = client.fetch_issues(owner="mpazaryna", repo="chiro", state="open", limit=100)
```

**Error Handling**:
- `RuntimeError`: GitHub CLI command failed
- `ValueError`: Invalid JSON response from CLI

---

### IssueOrganizer

**Location**: [src/github_pm/organizer.py](../../src/github_pm/organizer.py)

**Purpose**: Organize issues into groups by various criteria

**Key Methods**:

```python
def organize_by_repository(self, issues: list[dict]) -> dict[str, list[dict]]
def organize_by_labels(self, issues: list[dict]) -> dict[str, list[dict]]
def organize_by_milestone(self, issues: list[dict]) -> dict[str, list[dict]]
def organize_by_assignee(self, issues: list[dict]) -> dict[str, list[dict]]
```

**Implementation Details**:

1. **organize_by_repository**:
   - Groups by `issue['repository']` field
   - Repository format: `"owner/repo"`

2. **organize_by_labels**:
   - Issues can appear in multiple groups (has multiple labels)
   - Creates group per unique label
   - Issues without labels go to "No Labels" group

3. **organize_by_milestone**:
   - Groups by `issue['milestone']['title']`
   - Issues without milestone go to "No Milestone" group

4. **organize_by_assignee**:
   - Issues can appear in multiple groups (multiple assignees)
   - Groups by `assignee['login']`
   - Issues without assignees go to "Unassigned" group

**Dependencies**:
- Internal: None
- Uses Python's `defaultdict` for grouping

**Usage Example**:
```python
organizer = IssueOrganizer()
by_repo = organizer.organize_by_repository(all_issues)
by_label = organizer.organize_by_labels(all_issues)
```

---

### DataCollector

**Location**: [src/github_pm/data_collector.py](../../src/github_pm/data_collector.py)

**Purpose**: Manage timestamped snapshots of issue data

**Key Methods**:

```python
def create_snapshot(
    self,
    issues: list[dict[str, Any]],
    organized_data: dict[str, Any],
    config: dict[str, Any],
    label: str = "snapshot",
    date: str | None = None,
) -> Path

def list_snapshots(self, label: str | None = None) -> list[Path]

def load_snapshot(self, snapshot_identifier: Path | str) -> dict[str, Any]
```

**Implementation Details**:

1. **create_snapshot**:
   - Creates timestamped directory or file based on label
   - Filename format: `YYYY-MM-DD-label.json` (e.g., `2025-11-20-sod.json`)
   - Saves complete snapshot with metadata, issues, summary, organized views
   - Updates symlink: `latest-{label}.json` → current snapshot
   - Returns Path to snapshot file

2. **list_snapshots**:
   - Lists all snapshots (or filtered by label)
   - Excludes symlinks from listing
   - Returns sorted list (chronological)

3. **load_snapshot**:
   - Flexible identifier: filename, date-label, or just label (uses latest)
   - Handles symlink resolution
   - Returns complete snapshot dictionary

**Snapshot Structure**:
```json
{
  "metadata": {
    "snapshot_date": "2025-11-20",
    "snapshot_type": "SOD",
    "timestamp": "2025-11-20T09:30:00",
    "generated_by": "github-pm",
    "version": "0.1.0",
    "total_issues": 48,
    "repositories": ["owner/repo1", "owner/repo2"],
    "config": { /* collection config */ }
  },
  "issues": [ /* complete issue array */ ],
  "summary": { /* counts by state, repo, label, etc */ },
  "organized": {
    "by_repository": {},
    "by_labels": {},
    "by_milestone": {},
    "by_assignee": {}
  }
}
```

**Dependencies**:
- Python stdlib: `datetime`, `pathlib`, `json`

---

### MarkdownReportGenerator

**Location**: [src/github_pm/report_generator.py](../../src/github_pm/report_generator.py)

**Purpose**: Generate human-readable markdown reports

**Key Methods**:

```python
def generate_report(
    self,
    organized_issues: dict[str, list[dict]],
    group_by: str = "repository"
) -> str
```

**Implementation Details**:
- Generates markdown with:
  - Header with timestamp
  - Summary statistics
  - Groups with issue details
  - Issue formatting: number, title, state, labels, assignees, milestone, date, URL

**Output Format**:
```markdown
# GitHub Issues Report

**Generated:** 2025-11-20 10:30:00
**Total Issues:** 48
**Total Repositories:** 3

## owner/repo1

### Issue #123: Example Issue Title
- **State:** OPEN
- **Labels:** bug, high-priority
- **Assignees:** @user1
- **Milestone:** v1.0
- **Created:** 2025-11-15
- **URL:** https://github.com/owner/repo1/issues/123
```

**Dependencies**:
- Python stdlib: `datetime`

---

### JSONExporter

**Location**: [src/github_pm/json_exporter.py](../../src/github_pm/json_exporter.py)

**Purpose**: Export structured JSON data with metadata and summaries

**Key Methods**:

```python
def export(
    self,
    issues: list[dict[str, Any]],
    organized: dict[str, Any] | None = None
) -> dict[str, Any]
```

**Implementation Details**:
- Generates comprehensive JSON with:
  - Metadata (timestamp, version, counts)
  - Complete issues array
  - Summary statistics (by state, repo, label, milestone, assignee)
  - All organized views (if provided)

**Output Structure**: See DataCollector snapshot structure

**Dependencies**:
- Python stdlib: `datetime`, `collections.defaultdict`

---

## Analyzer Components

### CommitAnalyzer

**Location**: [src/github_pm/commit_analyzer.py](../../src/github_pm/commit_analyzer.py)

**Purpose**: Analyze commit messages and work patterns

**Key Methods**:

```python
def fetch_commits(
    self, owner: str, repo: str, since: str, until: str, limit: int = 100
) -> list[dict[str, Any]]

def analyze_commits(self, commits: list[dict]) -> dict[str, Any]

def parse_conventional_commit(self, message: str) -> dict[str, Any] | None
```

**Implementation Details**:

1. **fetch_commits**:
   - Uses GitHub CLI: `gh api repos/{owner}/{repo}/commits`
   - Date range filtering via `since` and `until`
   - Returns commit data: sha, message, author, date

2. **analyze_commits**:
   - Parses Conventional Commits format: `type(scope): description`
   - Extracts issue references: `#123`, `fixes #456`, `closes #789`
   - Detects breaking changes: `BREAKING CHANGE:` in body
   - Calculates:
     - Total commits
     - Conventional commits count and percentage
     - Commit types distribution (feat, fix, docs, etc.)
     - Authors activity
     - Issue references
     - Breaking changes
     - Daily commit timeline

3. **parse_conventional_commit**:
   - Regex pattern: `^(feat|fix|docs|style|refactor|perf|test|chore|ci|build)(\(.+?\))?: .+`
   - Extracts type, optional scope, description
   - Returns None for non-conventional commits

**Conventional Commit Types Recognized**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (formatting, no logic change)
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Tests
- `chore`: Maintenance
- `ci`: CI/CD changes
- `build`: Build system changes

**Dependencies**:
- External: GitHub CLI (`gh`)
- Python stdlib: `re`, `subprocess`

---

### StatusAnalyzer

**Location**: [src/github_pm/status_analyzer.py](../../src/github_pm/status_analyzer.py)

**Purpose**: Analyze issue status and workflow health

**Key Methods**:

```python
def extract_status(self, issue: dict[str, Any]) -> str

def analyze_status_distribution(
    self, issues: list[dict[str, Any]]
) -> dict[str, Any]

def analyze_flow_health(
    self, status_distribution: dict[str, Any]
) -> dict[str, Any]

def analyze_milestone_progress(
    self, issues: list[dict[str, Any]]
) -> dict[str, Any]

def get_priority_issues_by_status(
    self, issues: list[dict[str, Any]], status: str, limit: int = 5
) -> list[dict[str, Any]]
```

**Implementation Details**:

1. **extract_status**:
   - Matches issue labels against status patterns (case-insensitive)
   - Falls back to state: OPEN → backlog, CLOSED → done
   - Status patterns defined in `STATUS_PATTERNS` dict

2. **analyze_status_distribution**:
   - Counts issues by status
   - Groups issues by status for later access

3. **analyze_flow_health**:
   - Identifies bottlenecks:
     - Ready pileup: Many ready, few in progress
     - No reviews: Many in progress, none in review
     - Review bottleneck: Too many in review
     - Grooming needed: Many backlog, few ready
   - Calculates WIP (Work In Progress) total
   - Generates recommendations

4. **analyze_milestone_progress**:
   - Groups issues by milestone
   - Calculates progress percentage
   - Estimates needed velocity vs current velocity
   - Assigns health indicator: overdue, at_risk, behind, on_track, good

5. **get_priority_issues_by_status**:
   - Filters by status
   - Sorts by priority score:
     - +100: Has milestone with due date
     - +50: Has priority label (critical, high-priority, urgent, bug)
     - +0 to +30: Recently created (boost for newer issues)

**Status Patterns**:
```python
STATUS_PATTERNS = {
    "backlog": ["backlog", "status:backlog", "status: backlog"],
    "ready": ["ready", "status:ready", "status: ready", "to do", "todo"],
    "in_progress": ["in progress", "status:in progress", "wip", "work in progress"],
    "in_review": ["in review", "status:in review", "review"],
    "done": ["done", "status:done", "completed"]
}
```

**Dependencies**:
- Python stdlib: `collections.Counter`, `collections.defaultdict`, `datetime`

---

## Workflow Modules

### WeeklyPlanner

**Location**: [workflows/planning/weekly_planner.py](../../workflows/planning/weekly_planner.py)

**Purpose**: AI-powered weekly planning with work distribution recommendations

**Key Methods**:

```python
def analyze_last_week(
    self, repos: list[dict[str, str]], days: int = 7
) -> dict[str, Any]

def analyze_current_backlog(
    self, snapshot_data: dict[str, Any]
) -> dict[str, Any]

def generate_plan(
    self,
    last_week_analysis: dict[str, Any],
    backlog_analysis: dict[str, Any],
) -> str

def create_weekly_plan(
    self,
    repos: list[dict[str, str]],
    snapshot_data: dict[str, Any],
    output_path: Path,
    lookback_days: int = 7,
) -> None
```

**Implementation Details**:

1. **analyze_last_week**:
   - Fetches commits for each repo using CommitAnalyzer
   - Calculates commit distribution percentages
   - Identifies work types per repository

2. **analyze_current_backlog**:
   - Loads issues from snapshot
   - Uses StatusAnalyzer for status distribution and flow health
   - Analyzes milestone progress
   - Gets priority issues by status

3. **generate_plan**:
   - Creates LangChain prompt with formatted data
   - Invokes Ollama LLM for analysis
   - Returns AI-generated markdown plan

4. **create_weekly_plan**:
   - Orchestrates all analysis
   - Generates comprehensive report with:
     - Last week's delivery summary
     - Current backlog status
     - Flow health warnings
     - Milestone progress
     - Ready-to-work issues
     - AI-powered recommendations
   - Saves markdown and JSON outputs

**AI Prompt Structure**:
- Input: Last week's work distribution + current backlog
- Requests:
  1. Work distribution analysis
  2. Status flow analysis
  3. Milestone progress review
  4. Recommended distribution for next week
  5. Priority issues to address
  6. Strategic recommendations

**Dependencies**:
- Internal: CommitAnalyzer, StatusAnalyzer
- External: LangChain, Ollama

---

### VelocityTracker

**Location**: [workflows/metrics/velocity_tracker.py](../../workflows/metrics/velocity_tracker.py)

**Purpose**: Track velocity and productivity metrics over multiple cycles

**Key Methods**:

```python
def analyze_cycle(
    self, repos: list[dict], since: str, until: str, cycle_name: str
) -> dict[str, Any]

def generate_velocity_report(
    self, config_path: str, cycles: int = 6, cycle_length: int = 7
) -> dict[str, Any]

def generate_markdown(self, report: dict[str, Any]) -> str
```

**Implementation Details**:

1. **analyze_cycle**:
   - Fetches commits for cycle period using CommitAnalyzer
   - Aggregates metrics across all repositories:
     - Total commits
     - Conventional commits count
     - Issues completed (via references)
     - Breaking changes
     - Work types distribution
     - Contributor activity
     - Daily commit patterns

2. **generate_velocity_report**:
   - Analyzes multiple cycles (sliding windows)
   - Calculates trends (up, down, stable)
   - Computes averages
   - Identifies velocity trends

3. **generate_markdown**:
   - Executive summary with averages
   - Cycle-by-cycle table
   - Trend indicators with emojis
   - Work distribution (recent cycle)
   - Repository activity (recent cycle)
   - Contributors (recent cycle)
   - Insights (quality, consistency, productivity)

**Cycle Naming**:
- 7 days: `W47` (week number)
- 14 days: `Sprint 1`, `Sprint 2`, etc.
- Other: `Cycle 1`, `Cycle 2`, etc.

**Dependencies**:
- Internal: CommitAnalyzer, DataCollector
- External: GitHub CLI (via CommitAnalyzer)

---

### ComparePeriods (Trend Analysis)

**Location**: [workflows/trend_analysis/compare_periods.py](../../workflows/trend_analysis/compare_periods.py)

**Purpose**: Compare two snapshots to identify trends

**Key Methods**:

```python
def compare_snapshots(
    baseline: dict[str, Any],
    current: dict[str, Any]
) -> dict[str, Any]

def generate_insights(comparison: dict[str, Any]) -> list[str]
```

**Implementation Details**:

1. **compare_snapshots**:
   - Compares total counts
   - Analyzes state changes (open/closed)
   - Repository-level changes
   - Label usage changes
   - Milestone changes
   - Assignee workload changes
   - Calculates percentage changes

2. **generate_insights**:
   - Identifies significant changes (> threshold)
   - Generates natural language insights
   - Flags concerning trends

**Dependencies**:
- Internal: DataCollector

---

### RoadmapGenerator

**Location**: [workflows/planning/roadmap_generator.py](../../workflows/planning/roadmap_generator.py)

**Purpose**: Generate roadmap from GitHub milestones with predictions

**Key Methods**:

```python
def estimate_velocity(
    self, repos: list[dict], days: int = 30
) -> float

def predict_completion(
    milestone_data: dict,
    velocity: float
) -> str | None

def generate_roadmap(
    config_path: str,
    velocity_days: int = 30
) -> dict[str, Any]
```

**Implementation Details**:

1. **estimate_velocity**:
   - Analyzes recent commits to calculate current velocity
   - Returns issues/week estimate

2. **predict_completion**:
   - Uses velocity to predict when milestone will complete
   - Considers remaining issues and current pace

3. **generate_roadmap**:
   - Loads latest snapshot
   - Analyzes all milestones
   - Calculates progress and health
   - Predicts completion dates
   - Generates Mermaid Gantt chart
   - Outputs markdown with visual timeline

**Dependencies**:
- Internal: CommitAnalyzer, StatusAnalyzer, DataCollector

---

## Dashboard Components

### Streamlit Dashboard App

**Location**: [workflows/dashboard/app.py](../../workflows/dashboard/app.py)

**Purpose**: Interactive web dashboard for data visualization

**Key Features**:

1. **Snapshot Selection** (sidebar):
   - Radio buttons: Latest SOD, Latest EOD, Select Date
   - Date selectbox
   - Type radio (SOD/EOD)
   - Refresh button

2. **Metrics Overview**:
   - 4-column layout: Total Issues, Open Issues, Active Repos, Snapshot Info
   - 5-column status flow: Backlog, Ready, In Progress, In Review, Done

3. **Tabs**:
   - **Overview**: Label distribution chart, repository pie chart
   - **Repository Activity**: Detailed table, search/filter, drill-down
   - **Issues**: Full issue list with filtering, pagination

**Data Loading**:
```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_snapshot_data(snapshot_id):
    snapshot = data_collector.load_snapshot(snapshot_id)
    return snapshot
```

**Visualizations**:
- Bar chart: Label distribution (top 10)
- Pie chart: Repository distribution (donut chart)
- Table: Repository activity with links
- Expandable cards: Issue details

**Dependencies**:
- External: Streamlit, Plotly, Pandas
- Internal: DataCollector

---

### DashboardManager

**Location**: [workflows/dashboard/dashboard_manager.py](../../workflows/dashboard/dashboard_manager.py)

**Purpose**: Manage dashboard lifecycle (start, stop, status, logs)

**Key Methods**:

```python
def start(
    self, port: int = 5000, sod: bool = False, eod: bool = False
) -> tuple[bool, str]

def stop(self) -> tuple[bool, str]

def status(self) -> tuple[bool, str]

def get_logs(self, follow: bool = False) -> None
```

**Implementation Details**:

1. **start**:
   - Checks if already running (PID file)
   - Optionally runs snapshot collection (SOD/EOD)
   - Starts Streamlit server in background
   - Saves PID to runtime file
   - Returns success/failure

2. **stop**:
   - Reads PID from file
   - Sends SIGTERM to process
   - Cleans up PID file
   - Returns success/failure

3. **status**:
   - Checks if PID file exists
   - Verifies process is running
   - Returns running status

4. **get_logs**:
   - Reads log file
   - Optionally follows (tail -f)

**Runtime Files**:
- PID file: `runtime/dashboard.pid`
- Log file: `runtime/dashboard.log`

**Dependencies**:
- Python stdlib: `subprocess`, `signal`, `os`

---

## CLI Interfaces

### Main CLI

**Location**: [src/github_pm/cli.py](../../src/github_pm/cli.py)

**Purpose**: Main entry point for data collection

**Commands**:

```bash
github-pm [OPTIONS]

Options:
  -c, --config PATH       Config file path (default: config/collection/production.yaml)
  -o, --output PATH       Output file path (default: github-issues-report.md)
  --group-by CHOICE       repository|labels|milestone|assignee (default: repository)
  --format CHOICE         markdown|json|both (default: both)
  --save-snapshot         Save timestamped snapshot
  --label TEXT            Snapshot label (default: snapshot)
```

**Flow**: See [Architecture - Data Flow](./architecture.md#data-flow)

---

### Dashboard CLI

**Location**: [src/github_pm/dashboard_cli.py](../../src/github_pm/dashboard_cli.py)

**Purpose**: Manage dashboard lifecycle

**Commands**:

```bash
dashboard start [--port PORT] [--sod] [--eod]
dashboard stop
dashboard status
dashboard logs [--follow]
dashboard restart
```

**Integration**: Uses DashboardManager for all operations

---

## Utilities

### Configuration Loading

**Pattern**: YAML configuration loader

```python
def load_config(config_path: str) -> dict[str, Any]:
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_file) as f:
        config = yaml.safe_load(f)
    return config
```

**Used By**: CLI, workflows

---

## Component Dependencies Graph

```
┌──────────────┐
│   CLI Entry  │
└──────┬───────┘
       │
┌──────▼───────────────────────────────────────┐
│         Core Collection Layer                 │
│  ┌──────────────┐  ┌──────────────┐         │
│  │GitHubClient  │  │IssueOrganizer│         │
│  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐         │
│  │DataCollector │  │   Reporters  │         │
│  │              │  │ - Markdown   │         │
│  │              │  │ - JSON       │         │
│  └──────────────┘  └──────────────┘         │
└──────┬───────────────────────────────────────┘
       │
┌──────▼───────────────────────────────────────┐
│          Analyzer Layer                       │
│  ┌──────────────┐  ┌──────────────┐         │
│  │CommitAnalyzer│  │StatusAnalyzer│         │
│  └──────────────┘  └──────────────┘         │
└──────┬───────────────────────────────────────┘
       │
┌──────▼───────────────────────────────────────┐
│          Workflow Layer                       │
│  ┌──────────────┐  ┌──────────────┐         │
│  │WeeklyPlanner │  │VelocityTracker│        │
│  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐         │
│  │TrendAnalysis │  │Roadmap Gen   │         │
│  └──────────────┘  └──────────────┘         │
└──────┬───────────────────────────────────────┘
       │
┌──────▼───────────────────────────────────────┐
│       Presentation Layer                      │
│  ┌──────────────┐  ┌──────────────┐         │
│  │   Dashboard  │  │    Reports   │         │
│  │  (Streamlit) │  │  (Markdown)  │         │
│  └──────────────┘  └──────────────┘         │
└───────────────────────────────────────────────┘
```

---

## Quick Reference

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| GitHubClient | github_client.py | Fetch issues via gh CLI |
| IssueOrganizer | organizer.py | Group issues by criteria |
| DataCollector | data_collector.py | Manage snapshots |
| MarkdownReportGenerator | report_generator.py | Generate markdown |
| JSONExporter | json_exporter.py | Export JSON |

### Analyzers

| Component | File | Purpose |
|-----------|------|---------|
| CommitAnalyzer | commit_analyzer.py | Analyze commits |
| StatusAnalyzer | status_analyzer.py | Analyze workflow status |

### Workflows

| Component | File | Purpose |
|-----------|------|---------|
| WeeklyPlanner | planning/weekly_planner.py | AI-powered planning |
| VelocityTracker | metrics/velocity_tracker.py | Track velocity |
| ComparePeriods | trend_analysis/compare_periods.py | Trend analysis |
| RoadmapGenerator | planning/roadmap_generator.py | Generate roadmap |

### Dashboard

| Component | File | Purpose |
|-----------|------|---------|
| Dashboard App | dashboard/app.py | Streamlit UI |
| DashboardManager | dashboard/dashboard_manager.py | Lifecycle management |
| Dashboard CLI | dashboard_cli.py | CLI interface |

---

[← Back to MOC](./README.md) | [← Features](./features.md) | [← Architecture](./architecture.md)
