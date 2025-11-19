# Repository Management System

## Overview
Automatically discover and sync GitHub repositories instead of manually maintaining lists. Uses `gh` CLI to fetch repos and applies customizable filters to control what gets included.

## Why Dynamic Discovery?

**Problem with Manual Lists:**
- Requires updating config every time you create a new repo
- Easy to forget to add repos to the list
- No way to automatically exclude forks, archived repos, or test projects
- Copy/paste errors when adding repos

**Benefits of Dynamic Discovery:**
- Zero maintenance - new repos automatically included
- Intelligent filtering by visibility, topics, language, age
- Manual overrides for edge cases
- Statistics to understand what's being included/excluded
- Version-controlled filter preferences

## Quick Start

### 1. Configure Filters
Edit `config/collection/repo_filters.yaml`:

```yaml
owner: your-github-username

filters:
  exclude_forks: true        # Skip forked repos
  exclude_archived: true     # Skip archived repos
  visibility: []             # Include all (public, private, internal)

  # Only include repos with these topics (empty = all)
  include_topics: []

  # Exclude repos with these topics
  exclude_topics:
    - archived
    - deprecated
    - template
```

### 2. Preview What Will Be Included
```bash
uv run python scripts/sync_repos.py --dry-run
```

### 3. Generate Config
```bash
uv run python scripts/sync_repos.py
```

This updates `config/collection/production.yaml` with all matching repos.

### 4. Collect Issues
```bash
uv run github-pm --save-snapshot
```

## Filter Options

### Owner Configuration
```yaml
# Primary GitHub user/org
owner: mpazaryna

# Additional owners (orgs you contribute to)
additional_owners:
  - my-company
  - open-source-org
```

### Basic Filters
```yaml
filters:
  # Exclude forked repositories
  exclude_forks: true

  # Exclude archived repositories
  exclude_archived: true

  # Include only these visibility levels
  # Options: public, private, internal
  # Empty list = include all
  visibility: []
```

### Topic-Based Filtering
```yaml
filters:
  # Only include repos with ALL of these topics
  # Empty = include all topics
  include_topics:
    - production
    - active-development

  # Exclude repos with ANY of these topics
  exclude_topics:
    - archived
    - deprecated
    - template
    - test
```

**Use Cases:**
- Tag production repos with "production" topic, filter by that
- Tag archived projects with "archived" topic to auto-exclude
- Tag experiments with "experiment" to separate from main projects

### Language-Based Filtering
```yaml
filters:
  # Only include repos in these languages
  # Empty = include all languages
  include_languages:
    - Python
    - TypeScript
    - Go

  # Exclude repos in these languages
  exclude_languages:
    - HTML
    - CSS
```

**Use Cases:**
- Focus on Python projects only
- Exclude frontend-only repos
- Track specific language ecosystems

### Age-Based Filtering
```yaml
filters:
  # Exclude repos not updated in X days (0 = include all)
  # Example: 90 = exclude if no updates in 3 months
  min_days_since_update: 90

  # Exclude repos older than X days (0 = include all)
  # Example: 365 = exclude repos created > 1 year ago
  max_age_days: 0
```

**Use Cases:**
- Focus on recently active projects
- Exclude abandoned repos
- Track only current work

### Manual Overrides
```yaml
overrides:
  # Force include (even if filters exclude)
  force_include:
    - owner: mpazaryna
      name: special-legacy-project

  # Force exclude (even if filters include)
  force_exclude:
    - owner: mpazaryna
      name: personal-notes
    - owner: mpazaryna
      name: test-repo
```

**Use Cases:**
- Include archived repo that's still relevant
- Exclude specific repos with sensitive data
- Override filters for edge cases

## Common Configurations

### Active Projects Only
```yaml
filters:
  exclude_forks: true
  exclude_archived: true
  visibility: []
  exclude_topics: [archived, deprecated, template]
  min_days_since_update: 30  # Updated in last 30 days
```

### Python Projects Only
```yaml
filters:
  exclude_forks: true
  exclude_archived: true
  visibility: []
  include_languages: [Python]
```

### Production Systems
```yaml
filters:
  exclude_forks: true
  exclude_archived: true
  visibility: [private]  # Private repos only
  include_topics: [production]
```

### Everything Except Tests
```yaml
filters:
  exclude_forks: true
  exclude_archived: true
  visibility: []
  exclude_topics: [test, template, archived]
```

## Workflow

### Daily Development Flow
```bash
# 1. Morning: Sync repos and start dashboard
uv run python scripts/sync_repos.py
uv run dashboard start --sod

# 2. Work on issues across repos...

# 3. Evening: EOD workflow
uv run dashboard eod
```

### Weekly Maintenance
```bash
# Review what repos are included
uv run python scripts/sync_repos.py --stats

# Update filters if needed
vim config/collection/repo_filters.yaml

# Regenerate config
uv run python scripts/sync_repos.py
```

### Adding New Repos
**No action needed!** New repos are automatically discovered on next sync.

Optionally, add topics to new repos for better filtering:
```bash
gh repo edit owner/repo --add-topic production
gh repo edit owner/repo --add-topic python
```

