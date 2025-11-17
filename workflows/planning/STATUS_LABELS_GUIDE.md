# GitHub Status Labels Setup Guide

## Overview

This guide helps you set up status labels in your GitHub repositories to enable powerful workflow tracking and AI-powered planning with the weekly planner.

## Why Status Labels?

Status labels enable the weekly planner to:
- **Track flow health**: Identify bottlenecks in your workflow
- **Balance WIP**: Ensure you're not overloaded with in-progress work
- **Prioritize grooming**: Know when you need to prepare more work
- **Measure velocity**: Understand how quickly work moves through stages

## Quick Setup

### Option 1: Using GitHub CLI (Recommended)

```bash
# Navigate to your repository
cd /path/to/your/repo

# Create all status labels at once
gh label create "status:backlog" --color "D4C5F9" --description "Issue is in the backlog"
gh label create "status:ready" --color "0E8A16" --description "Issue is ready to be worked on"
gh label create "status:in progress" --color "FBCA04" --description "Issue is currently being worked on"
gh label create "status:in review" --color "1D76DB" --description "Issue is in review/PR stage"
gh label create "status:done" --color "5319E7" --description "Issue is complete"
```

### Option 2: Using GitHub Web UI

1. Go to your repository on GitHub
2. Click **Issues** → **Labels**
3. Click **New label** for each status:

| Label Name | Color | Description |
|------------|-------|-------------|
| `status:backlog` | `#D4C5F9` (light purple) | Issue is in the backlog |
| `status:ready` | `#0E8A16` (green) | Issue is ready to be worked on |
| `status:in progress` | `#FBCA04` (yellow) | Issue is currently being worked on |
| `status:in review` | `#1D76DB` (blue) | Issue is in review/PR stage |
| `status:done` | `#5319E7` (dark purple) | Issue is complete |

## Recognized Label Patterns

The `StatusAnalyzer` recognizes multiple label patterns for flexibility:

### Backlog
- `backlog`
- `status:backlog`
- `status: backlog`

### Ready
- `ready`
- `status:ready`
- `status: ready`
- `to do`
- `todo`

### In Progress
- `in progress`
- `status:in progress`
- `status: in progress`
- `in-progress`
- `status:in-progress`
- `wip`
- `work in progress`

### In Review
- `in review`
- `status:in review`
- `status: in review`
- `review`
- `status:review`

### Done
- `done`
- `status:done`
- `status: done`
- `completed`

**Note**: Label matching is case-insensitive.

## Recommended Workflow

### 1. Backlog → Ready (Grooming)

When planning your week:
```bash
# Move issues to ready status
gh issue edit 123 --add-label "status:ready" --remove-label "status:backlog"
```

**Guidelines:**
- Keep 3-5 issues in "Ready" at all times
- "Ready" means: well-defined, accepted, ready to start
- Groom issues during weekly planning sessions

### 2. Ready → In Progress (Start Work)

When you start working:
```bash
gh issue edit 123 --add-label "status:in progress" --remove-label "status:ready"
```

**Guidelines:**
- Limit WIP (Work In Progress) to 3 items or fewer
- Only move to "In Progress" when actively working
- Include the issue number in your commit messages: `feat: add feature (#123)`

### 3. In Progress → In Review (Create PR)

When you create a pull request:
```bash
gh issue edit 123 --add-label "status:in review" --remove-label "status:in progress"
```

**Guidelines:**
- Create PR with issue reference: "Closes #123"
- Request reviews promptly
- Keep PRs small and focused

### 4. In Review → Done (Merge PR)

When PR is merged:
```bash
gh issue close 123 --comment "Merged in PR #456"
```

**Note:** The system automatically treats closed issues as "done", but you can also add the label explicitly.

## Bulk Operations

### Add Status Labels to Existing Issues

```bash
# Add backlog label to all open issues without a status
gh issue list --limit 100 --json number,labels --jq '.[] | select(.labels | map(.name) | any(test("status:")) | not) | .number' | \
  xargs -I {} gh issue edit {} --add-label "status:backlog"
```

### Move Multiple Issues to Ready

