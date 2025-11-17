# Workflows

This directory contains agentic analysis workflows that process collected GitHub issue data.

## Available Workflows

### Trend Analysis (`trend_analysis/`)

**compare_periods.py** - Compare two data snapshots to identify trends
```bash
uv run python workflows/trend_analysis/compare_periods.py <baseline_timestamp> <current_timestamp>

# Example
uv run python workflows/trend_analysis/compare_periods.py 2025-01-17_09-30 2025-01-17_14-15
```

Analyzes:
- Overall issue count changes
- State transitions (open/closed)
- Repository-specific trends
- Label usage patterns
- Assignee workload changes

Generates insights about significant changes and creates a detailed markdown report.

### Summarization (`summarization/`)

**repo_comparison.py** - AI-powered repository comparison using LangChain + Ollama
```bash
uv run python workflows/summarization/repo_comparison.py --model llama3.2

# Analyze specific snapshot
uv run python workflows/summarization/repo_comparison.py \
  --snapshot 2025-11-17_08-23-35 \
  --model llama3.2

# Use different Ollama model
uv run python workflows/summarization/repo_comparison.py --model mistral
```

**Requirements:**
- [Ollama](https://ollama.ai) installed and running
- Ollama model pulled (e.g., `ollama pull llama3.2`)

Generates:
- Overview of each repository based on its issues
- Key differences between repositories
- Notable patterns or themes
- Insights about workload distribution and focus areas

### Anomaly Detection (`anomaly_detection/`)

Coming soon - Detect unusual patterns, spikes, and stale issues

### Custom Reports (`custom_reports/`)

Coming soon - Stakeholder-specific reports

## Configuration

Workflows use configuration from `config/workflows/workflow_config.yaml` to customize:
- Analysis thresholds
- Metrics to track
- Report formatting

## Running Workflows

### Individual Workflow
```bash
uv run python workflows/<category>/<workflow>.py [arguments]
```

### Via Orchestration Script
```bash
# Run specific workflow
uv run python scripts/run_workflow.py trend_analysis compare_periods --baseline 2025-01-17_09-30

# Run all workflows on latest data
./scripts/run_all_workflows.sh
```

## Adding New Workflows

1. Create a new Python file in the appropriate category directory
2. Implement analysis logic using data from `data/` directory
3. Output results to `reports/` directory
4. Update this README with usage instructions