### Excluding Repos
**Option 1: Add to force_exclude**
```yaml
overrides:
  force_exclude:
    - owner: mpazaryna
      name: unwanted-repo
```

**Option 2: Add topic and filter**
```bash
gh repo edit owner/repo --add-topic exclude-from-pm
```

Then in filters:
```yaml
filters:
  exclude_topics: [exclude-from-pm]
```

## Statistics and Debugging

### Show Sync Statistics
```bash
uv run python scripts/sync_repos.py --stats
```

Output:
```
============================================================
Repository Sync Statistics
============================================================
Owners scanned: mpazaryna, j-bouchard
Total repositories: 37
After filtering: 33

Exclusions:
  - Forks: 2
  - Archived: 2
  - Visibility: 0
  - Topics: 0
  - Language: 0
  - Age: 0

Overrides:
  - Force included: 0
  - Force excluded: 0
============================================================
```

### Preview Generated Config
```bash
uv run python scripts/sync_repos.py --dry-run
```

Shows exactly what repos will be included without writing the file.

### Debug Filtering
If repos are missing:
1. Run with `--stats` to see exclusion reasons
2. Check repo topics: `gh repo view owner/repo --json repositoryTopics`
3. Check repo metadata: `gh repo view owner/repo --json isFork,isArchived,visibility,primaryLanguage`
4. Adjust filters or use force_include

## Advanced Usage

### Multiple Filter Configs
```bash
# Production projects
uv run python scripts/sync_repos.py \
  --filters config/collection/production-filters.yaml \
  --output config/collection/production.yaml

# Personal projects
uv run python scripts/sync_repos.py \
  --filters config/collection/personal-filters.yaml \
  --output config/collection/personal.yaml

# Experiments
uv run python scripts/sync_repos.py \
  --filters config/collection/experiment-filters.yaml \
  --output config/collection/experiments.yaml
```

Then collect from specific configs:
```bash
uv run github-pm --config config/collection/production.yaml
uv run github-pm --config config/collection/personal.yaml
```

### Scheduled Sync (via cron)
```bash
# Add to crontab: sync repos daily at 8am
0 8 * * * cd /path/to/github-pm && uv run python scripts/sync_repos.py
```

### CI/CD Integration
```yaml
# .github/workflows/sync-repos.yml
name: Sync Repositories
on:
  schedule:
    - cron: '0 8 * * *'  # Daily at 8am
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: cli/cli@v2
      - name: Sync repos
        run: uv run python scripts/sync_repos.py
      - name: Commit changes
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add config/collection/production.yaml
          git commit -m "chore: sync repositories" || exit 0
          git push
```

## Migration from Manual Lists

### Step 1: Backup Current Config
```bash
cp config/collection/production.yaml config/collection/production.yaml.backup
```

### Step 2: Configure Filters
Look at your manual list and create filters that match:
```yaml
# If you had these repos manually:
repositories:
  - owner: mpazaryna
    name: chiro
  - owner: mpazaryna
    name: github-pm
  - owner: j-bouchard
    name: ai-fundraising-v2

# Configure these filters:
owner: mpazaryna
additional_owners:
  - j-bouchard
filters:
  exclude_forks: true
  exclude_archived: true
```

### Step 3: Preview
```bash
uv run python scripts/sync_repos.py --dry-run
```

Compare output with your manual list.

### Step 4: Adjust Filters
If repos are missing, check why:
```bash
uv run python scripts/sync_repos.py --stats
```

Adjust filters or use force_include for specific repos.

### Step 5: Generate
```bash
uv run python scripts/sync_repos.py
```

### Step 6: Test
```bash
uv run github-pm --save-snapshot
```

Verify all expected repos are included.

## Tips

- **Start permissive, then restrict**: Begin with minimal filters, then add exclusions
- **Use topics liberally**: Tag repos with topics for easier filtering
- **Review stats regularly**: Run `--stats` monthly to see what's excluded
- **Force overrides sparingly**: Prefer topic-based filters over force_include
- **Document filter rationale**: Add comments in repo_filters.yaml explaining why
- **Test before production**: Always use `--dry-run` before regenerating production config
- **Version control filters**: Commit repo_filters.yaml changes with explanations

## Troubleshooting

### No repos after filtering
- Run `--stats` to see exclusion reasons
- Check if visibility filter is too restrictive
- Verify owner name is correct
- Check if all repos are forks/archived

### Missing specific repo
- Check if it's a fork: `gh repo view owner/repo --json isFork`
- Check if it's archived: `gh repo view owner/repo --json isArchived`
- Add to force_include as temporary solution
- Adjust filters to include similar repos

### Too many repos
- Add exclude_topics to filter out unwanted categories
- Use language filtering to narrow scope
- Set min_days_since_update to focus on active repos
- Use force_exclude for specific repos

### Sync errors
- Verify `gh` CLI is installed: `gh --version`
- Check authentication: `gh auth status`
- Ensure owner name is correct (case-sensitive)
- Check rate limiting: `gh api rate_limit`
