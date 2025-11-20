---
title: GitHub PM - Architecture Overview
type: architecture-moc
generated: 2025-11-20
last_updated: 2025-11-20
project: github-pm
---

# Architecture Overview

> System design, architectural decisions, and design patterns

[← Back to MOC](./README.md)

## Table of Contents

- [System Architecture](#system-architecture)
- [Design Principles](#design-principles)
- [Data Flow](#data-flow)
- [Architectural Decisions](#architectural-decisions)
- [Technology Stack Rationale](#technology-stack-rationale)
- [Extension Points](#extension-points)

---

## System Architecture

### Two-Phase Architecture

GitHub PM uses a **separation of concerns** approach with two distinct phases:

```
┌─────────────────────────────────────────────────────────────┐
│                     PHASE 1: COLLECTION                      │
│                                                              │
│  Config YAML → GitHubClient → Issues → Organizer → Snapshot │
│                                    ↓                         │
│                            DataCollector                     │
│                                    ↓                         │
│                        data/YYYY-MM-DD_HH-MM-SS/            │
│                                    ↓                         │
│                      Reports (markdown/JSON)                 │
└─────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────┐
│                     PHASE 2: ANALYSIS                        │
│                                                              │
│  Snapshots → Workflows → Analysis → reports/                │
│                                                              │
│  Workflows:                                                  │
│  ├─ Trend Analysis (compare_periods.py)                     │
│  ├─ AI Planning (weekly_planner.py)                         │
│  ├─ Commit Analysis (commit_report.py, daily_activity.py)   │
│  ├─ Velocity Tracking (velocity_tracker.py)                 │
│  ├─ Roadmap Generation (roadmap_generator.py)               │
│  └─ Dashboard (app.py)                                       │
└─────────────────────────────────────────────────────────────┘
```

**Why This Separation?**

1. **Decoupling**: Collection can run without analysis, analysis can run without new collection
2. **Historical Analysis**: Multiple snapshots enable trend tracking
3. **Flexibility**: Add new workflows without touching collection code
4. **Reliability**: Collection failures don't break analysis, analysis failures don't break collection
5. **Performance**: Heavy analysis (AI, commits) doesn't block basic reporting

---

## Design Principles

### 1. Immutable Snapshots

**Decision**: Once created, snapshot files are never modified.

**Rationale**:
- Enables reliable trend analysis (data won't change under you)
- Simplifies concurrent access (no locking needed)
- Historical record is preserved
- Easy to reason about data at any point in time

**Implementation**: [src/github_pm/data_collector.py:22](../../src/github_pm/data_collector.py)

**Trade-off**: Storage grows over time (mitigated by keeping only recent snapshots)

---

### 2. All Organization Views Pre-Computed

**Decision**: During collection, compute ALL organization strategies (by repo, label, milestone, assignee), not just the one requested.

**Rationale**:
- JSON export is complete and self-contained
- Workflows can use any organization view without re-processing
- Minimal overhead (grouping is cheap compared to API calls)
- Enables flexible analysis without re-collection

**Implementation**: [src/github_pm/cli.py:151](../../src/github_pm/cli.py)

**Trade-off**: Slightly larger snapshot files (acceptable for the flexibility gained)

---

### 3. Local-First with Optional Cloud Integration

**Decision**: Everything runs locally by default. External services (GitHub, Ollama) are opt-in.

**Rationale**:
- Privacy: Your data stays on your machine
- Cost: $0 for core functionality
- Control: No vendor lock-in
- Speed: No network latency for analysis
- Reliability: Works offline for analysis

**Implementation**:
- Core collection: GitHub CLI (already authenticated)
- AI features: Local Ollama (user installs)
- No cloud databases, no SaaS dependencies

**Trade-off**: User must install and configure tools (GitHub CLI, Ollama)

---

### 4. Markdown + JSON Dual Output

**Decision**: Always generate both human-readable markdown and machine-readable JSON.

**Rationale**:
- Markdown: Perfect for reports, documentation, GitHub rendering
- JSON: Perfect for dashboards, automation, programmatic access
- Both generated from same data (consistency guaranteed)
- Minimal overhead (generation is fast)

**Implementation**: [src/github_pm/cli.py:162](../../src/github_pm/cli.py)

---

### 5. AI as Assistant, Not Autonomous Agent (Yet)

**Decision**: AI provides recommendations, humans make decisions.

**Rationale**:
- Current phase: Human reviews AI plan, decides actions
- Reduces risk of AI making bad decisions
- Builds trust through transparency
- Enables gradual autonomy increase

**Future Path**:
- Phase 2: Semi-autonomous (AI creates draft issues, auto-assigns)
- Phase 3: Fully autonomous (AI manages entire sprint)

**Implementation**: [workflows/planning/weekly_planner.py](../../workflows/planning/weekly_planner.py)

---

### 6. Status Labels as Optional Enhancement

**Decision**: Status flow analysis works without labels but is enhanced with them.

**Rationale**:
- Default: Open issues = backlog, closed = done (works out of box)
- With labels: Full flow tracking (backlog → ready → in progress → in review → done)
- Progressive enhancement: Users can adopt gradually
- No forced process change on teams

**Implementation**: [src/github_pm/status_analyzer.py:34](../../src/github_pm/status_analyzer.py)

**Patterns Recognized**:
```python
STATUS_PATTERNS = {
    "backlog": ["backlog", "status:backlog"],
    "ready": ["ready", "status:ready", "todo"],
    "in_progress": ["in progress", "wip", "work in progress"],
    "in_review": ["in review", "review"],
    "done": ["done", "completed"]
}
```

---

## Data Flow

### Collection Flow (Detailed)

```
1. CLI Entry Point (cli.py:main)
   ↓
2. Load YAML Config (cli.py:load_config)
   - Repositories list
   - Issue state filter
   - Limit per repo
   ↓
3. Initialize Clients
   - GitHubClient (github_client.py)
   - IssueOrganizer (organizer.py)
   - MarkdownReportGenerator (report_generator.py)
   - JSONExporter (json_exporter.py)
   - DataCollector (data_collector.py)
   ↓
4. Fetch Issues Loop (cli.py:102)
   For each repository:
     - GitHubClient.fetch_issues()
       ↓ subprocess.run(['gh', 'issue', 'list', ...])
       ↓ Parse JSON response
       ↓ Add 'repository' field to each issue
     - Append to all_issues list
   Error handling: Log and continue on failure
   ↓
5. Organize Issues (cli.py:136)
   - IssueOrganizer.organize_by_*()
   - Create groups based on --group-by flag
   ↓
6. Optional: Save Snapshot (cli.py:148)
   If --save-snapshot flag:
     - Organize by ALL strategies (not just selected)
     - DataCollector.create_snapshot()
       ↓ Create timestamped directory
       ↓ Save raw.json with complete data
       ↓ Save metadata.json for quick access
       ↓ Update 'latest' symlink
   ↓
7. Generate Outputs (cli.py:166)
   - Markdown: MarkdownReportGenerator.generate_report()
   - JSON: JSONExporter.export()
   - Save to disk
   ↓
8. Success
```

### Workflow Analysis Flow

```
1. Workflow Script Entry Point
   ↓
2. Load Snapshot(s)
   - DataCollector.list_snapshots()
   - DataCollector.load_snapshot()
   ↓
3. Analysis Logic
   Examples:
   - Trend: Compare two snapshots
   - Planning: Analyze commits + backlog
   - Velocity: Analyze multiple cycles
   ↓
4. Generate Insights
   - Calculations
   - Comparisons
   - Optional: AI processing (LangChain + Ollama)
   ↓
5. Create Report
   - Markdown formatting
   - JSON data export
   - Save to reports/ directory
   ↓
6. Output
```

---

## Architectural Decisions

### Decision 1: Use GitHub CLI Instead of PyGithub/Octokit

**Context**: Need to fetch GitHub issues from multiple repositories.

**Options Considered**:
1. PyGithub (Python SDK for GitHub API)
2. GitHub CLI (gh) via subprocess
3. Direct REST API calls

**Decision**: Use GitHub CLI via subprocess

**Rationale**:
- Pros:
  - User already has gh installed and authenticated
  - No need to manage API tokens in code
  - Rate limiting handled by gh CLI
  - Consistent with user's GitHub setup
  - JSON output is well-structured
- Cons:
  - Subprocess overhead (minimal for use case)
  - Dependency on external tool

**Implementation**: [src/github_pm/github_client.py:11](../../src/github_pm/github_client.py)

**Result**: Clean, simple integration with zero authentication setup

---

### Decision 2: Timestamped Directories vs Database

**Context**: Need to store historical snapshots for trend analysis.

**Options Considered**:
1. SQLite database
2. Timestamped directories with JSON files
3. Single JSON file with versioning

**Decision**: Timestamped directories with JSON files

**Rationale**:
- Pros:
  - Simple to understand (just files)
  - No database setup required
  - Easy to inspect/debug (cat raw.json)
  - Immutable by design
  - Git-friendly (can commit snapshots)
  - Easy cleanup (rm -rf old directories)
- Cons:
  - Slower than database for complex queries (not needed)
  - More disk space (acceptable)

**Implementation**: [src/github_pm/data_collector.py](../../src/github_pm/data_collector.py)

**Result**: Zero-configuration, reliable storage that's easy to work with

---

### Decision 3: LangChain + Ollama vs OpenAI

**Context**: Need AI-powered analysis for weekly planning.

**Options Considered**:
1. OpenAI API (GPT-4)
2. Anthropic API (Claude)
3. LangChain + Ollama (local LLMs)

**Decision**: LangChain + Ollama

**Rationale**:
- Pros:
  - Local execution (privacy, no API costs)
  - No API keys to manage
  - Works offline
  - LangChain provides abstraction for future model swaps
  - Ollama is easy to install and use
- Cons:
  - Requires user to install Ollama
  - Slower than cloud APIs (on CPU)
  - Model quality varies

**Implementation**: [workflows/planning/weekly_planner.py:28](../../workflows/planning/weekly_planner.py)

**Result**: $0 cost, private, extensible AI analysis

---

### Decision 4: Streamlit for Dashboard vs Custom React

**Context**: Need interactive dashboard for visualizing data.

**Options Considered**:
1. Custom React/Next.js app
2. Streamlit (Python-native)
3. Flask + Jinja templates
4. Static HTML with JavaScript

**Decision**: Streamlit

**Rationale**:
- Pros:
  - Pure Python (no JS/HTML/CSS)
  - Built-in widgets and charts
  - Hot reload during development
  - Auto-caching
  - Easy to deploy
  - Great for data apps
- Cons:
  - Less control over UI
  - Heavier than static HTML
  - Python-only (no separate frontend team)

**Implementation**: [workflows/dashboard/app.py](../../workflows/dashboard/app.py)

**Result**: Rapid dashboard development with professional UI

---

### Decision 5: Workflow Scripts vs Monolithic CLI

**Context**: Need multiple analysis workflows with different inputs/outputs.

**Options Considered**:
1. Extend main CLI with subcommands (click/typer)
2. Separate workflow scripts in workflows/ directory
3. Plugin system

**Decision**: Separate workflow scripts

**Rationale**:
- Pros:
  - Clear separation of concerns
  - Easy to add new workflows (just add script)
  - Each workflow can have custom flags
  - No bloat in main CLI
  - Easier to test individually
- Cons:
  - Multiple entry points (mitigated by orchestration scripts)

**Implementation**: [workflows/](../../workflows/) directory structure

**Result**: Flexible, extensible workflow system

---

## Technology Stack Rationale

### Core Technologies

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| **Python 3.11+** | Language | Modern syntax, type hints, great ecosystem |
| **uv** | Package manager | Fast, reliable, better than pip/pipenv |
| **GitHub CLI (gh)** | Data source | User already has it, handles auth |
| **YAML** | Configuration | Human-readable, well-supported |
| **JSON** | Data format | Universal, structured, easy to parse |
| **Markdown** | Reports | GitHub-native, human-readable |

### AI/ML Stack

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| **LangChain** | LLM abstraction | Model-agnostic, prompt management |
| **Ollama** | Local LLM runtime | Free, private, easy to use |
| **llama3.2** | Default model | Good quality/speed balance |

### Dashboard Stack

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| **Streamlit** | Web framework | Pure Python, rapid development |
| **Plotly** | Charts | Interactive, professional |
| **Pandas** | Data manipulation | Standard for data analysis |

### Testing Stack

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| **pytest** | Test framework | Standard, powerful, plugins |
| **pytest-mock** | Mocking | Subprocess mocking for gh CLI |
| **pytest-cov** | Coverage | Track test coverage |

---

## Extension Points

### Adding New Workflows

**Pattern**: Create new script in `workflows/<category>/`

```python
# workflows/custom/my_workflow.py
from github_pm.data_collector import DataCollector

def analyze(snapshot_data):
    # Your custom analysis
    pass

def main():
    collector = DataCollector()
    data = collector.load_snapshot('latest')
    results = analyze(data)
    # Save report
    pass

if __name__ == "__main__":
    main()
```

**Integration**: Add to `scripts/run_all_workflows.sh`

---

### Adding New Organization Strategies

**Pattern**: Add method to `IssueOrganizer`

```python
# src/github_pm/organizer.py
def organize_by_priority(self, issues):
    organized = {}
    for issue in issues:
        priority = self._extract_priority(issue)
        organized.setdefault(priority, []).append(issue)
    return organized
```

**Integration**: Add to CLI `--group-by` choices and JSON export

---

### Adding New Analyzers

**Pattern**: Create new analyzer class

```python
# src/github_pm/custom_analyzer.py
class CustomAnalyzer:
    def analyze(self, issues):
        # Your analysis logic
        return results
```

**Integration**: Use in workflows as needed

---

### Adding New AI Models

**Pattern**: Swap Ollama model

```python
# workflows/planning/weekly_planner.py
llm = OllamaLLM(model="mistral")  # or any Ollama model
```

Or extend for OpenAI:

```python
from langchain_openai import OpenAI
llm = OpenAI(model="gpt-4", api_key=os.environ["OPENAI_API_KEY"])
```

---

## Future Architecture Considerations

### Planned Enhancements

1. **Plugin System** - Load custom workflows dynamically
2. **Real-time Updates** - Webhook-based snapshot updates
3. **Multi-user Support** - Team dashboards with auth
4. **Cloud Sync** - Optional backup to S3/GCS
5. **Advanced AI** - Fine-tuned models for project management

### Scalability Notes

**Current Design**:
- Optimized for 5-20 repositories
- Handles hundreds of issues per repo
- Snapshots kept for 30-90 days typically

**If Scaling Needed**:
- Use database (PostgreSQL) instead of JSON files
- Add Redis for caching
- Implement pagination in dashboard
- Optimize snapshot cleanup

---

## Diagrams

### System Context Diagram

```
┌─────────────┐
│   GitHub    │ ← Issues, Commits
└─────┬───────┘
      │ via gh CLI
┌─────▼───────────────────────────────────────┐
│          GitHub PM (Local)                   │
│                                              │
│  ┌──────────────┐      ┌──────────────┐    │
│  │ Collection   │──→   │  Snapshots   │    │
│  │  Pipeline    │      │  (data/)     │    │
│  └──────────────┘      └──────┬───────┘    │
│                               │             │
│  ┌──────────────┐      ┌──────▼───────┐    │
│  │  Workflows   │──→   │   Reports    │    │
│  │  (Analysis)  │      │  (reports/)  │    │
│  └──────────────┘      └──────────────┘    │
│                                              │
│  ┌──────────────┐                           │
│  │  Dashboard   │ ← http://localhost:5000   │
│  │ (Streamlit)  │                           │
│  └──────────────┘                           │
└──────────────────────────────────────────────┘
      │
┌─────▼───────┐
│   Ollama    │ ← Local LLM (optional)
│  (AI/ML)    │
└─────────────┘
```

---

[← Back to MOC](./README.md) | [← Features](./features.md) | [Components →](./components.md)
