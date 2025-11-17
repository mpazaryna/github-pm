# Planning Workflows

AI-powered workflows that help you plan and balance work across multiple concurrent projects.

## Available Workflows

### Weekly Planner (`weekly_planner.py`)

**The Problem:** When managing multiple repositories, it's hard to ensure balanced attention. You might work heavily on one project and neglect others.

**The Solution:** AI analyzes last week's commits and your current backlog to suggest a balanced plan for next week.

**Usage:**

```bash
# Generate weekly plan for next week
uv run python workflows/planning/weekly_planner.py

# Look back 14 days instead of 7
uv run python workflows/planning/weekly_planner.py --days 14

# Use different AI model
uv run python workflows/planning/weekly_planner.py --model mistral

# Custom config
uv run python workflows/planning/weekly_planner.py --config config/collection/production.yaml
```

**What It Analyzes:**

1. **Last Week's Commits** - Actual work delivered per repository
2. **Current Backlog** - Open issues, priority issues, unassigned work
3. **Work Distribution** - Percentage of effort per repository
4. **Imbalances** - Which repos got neglected

**AI-Generated Plan Includes:**

1. **Work Distribution Analysis**
   - Which repositories got attention
   - Which were neglected
   - Concerning imbalances

2. **Recommended Distribution**
   - Suggested % allocation for next week
   - Rationale for rebalancing

3. **Priority Issues**
   - Specific issue recommendations per repo
   - Why they should be prioritized

4. **Strategic Recommendations**
   - Patterns and concerns
   - Suggestions for maintaining balance

**Example Output:**

```markdown
## Last Week's Delivery
| Repository | Commits | Percentage |
|------------|---------|------------|
| chiro | 22 | 43.1% |
| ai-fundraising-v2 | 29 | 56.9% |
| authentic-advantage | 0 | 0.0% | ⚠️

## AI Recommendation for Next Week:
- authentic-advantage: 20% (catch up on neglected work)
- chiro: 40% (maintain momentum)
- ai-fundraising-v2: 40% (sustain progress)

## Priority Issues:
- authentic-advantage #37: UI Tests Failing
- chiro: Performance Optimization
- ai-fundraising-v2 #10: Data Validation
```

**Output Files:**

- **Markdown**: `reports/weekly/plan_TIMESTAMP.md` - Human-readable plan
- **JSON**: `reports/weekly/plan_TIMESTAMP.json` - Machine-readable data

## Weekly Planning Workflow

### Recommended Schedule:

**Friday Afternoon (15 minutes):**

```bash
# 1. Collect latest data
./scripts/collect.sh --production

# 2. Generate weekly plan
uv run python workflows/planning/weekly_planner.py

# 3. Review the plan
cat reports/weekly/plan_*.md
```

**Monday Morning (Planning Session):**

1. Review AI-generated plan
2. Adjust based on priorities/constraints
3. Assign specific issues to team members
4. Set goals for the week

**Throughout the Week:**

- Work on assigned issues
- Commit with proper conventional format
- Reference issue numbers in commits

**Next Friday:**

- Run planner again
- See if you achieved balance
- Adjust for next week

## Concurrent Work Stream Management

This tool enables **agentic planning** across multiple concurrent projects:

### The Vision:

Instead of ad-hoc work distribution, you have:

1. **Data-Driven Insights** - Know exactly where effort went
2. **AI Recommendations** - Get balanced distribution suggestions
3. **Issue Prioritization** - Clear guidance on what to work on
4. **Continuous Adjustment** - Weekly feedback loop

### Multi-Session Agentic Programming:

The AI helps you balance:
- **Project A** - Feature development
- **Project B** - Bug fixes and stability
- **Project C** - New experimental work

Each week it ensures no project gets completely neglected.

## Integration with Other Workflows

Combine weekly planning with other analyses:

```bash
# Complete weekly workflow

# 1. Collect data
./scripts/collect.sh --production

# 2. Generate weekly plan (AI-powered)
uv run python workflows/planning/weekly_planner.py

# 3. Analyze individual repo commits
uv run python workflows/code_analysis/commit_report.py \
  --owner mpazaryna --repo chiro --format both

# 4. Get repository comparison
uv run python workflows/summarization/repo_comparison.py

# 5. Run trend analysis
./scripts/run_all_workflows.sh
```

## JSON Output for Programmatic Use

The JSON output enables further automation:

```python
import json

# Load weekly plan data
with open('reports/weekly/plan_2025-11-17_08-54-37.json') as f:
    plan = json.load(f)

# Get last week's distribution
last_week = plan['last_week']['by_repository']

# Find neglected repos (< 10% of commits)
neglected = {
    repo: data
    for repo, data in last_week.items()
    if data['percentage'] < 10
}

print(f"Neglected repos: {list(neglected.keys())}")

# Automatically create issues for rebalancing
for repo in neglected:
    print(f"Action: Prioritize work on {repo} next week")
```

## Future Enhancements

- **Automated Issue Assignment** - AI suggests which team member should work on which issue
- **Sprint Velocity Tracking** - Compare planned vs actual delivery
- **Multi-Week Planning** - Look ahead 2-4 weeks
- **Dependency Detection** - Identify cross-repo dependencies
- **Capacity Planning** - Account for team size and availability

---

**Remember:** The goal is balanced, sustainable progress across all your projects. The AI helps you avoid the natural tendency to focus on one project and neglect others.
