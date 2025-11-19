# GitHub PM Quick Reference Guide

## Dashboard Management

### Start Dashboard
```bash
# Basic start (reads from latest snapshot)
uv run dashboard start

# Start on custom port
uv run dashboard start --port 8080

# Start with SOD snapshot collection
uv run dashboard start --sod
```
Starts the Streamlit dashboard server in the background. Optionally collects a Start of Day (SOD) snapshot before starting. Dashboard runs at http://localhost:5000 by default.

### Stop Dashboard
```bash
uv run dashboard stop
```
Gracefully stops the running dashboard server. Attempts SIGTERM first, then SIGKILL if needed.

### Restart Dashboard
```bash
uv run dashboard restart

# Restart on custom port
uv run dashboard restart --port 8080
```
Stops and starts the dashboard server. Useful after configuration changes or system updates.

### Check Status
```bash
uv run dashboard status
```
Shows whether dashboard is running, its PID, URL, and log file location. Displays port information if dashboard is active.

### View Logs
```bash
# Last 50 lines (default)
uv run dashboard logs

# Last 100 lines
uv run dashboard logs --lines 100

# Follow logs (live tail)
uv run dashboard logs --follow
```
Displays dashboard server logs. Use `--follow` to watch logs in real-time (Ctrl+C to exit).

## SOD/EOD Workflows

### Start of Day (SOD)
```bash
# Collect SOD snapshot and start dashboard
uv run dashboard start --sod
```
Collects a morning snapshot labeled "sod", then starts the dashboard. Use this at the beginning of your workday to capture baseline state.

### End of Day (EOD)
```bash
# Complete EOD workflow
uv run dashboard eod
```
Runs full End of Day workflow: collects EOD snapshot labeled "eod", generates daily summary report, and stops dashboard. Use this at end of workday for automated wrap-up.

## Snapshot Collection

### Manual Snapshots
```bash
# Collect snapshot with default label
uv run github-pm --save-snapshot

# Collect snapshot with custom label
uv run github-pm --save-snapshot --label milestone-review

# Collect SOD snapshot (manual)
uv run github-pm --save-snapshot --label sod

# Collect EOD snapshot (manual)
uv run github-pm --save-snapshot --label eod
```
Saves timestamped snapshot to `data/YYYY-MM-DD_HH-MM-SS/` directory. Label is stored in metadata for filtering and identification.

### List Snapshots
```bash
# List all snapshots
uv run python -c "from src.github_pm.data_collector import DataCollector; dc = DataCollector(); print('\n'.join([f'{s[\"timestamp\"]} - {s.get(\"label\", \"unlabeled\")}' for s in dc.list_snapshots()]))"

# Count snapshots
ls -1 data/ | grep -E '^[0-9]{4}-' | wc -l
```
Shows all collected snapshots with timestamps and labels. Use for reviewing snapshot history or finding specific snapshots for comparison.

### Load Specific Snapshot
```bash
# Load snapshot by timestamp
uv run python -c "from src.github_pm.data_collector import DataCollector; import json; dc = DataCollector(); data = dc.load_snapshot('2025-01-17_09-30'); print(json.dumps(data['metadata'], indent=2))"
```
Loads a specific snapshot for inspection or analysis. Replace timestamp with actual snapshot directory name.

## Repository Management

### Sync Repositories from GitHub
```bash
# Generate config by fetching all repos
uv run python scripts/sync_repos.py

# Preview without writing
uv run python scripts/sync_repos.py --dry-run

# Show statistics only
uv run python scripts/sync_repos.py --stats

# Write to custom output file
uv run python scripts/sync_repos.py --output config/collection/custom.yaml
```
Dynamically fetches all repositories from GitHub using `gh` CLI and applies filters from `config/collection/repo_filters.yaml`. Automatically excludes forks and archived repos by default, supports topic/language filtering, and allows manual overrides.

### Configure Repository Filters
```bash
# Edit filter preferences
vim config/collection/repo_filters.yaml

# Or use preferred editor
code config/collection/repo_filters.yaml
```
Configure which repos to include/exclude by setting filters for forks, archived status, visibility, topics, languages, and age. Add force_include/force_exclude lists for manual overrides.

