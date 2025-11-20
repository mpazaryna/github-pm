---
title: GitHub PM - Project Map of Content
type: moc
generated: 2025-11-20
last_updated: 2025-11-20
project: github-pm
version: 0.1.0
---

# GitHub PM - Map of Content

> **Autonomous multi-project management powered by AI**
>
> A Python CLI tool that aggregates GitHub issues and commits across multiple repositories, generating comprehensive reports and AI-powered insights for project planning, trend analysis, and work distribution.

## Quick Navigation

- [Features Documentation](./features.md) - Complete catalog of implemented features
- [Architecture Overview](./architecture.md) - System design and decision history
- [Component Reference](./components.md) - Detailed component documentation

## Project Overview

**GitHub PM** is an agentic project management tool designed for small teams (1-2 developers) managing multiple concurrent repositories. It combines data collection, historical tracking, and AI-powered analysis to provide actionable insights for balanced work distribution.

### Key Capabilities

1. **Data Collection Pipeline**
   - Fetch issues from multiple GitHub repositories via GitHub CLI
   - Create timestamped snapshots for historical tracking
   - Export to markdown reports and structured JSON
   - Organize by repository, labels, milestones, or assignees

2. **Agentic Workflow System**
   - Trend analysis comparing snapshots over time
   - AI-powered weekly planning with work distribution recommendations
   - Commit analysis tracking actual delivery vs planned work
   - Velocity tracking across multiple cycles
   - Status flow analysis identifying bottlenecks

3. **Interactive Dashboard**
   - Streamlit-based web dashboard
   - Real-time metrics with visual charts
   - Repository drill-down with filtering
   - SOD/EOD snapshot support

4. **Work Stream Management**
   - Balance work across 3-5 concurrent projects
   - Detect neglected repositories
   - Recommend priority issues
   - Track milestone progress and health

## Technology Stack

- **Language**: Python 3.11+
- **Package Manager**: uv
- **CLI Integration**: GitHub CLI (gh)
- **AI/ML**: LangChain + Ollama (local LLM inference)
- **Dashboard**: Streamlit + Plotly
- **Data Formats**: YAML (config), JSON (data), Markdown (reports)
- **Testing**: pytest with pytest-cov and pytest-mock

## Getting Started

### Installation

```bash
# Install dependencies
uv sync

# Install package in editable mode
uv pip install -e .
```

### Quick Start

```bash
# 1. Collect data from your repositories
uv run dashboard start --sod

# 2. View the dashboard
# Opens at http://localhost:5000

# 3. Generate AI-powered weekly plan
uv run python workflows/planning/weekly_planner.py
```

## Documentation Structure

### [Features](./features.md)

Complete catalog of all implemented features organized by category:

- Data collection and snapshot management
- Workflow analysis (trend, commit, velocity, planning)
- Dashboard and visualization
- Configuration and orchestration
- Testing infrastructure

### [Architecture](./architecture.md)

System design, architectural decisions, and design patterns:

- Two-phase architecture (collection + analysis)
- Data flow and pipeline design
- Snapshot system and immutability
- AI/LLM integration approach
- Status flow and milestone tracking
- Technology choices and rationale

### [Component Reference](./components.md)

Detailed documentation of all core components:

- Core collection components (GitHubClient, DataCollector, etc.)
- Analyzer components (CommitAnalyzer, StatusAnalyzer)
- Workflow modules (planning, metrics, visualization)
- CLI and dashboard interfaces
- Configuration management

## Use Cases

### Solo Developer Managing Multiple Projects

**Problem**: Juggling 3 personal projects, losing track of what needs attention

**Solution**:
- Weekly snapshots track all repositories
- AI planner identifies neglected projects
- Dashboard provides at-a-glance status

### Small Team Sprint Planning

**Problem**: Need data-driven sprint planning across concurrent work streams

**Solution**:
- Velocity tracking shows team capacity
- Status flow analysis identifies bottlenecks
- AI recommends work distribution percentages
- Milestone tracking flags at-risk deadlines

### Engineering Manager Reporting

**Problem**: Need weekly status updates for stakeholders across multiple projects

**Solution**:
- Commit analysis shows actual delivery
- Period comparison highlights trends
- Markdown reports are stakeholder-ready
- JSON export feeds other tools

## Key Design Principles

1. **Immutable Snapshots** - Historical data never changes, enabling reliable trend analysis
2. **Separation of Concerns** - Collection phase separate from analysis workflows
3. **Local-First** - Runs entirely on your machine, no cloud dependencies
4. **AI-Augmented** - Humans make decisions, AI provides recommendations
5. **Zero Process Overhead** - Uses existing GitHub data, no new workflow for team
6. **Extensible** - Workflow system allows custom analysis without modifying core

## Project Structure

```
github-pm/
├── src/github_pm/          # Core collection modules
├── workflows/              # Analysis workflows (trend, planning, metrics)
├── config/                 # YAML configurations
├── data/                   # Timestamped snapshots
├── reports/                # Generated analysis reports
├── scripts/                # Orchestration scripts
├── tests/                  # Pytest test suite
└── docs/                   # Documentation
    ├── moc/               # This MOC documentation
    ├── AGENTIC_VISION.md  # Vision and principles
    ├── DASHBOARD.md       # Dashboard guide
    └── *.md               # Other guides
```

## External Documentation

- [Main README](../../README.md) - Installation and basic usage
- [Agentic Vision](../AGENTIC_VISION.md) - Philosophy and future roadmap
- [Dashboard Guide](../DASHBOARD.md) - Dashboard features and commands
- [Engineering Manager Guide](../ENGINEERING_MANAGER_GUIDE.md) - Manager-focused usage
- [Multi-Agent Workflow](../MULTI_AGENT_WORKFLOW.md) - Workflow coordination patterns

## Development Status

**Current Version**: 0.1.0

**Implemented**:
- ✅ Data collection pipeline with snapshot system
- ✅ Trend analysis comparing time periods
- ✅ AI-powered weekly planning with LangChain + Ollama
- ✅ Commit analysis with Conventional Commits parsing
- ✅ Velocity tracking over multiple cycles
- ✅ Status flow analysis and milestone tracking
- ✅ Interactive Streamlit dashboard
- ✅ SOD/EOD snapshot workflow
- ✅ Roadmap generation from milestones

**In Progress**:
- 🚧 Portfolio system for cross-project insights
- 🚧 Enhanced dashboard tabs

**Planned**:
- 📋 Anomaly detection workflow
- 📋 Custom stakeholder reports
- 📋 Automated issue grooming suggestions
- 📋 Sprint issue auto-creation

## Contributing

This is currently a personal project. For questions or suggestions, see the GitHub repository.

## License

MIT License - See LICENSE file for details

---

**Last Updated**: 2025-11-20
**Project**: github-pm v0.1.0
**Documentation**: [Features](./features.md) | [Architecture](./architecture.md) | [Components](./components.md)
