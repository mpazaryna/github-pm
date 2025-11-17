#!/bin/bash
# Data collection script for GitHub PM

set -e

# Default values
CONFIG="config/collection/production.yaml"
SAVE_SNAPSHOT=false
FORMAT="both"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --config)
      CONFIG="$2"
      shift 2
      ;;
    --snapshot)
      SAVE_SNAPSHOT=true
      shift
      ;;
    --testing)
      CONFIG="config/collection/testing.yaml"
      SAVE_SNAPSHOT=true
      shift
      ;;
    --production)
      CONFIG="config/collection/production.yaml"
      SAVE_SNAPSHOT=true
      shift
      ;;
    --format)
      FORMAT="$2"
      shift 2
      ;;
    --help)
      echo "Usage: ./scripts/collect.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --config FILE       Use specific config file (default: config/collection/production.yaml)"
      echo "  --snapshot          Save timestamped snapshot to data/"
      echo "  --testing           Use testing config and save snapshot"
      echo "  --production        Use production config and save snapshot"
      echo "  --format FORMAT     Output format: markdown, json, or both (default: both)"
      echo "  --help              Show this help message"
      echo ""
      echo "Examples:"
      echo "  ./scripts/collect.sh --testing"
      echo "  ./scripts/collect.sh --production --format json"
      echo "  ./scripts/collect.sh --config my-config.yaml --snapshot"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Run './scripts/collect.sh --help' for usage information"
      exit 1
      ;;
  esac
done

# Build command
CMD="uv run github-pm --config $CONFIG --format $FORMAT"

if [ "$SAVE_SNAPSHOT" = true ]; then
  CMD="$CMD --save-snapshot"
fi

# Run collection
echo "Running data collection..."
echo "Config: $CONFIG"
echo "Format: $FORMAT"
echo "Save snapshot: $SAVE_SNAPSHOT"
echo ""

eval $CMD

echo ""
echo "Collection complete!"
