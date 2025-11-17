# Code Analysis Workflows

Workflows that analyze actual code changes and commits to understand what work was delivered.

## Available Workflows

### Commit Report (`commit_report.py`)

Analyzes commit messages to understand work patterns, types of changes, and correlate with issues.

**Features:**
- Extracts and parses commit messages
- Recognizes Conventional Commits format (feat, fix, docs, etc.)
- Identifies breaking changes
- Correlates commits with GitHub issues
- Shows activity timeline
- Analyzes contributor patterns

**Usage:**

```bash
# Basic usage - analyze last 7 days
uv run python workflows/code_analysis/commit_report.py \
  --owner mpazaryna \
  --repo chiro

# Specific date range
uv run python workflows/code_analysis/commit_report.py \
  --owner mpazaryna \
  --repo chiro \
  --since 2025-01-01 \
  --until 2025-01-31

# More commits, with issue correlation
uv run python workflows/code_analysis/commit_report.py \
  --owner mpazaryna \
  --repo chiro \
  --limit 200 \
  --correlate-issues

# Via orchestration script
uv run python scripts/run_workflow.py code_analysis commit_report \
  --owner mpazaryna \
  --repo chiro \
  --since 2025-01-01
```

**Conventional Commits Format:**

The analyzer recognizes the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Examples:**
- `feat: add voice recording feature`
- `fix(dashboard): correct data display issue`
- `docs: update API documentation`
- `feat(mlx)!: breaking change to model interface`

**Recognized Types:**
- `feat` - New features
- `fix` - Bug fixes
- `docs` - Documentation changes
- `style` - Code style (formatting, etc.)
- `refactor` - Code refactoring
- `perf` - Performance improvements
- `test` - Test changes
- `chore` - Build/tooling changes
- `ci` - CI/CD changes
- `build` - Build system changes
- `revert` - Revert previous commits

**Output:**

Reports saved to `reports/adhoc/commit_report_REPO_TIMESTAMP.md` include:

1. **Summary Statistics**
   - Total commits
   - Conventional commit percentage
   - Contributors
   - Issues referenced

2. **Work Breakdown**
   - Commits by type (features, fixes, docs, etc.)
   - Percentage breakdown

3. **Areas of Focus**
   - Most active scopes/components

4. **Breaking Changes**
   - Highlighted breaking changes with details

5. **Issue Correlation**
   - Which commits reference which issues
   - Shows issue titles and states if correlated with snapshot

6. **Contributors**
   - Commit counts per author

7. **Activity Timeline**
   - Visual graph of daily commit activity

8. **Recent Commits Sample**
   - Detailed view of recent commits with metadata

**Use Cases:**

- **Weekly Status Reports** - Show what was actually delivered
- **Work Pattern Analysis** - Understand what types of work are being done
- **Commit Quality** - Track conventional commit adoption
- **Issue → Delivery** - See which issues have active work
- **Team Velocity** - Understand work patterns over time
- **Breaking Change Tracking** - Monitor API/interface changes

## Combining with Issue Analysis

The real power comes from combining commit analysis with issue tracking:

```bash
# 1. Collect issues
./scripts/collect.sh --production

# 2. Analyze commits for a specific repo
uv run python workflows/code_analysis/commit_report.py \
  --owner mpazaryna \
  --repo chiro \
  --correlate-issues

# This shows:
# - What's planned (issues)
# - What's being worked on (commits)
# - The connection between them (issue references)
```

## Configuration

Commit analysis parameters can be configured in:
- `config/workflows/workflow_config.yaml`

## Future Enhancements

- Multi-repo commit analysis
- Code churn metrics
- Author contribution patterns
- Automated changelog generation from commits
- AI-powered commit summarization using LangChain
