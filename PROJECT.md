# GitHub PM - Project Portfolio

## Elevator Pitch
A Python CLI tool that transforms scattered GitHub issues across multiple repositories into actionable intelligence through automated snapshots, AI-powered analysis, and real-time dashboards. Built for engineering managers and solo developers who need to track work across multiple projects without manual aggregation.

## Context & Problem
Managing multiple GitHub repositories creates visibility gaps - issues are scattered, trends are hidden, and status reporting requires manual aggregation. Traditional project management tools add overhead, while GitHub's native interface doesn't aggregate across repositories. Engineering managers and solo developers need a lightweight way to track work distribution, identify bottlenecks, and maintain velocity without context-switching between repositories.

## Solution & Approach
Built a two-phase system: (1) Regular timestamped snapshots of GitHub issues stored as structured datasets, and (2) Agentic workflows that process snapshots to generate insights. The system uses GitHub CLI as the data source, eliminates external dependencies, and provides both real-time dashboards and automated SOD/EOD workflows. AI-powered analysis (via LangChain + Ollama) provides natural language recommendations for work balancing and planning.

## Technical Implementation

### Architecture
- **Data Collection Pipeline**: GitHubClient wraps `gh` CLI, IssueOrganizer provides multiple grouping strategies, DataCollector manages timestamped snapshots with symlinks
- **Workflow System**: Modular workflows in `workflows/` for trend analysis, code analysis, planning, metrics, and summarization
- **Dashboard**: Streamlit-based real-time dashboard with process manager (background daemon, log management, auto-restart)
- **Status Tracking**: StatusAnalyzer extracts workflow state from labels, identifies bottlenecks, calculates milestone health

### Technology Stack
- **Core**: Python 3.11+, subprocess for GitHub CLI integration, python-dateutil for time handling
- **Data**: YAML configs, JSON snapshots, markdown reports
- **AI/ML**: LangChain + Ollama (local LLM) for AI-powered analysis
- **Dashboard**: Streamlit with 5-minute cache TTL, background process management
- **Testing**: pytest, pytest-mock, pytest-cov
- **Orchestration**: Bash scripts, CLI commands, workflow runners

### Key Design Decisions
1. **Timestamped Snapshots**: Immutable historical data enables trend analysis without external databases
2. **GitHub CLI Integration**: Leverages existing authentication, avoids API tokens, respects rate limits
3. **Multiple Organization Views**: JSON exports include all grouping strategies regardless of CLI selection
4. **Local LLM**: Uses Ollama for privacy-preserving AI analysis without cloud dependencies
5. **Process Manager Pattern**: Dashboard runs as background daemon with logs, PID files, and graceful shutdown

## Key Features
- **Automated SOD/EOD Workflows**: Morning snapshot + dashboard start, evening snapshot + summary + dashboard stop
- **Multi-Repository Aggregation**: Collect issues from unlimited repositories with single command
- **Flexible Organization**: Group by repository, labels, milestone, or assignee
- **Trend Analysis**: Compare snapshots to identify significant changes over time
- **AI-Powered Planning**: Weekly planner analyzes work distribution and recommends balanced approach
- **Velocity Tracking**: Track issues completed per cycle, commit volume trends, code quality metrics
- **Roadmap Generation**: Visual roadmap from GitHub milestones with predicted completion dates
- **Real-Time Dashboard**: Streamlit dashboard with period comparison, velocity trends, repository activity
- **Commit Analysis**: Parse Conventional Commits, correlate with issues, track breaking changes

## Outcomes & Metrics
- **Time Savings**: Reduces status report preparation from 30+ minutes to < 2 minutes via automated workflows
- **Visibility**: Aggregates 5+ repositories into single view, eliminating context-switching
- **Velocity Insights**: 6-week velocity tracking identifies trends, predicts milestone completion
- **Flow Optimization**: Automated bottleneck detection (ready pileup, review bottleneck, WIP overload)
- **Code Quality**: Conventional Commits tracking shows 70%+ adherence in analyzed repositories
- **Adoption**: Personal productivity tool used daily for multi-project management

## Technical Challenges & Solutions

### Challenge 1: Snapshot Management Without Database
**Problem**: Needed historical data for trend analysis without adding database dependency
**Solution**: Implemented timestamped directory structure with symlinks and metadata JSON for fast lookups

### Challenge 2: Process Management for Dashboard
**Problem**: Streamlit runs in foreground; needed background daemon with log management
**Solution**: Built process manager with PID files, graceful shutdown (SIGTERM → SIGKILL), log rotation

### Challenge 3: Cross-Repository Status Tracking
**Problem**: GitHub lacks standardized status labels across repositories
**Solution**: Flexible pattern matching for status extraction, falls back to issue state if labels missing

### Challenge 4: AI Analysis Privacy
**Problem**: Cloud LLM APIs expose project data and require API tokens
**Solution**: Integrated Ollama for local LLM inference, zero external dependencies for AI features

### Challenge 5: Workflow Discoverability
**Problem**: Too many workflows and flags led to poor user experience
**Solution**: Built orchestration scripts with sensible defaults, created comprehensive quick reference guide

## Learnings & Growth
- **Agentic Architecture**: Learned to design systems with autonomous agents rather than monolithic scripts
- **CLI UX Design**: Discovered that orchestration scripts > complex flag combinations for user experience
- **Snapshot Pattern**: Immutable timestamped data simplifies workflow development and debugging
- **Local-First AI**: Ollama integration proved that local LLMs are viable for development tools
- **Process Lifecycle**: Deepened understanding of Unix process management, signals, and daemon patterns

## Future Enhancements
- **Anomaly Detection**: Identify unusual patterns (sudden issue spikes, stale work, contributor churn)
- **Custom Reports**: Stakeholder-specific views (executive summary, team burndown, sprint report)
- **Webhook Integration**: Real-time updates via GitHub webhooks instead of polling
- **Multi-User Support**: Team dashboard with aggregated views across multiple users' repositories
- **Export Formats**: PDF reports, CSV exports, API endpoint for external integrations

## Project Links
- **Repository**: [github.com/mpazaryna/github-pm](https://github.com/mpazaryna/github-pm) *(update with actual link)*
- **Documentation**: See `CLAUDE.md`, `docs/AGENTIC_VISION.md`, `docs/DASHBOARD.md`
- **Quick Reference**: See `guide-to-using.md`

## Tags
`python` `cli` `github-api` `project-management` `data-analysis` `ai` `llm` `streamlit` `dashboard` `automation` `agentic-workflows` `engineering-management`

## Portfolio Use Cases
- **Resume Project Description**: Use "Elevator Pitch" + "Outcomes & Metrics" + "Technology Stack"
- **Technical Interview**: Reference "Technical Challenges & Solutions" for system design discussions
- **Portfolio Website**: Use "Context & Problem" + "Solution & Approach" + "Key Features"
- **LinkedIn Project**: Use "Elevator Pitch" + subset of "Key Features" + "Tags"
- **GitHub Profile**: Link to this PROJECT.md with "Elevator Pitch" as preview text