```bash
# Example: Move issues 101, 102, 103 to ready
for issue in 101 102 103; do
  gh issue edit $issue --add-label "status:ready" --remove-label "status:backlog"
done
```

## Integration with Weekly Planner

The weekly planner uses status labels to:

### 1. Show Current Status Distribution

```
## Current Backlog

| Repository | Open | Backlog | Ready | In Progress | In Review |
|------------|------|---------|-------|-------------|-----------|
| your-repo  | 23   | 18      | 3     | 2           | 0         |
```

### 2. Identify Flow Bottlenecks

```
## Flow Health

### your-repo
⚠️ **grooming_needed**: 18 issues in 'Backlog' but only 3 'Ready'

**Recommendations:**
- Need grooming session - move backlog issues to 'Ready'
```

### 3. Recommend Ready Work

```
## Ready to Work

### your-repo
1. Issue #123 - Fix authentication bug (priority, milestone: Q1 2025)
2. Issue #124 - Add user settings page
3. Issue #125 - Improve error handling
```

## Best Practices

### 1. Consistent Labeling
- Always add a status label when creating new issues
- Default new issues to `status:backlog`
- Update status labels as work progresses

### 2. WIP Limits
- Keep "In Progress" + "In Review" ≤ 3 items
- Finish work before starting new work
- The planner will warn you if WIP is too high

### 3. Regular Grooming
- Review backlog weekly
- Move 3-5 issues to "Ready" each week
- Ensure "Ready" issues are well-defined

### 4. Quick Status Updates
Create shell aliases for common operations:

```bash
# Add to your ~/.bashrc or ~/.zshrc
alias gh-ready='gh issue edit $1 --add-label "status:ready" --remove-label "status:backlog"'
alias gh-start='gh issue edit $1 --add-label "status:in progress" --remove-label "status:ready"'
alias gh-review='gh issue edit $1 --add-label "status:in review" --remove-label "status:in progress"'

# Usage:
# gh-ready 123
# gh-start 123
# gh-review 123
```

## Troubleshooting

### Issue: Planner shows all issues in "Backlog"

**Solution:** You haven't added status labels yet. Run the bulk operation:
```bash
gh issue list --limit 100 --json number --jq '.[].number' | \
  xargs -I {} gh issue edit {} --add-label "status:backlog"
```

### Issue: Flow health warnings don't make sense

**Problem:** Inconsistent label usage across team
**Solution:**
1. Audit labels: `gh issue list --label "status:in progress"`
2. Standardize on label format (e.g., `status:in progress` not `wip`)
3. Update team workflow documentation

### Issue: WIP limit seems too strict

**Response:** The default WIP limit is 3 items (ideal for 1-2 person teams). This is intentional:
- Focuses on finishing work
- Reduces context switching
- Improves flow efficiency

If you consistently have >3 items in progress, consider if they're truly "in progress" or just "started".

## Advanced: GitHub Projects Integration (Optional)

If you use GitHub Projects, you can sync status labels with project columns:

```yaml
# .github/workflows/sync-labels.yml
name: Sync Labels with Project
on:
  issues:
    types: [labeled]
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Move to column based on label
        uses: alex-page/github-project-automation-plus@v0.8.1
        with:
          project: Your Project Name
          column: ${{ github.event.label.name }}
          repo-token: ${{ secrets.GITHUB_TOKEN }}
```

## Validation

After setup, validate your labels are working:

```bash
# Run a collection and generate weekly plan
./scripts/collect.sh --production
uv run python workflows/planning/weekly_planner.py

# Check the report
cat reports/weekly/plan_*.md
```

You should see:
- Status distribution table populated
- Flow health analysis with specific numbers
- Recommendations based on your current flow

## Resources

- [GitHub Labels Documentation](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/managing-labels)
- [GitHub CLI Issue Commands](https://cli.github.com/manual/gh_issue)
- [Kanban Flow Methodology](https://kanbanize.com/kanban-resources/getting-started/what-is-kanban)
- [Limiting WIP](https://kanbanize.com/kanban-resources/getting-started/what-is-wip)

---

**Next Steps:**
1. Set up labels in all your repositories
2. Add status labels to existing issues
3. Run weekly planner to see flow analysis
4. Adjust your workflow based on recommendations
