# Summarization Workflows

AI-powered analysis workflows using LangChain + Ollama for natural language insights.

## Available Workflows

### Repository Comparison (`repo_comparison.py`)

Generates natural language comparison and analysis of your repositories using local LLM models.

**Features:**
- Analyzes differences between repositories
- Identifies focus areas and patterns
- Compares workload distribution
- Provides actionable insights

**Usage:**

```bash
# Analyze latest snapshot
uv run python workflows/summarization/repo_comparison.py --model llama3.2

# Analyze specific snapshot
uv run python workflows/summarization/repo_comparison.py \
  --snapshot 2025-11-17_08-23-35 \
  --model llama3.2

# Use different Ollama model
uv run python workflows/summarization/repo_comparison.py --model mistral

# Via orchestration script
uv run python scripts/run_workflow.py summarization repo_comparison --model llama3.2
```

**Prerequisites:**

1. Install [Ollama](https://ollama.ai)
2. Pull a model:
   ```bash
   ollama pull llama3.2
   # or
   ollama pull mistral
   ```
3. Ensure Ollama is running

**Output:**

Reports are saved to `reports/daily/repo_comparison_TIMESTAMP.md` and include:
- Summary statistics table
- AI-generated analysis comparing repositories
- Detailed breakdown of each repository

**Example Output:**

```markdown
# Repository Comparison Report

## Summary Statistics
| Repository | Issues | Top Labels |
|------------|--------|------------|
| org/repo1  | 23     | enhancement, bug |
| org/repo2  | 15     | enhancement, voice, core |

## AI-Powered Analysis

### org/repo1
Overview: Feature development focused with 14 enhancements...

### Key Differences Between Repositories
- **Feature Development**: repo1 has more diverse issue types...
- **Assignees**: repo2 has more unassigned issues...
```

## Available Models

Tested with:
- `llama3.2` (recommended, fast and efficient)
- `mistral` (alternative)
- `qwen2.5:7b` (larger model for more detailed analysis)

To see available models: `ollama list`

## Configuration

Model selection and analysis parameters can be configured in:
- `config/workflows/workflow_config.yaml`

## Technical Details

- **LangChain**: Provides prompt templates and LLM integration
- **Ollama**: Local LLM inference (privacy-focused, no data leaves your machine)
- **Model agnostic**: Works with any Ollama-compatible model

## Future Enhancements

- Executive summary generation
- Team-specific digests
- Time-based summaries (daily, weekly, monthly)
- Trend narratives combining with trend analysis data