## Data Collection

### Basic Collection
```bash
# Collect issues (no snapshot)
uv run github-pm

# Custom output location
uv run github-pm --output reports/custom-report.md

# JSON format only
uv run github-pm --format json
```
Fetches issues from configured repositories and generates report. Does not create timestamped snapshot unless `--save-snapshot` is used.

### Collection with Snapshots
```bash
# Using orchestration script (recommended)
./scripts/collect.sh --production

# Testing mode (smaller dataset)
./scripts/collect.sh --testing

# Custom config with snapshot
./scripts/collect.sh --config config/collection/custom.yaml --snapshot
```
Orchestration script simplifies collection and snapshot creation. Use `--production` for full dataset or `--testing` for quick validation.

### Grouping Options
```bash
# Group by repository (default)
uv run github-pm --group-by repository

# Group by labels
uv run github-pm --group-by labels

# Group by milestone
uv run github-pm --group-by milestone

# Group by assignee
uv run github-pm --group-by assignee
```
Changes how issues are organized in markdown report. JSON export always includes all grouping views.

## Workflow Execution

### Daily Activity
```bash
# Today's activity
uv run python workflows/code_analysis/daily_activity.py

# Last 7 days
uv run python workflows/code_analysis/daily_activity.py --days 7
```
Generates multi-repository activity report showing commits, issues, and work distribution. Analyzes commit messages and issue updates across all configured repositories.

### Period Comparison
```bash
# This week vs last week
uv run python workflows/code_analysis/period_comparison.py --days 7

# This month vs last month
uv run python workflows/code_analysis/period_comparison.py --days 30
```
Compares two time periods to identify trends and changes. Shows commit velocity, issue closure rate, and work pattern shifts.

### Weekly Planning
```bash
# Generate AI-powered weekly plan
uv run python workflows/planning/weekly_planner.py

# Look back 14 days for better context
uv run python workflows/planning/weekly_planner.py --days 14
```
AI-powered analysis of work distribution, status flow, and milestone progress. Requires Ollama with llama3.2 model for recommendations.

### Velocity Tracking
```bash
# Last 6 weeks
uv run python workflows/metrics/velocity_tracker.py

# Last 4 sprints (14-day cycles)
uv run python workflows/metrics/velocity_tracker.py --cycles 4 --cycle-length 14
```
Tracks issues completed per cycle, commit volume trends, and code quality metrics. Shows velocity trends and contributor activity over time.

### Roadmap Generation
```bash
# Generate roadmap from milestones
uv run python workflows/planning/roadmap_generator.py

# Use 60-day velocity sample
uv run python workflows/planning/roadmap_generator.py --velocity-days 60
```
Creates visual roadmap from GitHub milestones with progress tracking. Predicts completion dates based on actual velocity and shows health status.

### Trend Analysis
```bash
# Compare two snapshots
uv run python workflows/trend_analysis/compare_periods.py 2025-01-17_09-30 2025-01-17_14-15

# Using orchestration script
uv run python scripts/run_workflow.py trend_analysis compare_periods \
  --baseline 2025-01-17_09-30 \
  --current 2025-01-17_14-15
```
Compares two snapshots to identify significant changes. Analyzes issue states, labels, repositories, and assignee workload shifts.

### Repository Comparison (AI)
```bash
# Analyze with AI
uv run python workflows/summarization/repo_comparison.py --model llama3.2

# Using orchestration script
uv run python scripts/run_workflow.py summarization repo_comparison --model llama3.2
```
AI-powered analysis comparing activity across repositories. Requires Ollama with specified model to generate natural language insights.

## Common Workflows

### Morning Routine
```bash
# Collect SOD snapshot and start dashboard
uv run dashboard start --sod

# View daily activity
uv run python workflows/code_analysis/daily_activity.py
```
Captures baseline state and starts monitoring. Dashboard shows real-time metrics while daily activity provides detailed yesterday's work summary.

### End of Day Routine
```bash
# Run complete EOD workflow
uv run dashboard eod

# Manually: collect EOD, generate summary, stop dashboard
uv run github-pm --save-snapshot --label eod
uv run python workflows/planning/daily_summary.py
uv run dashboard stop
```
Automated workflow captures end-of-day state, generates summary, and cleans up. Manual steps shown for customization or troubleshooting.

