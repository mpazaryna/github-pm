#!/bin/bash
# Run all workflows on collected data

set -e

echo "GitHub PM - Running All Workflows"
echo "=================================="
echo ""

# Check if we have data
if [ ! -d "data" ] || [ -z "$(ls -A data 2>/dev/null | grep -v '.gitkeep')" ]; then
  echo "Error: No data found in data/ directory"
  echo "Run './scripts/collect.sh --snapshot' first"
  exit 1
fi

# Get list of snapshots
SNAPSHOTS=($(ls -1 data | grep -v '.gitkeep' | grep -v 'latest' | sort))
NUM_SNAPSHOTS=${#SNAPSHOTS[@]}

echo "Found $NUM_SNAPSHOTS snapshots"
echo ""

if [ $NUM_SNAPSHOTS -lt 2 ]; then
  echo "Warning: Need at least 2 snapshots for trend analysis"
  echo "Only basic analysis available"
  echo ""
fi

# Run trend analysis if we have multiple snapshots
if [ $NUM_SNAPSHOTS -ge 2 ]; then
  echo "Running Trend Analysis..."
  echo "------------------------"

  # Compare latest two snapshots
  BASELINE=${SNAPSHOTS[$NUM_SNAPSHOTS-2]}
  CURRENT=${SNAPSHOTS[$NUM_SNAPSHOTS-1]}

  echo "Comparing $BASELINE → $CURRENT"
  uv run python scripts/run_workflow.py trend_analysis compare_periods \
    --baseline "$BASELINE" \
    --current "$CURRENT"

  echo ""
fi

# Run summarization workflow
echo "Running Repository Comparison..."
echo "--------------------------------"
echo "Analyzing latest snapshot with AI"

# Check if Ollama is available
if command -v ollama &> /dev/null; then
  uv run python scripts/run_workflow.py summarization repo_comparison \
    --model llama3.2 || echo "  Note: Install Ollama and pull llama3.2 to enable AI analysis"
else
  echo "  Skipping: Ollama not installed"
  echo "  Install from: https://ollama.ai"
fi

echo ""

# Placeholder for future workflows
echo "Additional Workflows:"
echo "--------------------"
echo "- Anomaly Detection: Coming soon"
echo "- Custom Reports: Coming soon"
echo ""

echo "All workflows complete!"
