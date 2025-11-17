# Engineering Manager's Guide to GitHub PM

A practical guide for using GitHub PM to manage multiple repositories and teams.

## The Problem We Solve

As an engineering manager for small teams (1-2 person shops):
- **Linear/Jira are overkill** - Expensive, complex, force process changes
- **GitHub alone isn't enough** - No cross-repo visibility or insights
- **Manual reporting is tedious** - Copy-pasting issues into status reports
- **Can't see the forest for the trees** - Hard to spot patterns across repos

## The Solution

**Meet your team where they are** - Issues and commits stay in GitHub
**Get intelligence without overhead** - Automated data collection and AI analysis
**Own your data** - Everything runs locally, private, forever
**Flexible reporting** - Generate views for any audience

## Daily Workflow Example

### Monday Morning (5 minutes)

```bash
# Collect latest data from all repos
./scripts/collect.sh --production

# Run analysis
./scripts/run_all_workflows.sh
```

**You now have:**
1. ✅ Trend analysis showing what changed over the week
2. ✅ AI-powered repository comparison
3. ✅ All data timestamped and stored

### Generate Reports for Different Audiences

#### For Your Team (Technical Deep Dive)

```bash
# Show commits from chiro repo this week
uv run python workflows/code_analysis/commit_report.py \
  --owner mpazaryna \
  --repo chiro \
  --since 2025-11-10 \
  --correlate-issues
```

**Shows:**
- 76% conventional commits (good!) ✨
- 32% features, 14% docs, 14% fixes
- Which issues had commits this week
- When people were working
- Breaking changes to watch out for

#### For Stakeholders (High-Level Summary)

Use the AI-generated repo comparison:
```bash
uv run python workflows/summarization/repo_comparison.py --model llama3.2
```

**Copy the AI summary into:**
- Investor email: "Here's what we shipped this week"
- Team Slack: "Focus areas this sprint"
- Board meeting notes

#### For Yourself (Strategic View)

Check the trend analysis report:
- Are issues piling up in one repo?
- Is one project getting all the attention?
- Are unassigned issues growing?
- What labels are trending?

## Complete Weekly Workflow

### Friday 4pm - Weekly Snapshot

```bash
# Collect data
./scripts/collect.sh --production

# Run all analysis
./scripts/run_all_workflows.sh

# Analyze commits for each active repo
uv run python scripts/run_workflow.py code_analysis commit_report \
  --owner mpazaryna --repo chiro --since 2025-11-10

uv run python scripts/run_workflow.py code_analysis commit_report \
  --owner mpazaryna --repo authentic-advantage --since 2025-11-10
```

### What You Learn

#### From Issues (Planned Work)
- What's on the backlog
- What's prioritized
- Who's assigned what
- Milestone progress

#### From Commits (Actual Work)
- What was actually delivered
- Types of work (features vs fixes vs docs)
- Work patterns and velocity
- Breaking changes

#### From AI Analysis
- How repos compare
- Focus areas
- Workload distribution
- Strategic insights

## Real-World Use Cases

### 1. Weekly Status Email

**Situation:** Need to send update to investors
**Solution:**
```bash
./scripts/collect.sh --production
uv run python workflows/summarization/repo_comparison.py --model llama3.2
```

Copy AI summary from `reports/daily/repo_comparison_*.md`
Paste into email, add context, send.

### 2. Sprint Planning

**Situation:** Need to understand current state before planning
**Solution:**
```bash
# See trends
./scripts/run_all_workflows.sh

# See what was actually delivered last sprint
uv run python scripts/run_workflow.py code_analysis commit_report \
  --owner mpazaryna --repo chiro --since 2025-11-01
```

Now you know:
- Issue velocity
- Actual delivery vs planned
- Where bottlenecks are

### 3. Team 1-on-1s

**Situation:** Meeting with developer to discuss their work
**Solution:** Look at commit report

See exactly:
- What they worked on
- Types of contributions
- Issues they addressed
- Impact of their work

### 4. Justifying Resources

**Situation:** Need to show workload to get more budget
**Solution:** Historical trend analysis

```bash
# Compare now vs 3 months ago
uv run python scripts/run_workflow.py trend_analysis compare_periods \
  --baseline 2025-08-01_09-00-00 \
  --current latest
```

Show concrete data:
- Issue growth
- Unassigned work piling up
- Label distribution changes

## Conventional Commits (Optional but Recommended)

Encourage your team to use this format:

```
feat(dashboard): add real-time updates
fix(api): correct date parsing bug
docs: update API documentation
```

**Benefits:**
- Automatic changelogs
- Better commit analysis
- Clearer history
- Breaking change detection

**It's optional** - The tool works either way, but gets superpowers with structured commits.

## Integration with Existing Tools

### You Can Still Use Linear

If you grow and stakeholders want Linear:
- Keep GitHub as source of truth
- One-way sync: GitHub → Linear
- Or just send them reports from this tool

### Slack Integration (Future)

Easy to add:
```python
# Post daily summaries to Slack
./scripts/collect.sh --production
python workflows/integrations/post_to_slack.py
```

## Cost Comparison

**Linear:**
- $8-15/user/month
- 2 person team = $192-360/year
- Everyone needs to learn it
- Data locked in their system

**GitHub PM:**
- $0
- Runs locally
- Team uses GitHub (already know it)
- Own your data forever

## Why This Works for Small Teams

**1-2 person shops need:**
- ✅ Low overhead (no process changes)
- ✅ High visibility (see everything)
- ✅ Flexible reporting (different audiences)
- ✅ Cost effective (free)
- ✅ Private/secure (runs locally)

**This tool gives you:**
- Engineering manager superpowers
- Without adding bureaucracy
- To your team

## Getting Started Checklist

- [ ] Install prerequisites (gh CLI, Ollama, uv)
- [ ] Configure `config/collection/production.yaml` with your repos
- [ ] Run first collection: `./scripts/collect.sh --production`
- [ ] Run analysis: `./scripts/run_all_workflows.sh`
- [ ] Review reports in `reports/`
- [ ] Set up weekly cron job for automated collection
- [ ] Share AI summary in next team meeting

## Advanced: Automated Weekly Reports

Add to crontab:
```bash
# Every Friday at 4pm
0 16 * * 5 cd /path/to/github-pm && ./scripts/collect.sh --production && ./scripts/run_all_workflows.sh

# Email yourself the AI summary
5 16 * * 5 cat /path/to/github-pm/reports/daily/repo_comparison_*.md | mail -s "Weekly Repo Summary" you@company.com
```

## Support & Questions

- **Documentation:** See README.md and CLAUDE.md
- **Workflows:** Each workflow has its own README in `workflows/`
- **Issues:** Use GitHub issues in this repo

---

**Remember:** The best tool is one your team actually uses. Since this requires zero changes from your developers, adoption is instant. You get the intelligence, they keep working how they always have.