### Weekly Planning
```bash
# Compare this week vs last week
uv run python workflows/code_analysis/period_comparison.py --days 7

# Generate AI planning recommendations
uv run python workflows/planning/weekly_planner.py

# Check velocity trends
uv run python workflows/metrics/velocity_tracker.py
```
Three-step process for weekly planning. Period comparison shows what happened, weekly planner recommends next steps, velocity tracker shows trends.

### Milestone Review
```bash
# Collect snapshot for milestone
uv run github-pm --save-snapshot --label milestone-review

# Generate roadmap
uv run python workflows/planning/roadmap_generator.py

# Check velocity for predictions
uv run python workflows/metrics/velocity_tracker.py --cycles 4 --cycle-length 14
```
Captures milestone state, visualizes roadmap, and validates velocity assumptions. Use for sprint planning or milestone retrospectives.

## File Locations

### Snapshots
```
data/YYYY-MM-DD_HH-MM-SS/     # Timestamped snapshot directories
data/latest                    # Symlink to most recent snapshot
```

### Reports
```
reports/daily/                 # Daily activity and summaries
reports/weekly/                # Weekly plans and comparisons
reports/adhoc/                 # Ad-hoc analysis and trend reports
reports/metrics/               # Velocity and metric tracking
reports/planning/              # Roadmaps and strategic planning
```

### Logs
```
.dashboard.log                 # Dashboard server logs
.dashboard.pid                 # Dashboard process ID
```

### Configuration
```
config/collection/default.yaml      # Production collection config
config/collection/testing.yaml      # Testing collection config
config/workflows/workflow_config.yaml  # Workflow thresholds and parameters
```

## Portfolio Documentation

### Extract for Resume
```bash
# Resume format (elevator pitch + outcomes + tech stack)
uv run python scripts/extract_portfolio.py resume

# Save to file
uv run python scripts/extract_portfolio.py resume > resume-project.txt
```
Extracts project description formatted for resume use. Includes elevator pitch, top 3 outcomes, and technology stack in plain text format.

### Extract for LinkedIn
```bash
# LinkedIn post format
uv run python scripts/extract_portfolio.py linkedin

# Save to file
uv run python scripts/extract_portfolio.py linkedin > linkedin-post.md
```
Generates social media post with elevator pitch, top 5 features, and hashtags. Ready to copy/paste to LinkedIn project section.

### Extract for Interview Prep
```bash
# Interview discussion format
uv run python scripts/extract_portfolio.py interview

# Save to file
uv run python scripts/extract_portfolio.py interview > interview-prep.md
```
Creates interview prep document with problem context, solution approach, and top 3 technical challenges. Use for technical interview preparation.

### Extract for Portfolio Website
```bash
# Full project page format
uv run python scripts/extract_portfolio.py website

# Save to file
uv run python scripts/extract_portfolio.py website > portfolio-page.md
```
Generates complete project page with problem, solution, features, tech stack, and outcomes. Web-ready markdown for portfolio sites.

### Extract Tags
```bash
# Get all technology tags
uv run python scripts/extract_portfolio.py tags
```
Outputs comma-separated list of technology and domain tags. Use for skill matrices and keyword optimization.

### Update PROJECT.md
```bash
# Edit project description
vim PROJECT.md

# Or use preferred editor
code PROJECT.md
```
Update project description as the project evolves. See `PROJECT.template.md` for structure guide and `docs/PORTFOLIO_SYSTEM.md` for complete documentation.

## Tips

- **Always use orchestration scripts** (`./scripts/collect.sh`, `./scripts/run_workflow.py`) for consistency
- **Label snapshots meaningfully** using `--label` for easier identification and filtering
- **Use testing config** (`./scripts/collect.sh --testing`) before running production workflows
- **Dashboard status command** shows if server is running before trying to start/stop
- **Follow logs** (`uv run dashboard logs --follow`) when troubleshooting dashboard issues
- **SOD/EOD labels** are recognized patterns - use them for time-of-day tracking
- **Latest symlink** always points to most recent snapshot - workflows use this by default
