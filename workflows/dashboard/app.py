"""Streamlit dashboard for GitHub PM analytics."""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.github_pm.data_collector import DataCollector

# Page config
st.set_page_config(
    page_title="Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize data collector
data_collector = DataCollector()

# Sidebar - Snapshot Selection
st.sidebar.header("📸 Snapshot Selection")

# Get available snapshots
sod_snapshots = data_collector.list_snapshots("sod")
eod_snapshots = data_collector.list_snapshots("eod")

snapshot_source = st.sidebar.radio(
    "Data Source",
    ["Latest SOD", "Latest EOD", "Select Date"],
    index=0,
)

# Determine which snapshot to load
snapshot_identifier = None

if snapshot_source == "Latest SOD":
    snapshot_identifier = "sod"
    snapshot_label = "SOD"
elif snapshot_source == "Latest EOD":
    snapshot_identifier = "eod"
    snapshot_label = "EOD"
else:  # Select Date
    available_dates = sorted(set(
        [s.stem.rsplit('-', 1)[0] for s in sod_snapshots + eod_snapshots]
    ), reverse=True)

    if available_dates:
        selected_date = st.sidebar.selectbox("Date", available_dates)
        snapshot_type = st.sidebar.radio("Type", ["SOD", "EOD"])
        snapshot_identifier = f"{selected_date}-{snapshot_type.lower()}"
        snapshot_label = f"{snapshot_type} ({selected_date})"
    else:
        st.sidebar.error("No snapshots available. Run `uv run dashboard start --sod` first.")
        st.stop()

st.sidebar.info(f"📸 **{snapshot_label}**")

# Refresh button
if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Main content
st.title("📊 Dashboard")

# Load snapshot data
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_snapshot_data(snapshot_id):
    """Load data from snapshot file."""
    try:
        snapshot = data_collector.load_snapshot(snapshot_id)
        return snapshot
    except FileNotFoundError:
        st.error(f"Snapshot not found: {snapshot_id}")
        st.error("Please run `uv run dashboard start --sod` to create a snapshot first.")
        return None
    except Exception as e:
        st.error(f"Error loading snapshot: {e}")
        return None

def parse_snapshot_for_dashboard(snapshot):
    """Parse snapshot data for dashboard display."""
    if not snapshot:
        return None

    issues = snapshot.get("issues", [])
    summary = snapshot.get("summary", {})
    metadata = snapshot.get("metadata", {})

    # Count issues by state
    open_issues = sum(1 for issue in issues if issue.get("state") == "OPEN")
    closed_issues = sum(1 for issue in issues if issue.get("state") == "CLOSED")

    # Count by status labels (from GitHub Projects synced labels)
    # Note: "done" is determined by CLOSED state, not a label
    status_counts = {"backlog": 0, "ready": 0, "in_progress": 0, "in_review": 0, "done": closed_issues}

    for issue in issues:
        # Only count OPEN issues in workflow states
        if issue.get("state") != "OPEN":
            continue

        labels = [l.get("name", "").lower() for l in issue.get("labels", [])]

        # Check for status:* labels (supports multiple formats)
        if any("status:ready" in l or l == "ready" for l in labels):
            status_counts["ready"] += 1
        elif any("status:progress" in l or "status:in progress" in l or "status:wip" in l or "in progress" in l or l == "wip" for l in labels):
            status_counts["in_progress"] += 1
        elif any("status:review" in l or "status:in review" in l or "in review" in l for l in labels):
            status_counts["in_review"] += 1
        elif any("status:backlog" in l or l == "backlog" for l in labels):
            status_counts["backlog"] += 1
        else:
            # No status label = backlog by default
            status_counts["backlog"] += 1

    # Count by label type
    label_counts = {}
    for issue in issues:
        for label in issue.get("labels", []):
            label_name = label.get("name", "")
            label_counts[label_name] = label_counts.get(label_name, 0) + 1

    # Get repositories
    repos = summary.get("by_repository", {})

    return {
        "metadata": metadata,
        "total_issues": len(issues),
        "open_issues": open_issues,
        "closed_issues": closed_issues,
        "status_counts": status_counts,
        "label_counts": label_counts,
        "repos_active": len(repos),
        "repositories": repos,
        "issues": issues,
    }

# Load snapshot data
with st.spinner("Loading snapshot data..."):
    snapshot = load_snapshot_data(snapshot_identifier)
    data = parse_snapshot_for_dashboard(snapshot)

    if not data:
        st.error("Failed to load snapshot data")
        st.stop()

# Metrics Row 1 - Issue Status
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Issues",
        data["total_issues"],
    )

with col2:
    st.metric(
        "Open Issues",
        data["open_issues"],
    )

with col3:
    st.metric(
        "Active Repos",
        data["repos_active"],
    )

with col4:
    snapshot_date = data["metadata"].get("snapshot_date", "Unknown")
    snapshot_type = data["metadata"].get("snapshot_type", "Unknown")
    st.metric(
        "Snapshot",
        snapshot_type,
        delta=snapshot_date,
    )

st.divider()

# Metrics Row 2 - Status Flow
st.info("ℹ️ **Status Flow**: Add `status:ready`, `status:progress` (or `status:in progress`), `status:review` (or `status:in review`) labels to track workflow. Open issues without labels = Backlog. Closed issues = Done.")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Backlog",
        data["status_counts"]["backlog"],
        help="Open issues without workflow status labels",
    )

with col2:
    st.metric(
        "Ready",
        data["status_counts"]["ready"],
        help="Open issues labeled 'status:ready'",
    )

with col3:
    st.metric(
        "In Progress",
        data["status_counts"]["in_progress"],
        help="Open issues labeled 'status:in progress'",
    )

with col4:
    st.metric(
        "In Review",
        data["status_counts"]["in_review"],
        help="Open issues labeled 'status:in review'",
    )

with col5:
    st.metric(
        "Done",
        data["status_counts"]["done"],
        help="Closed issues (no label needed)",
    )

st.divider()

# Two column layout
col1, col2 = st.columns(2)

# Label Distribution Chart
with col1:
    st.subheader("🏷️ Label Distribution")
    import pandas as pd

    if data["label_counts"]:
        # Show top 10 labels
        sorted_labels = sorted(data["label_counts"].items(), key=lambda x: x[1], reverse=True)[:10]
        label_df = pd.DataFrame(sorted_labels, columns=["Label", "Count"])
        st.bar_chart(label_df.set_index("Label"))
    else:
        st.info("No labels found in issues")

# Repository Activity
with col2:
    st.subheader("📂 Repository Activity")
    if data["repositories"]:
        import pandas as pd

        repo_df = pd.DataFrame(
            list(data["repositories"].items()),
            columns=["Repository", "Issues"],
        ).sort_values("Issues", ascending=False)

        st.dataframe(
            repo_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No repository data in this snapshot")

# Issues Table
st.divider()
st.subheader("📋 Issues")

if data["issues"]:
    # Filter options
    col1, col2 = st.columns(2)

    with col1:
        state_filter = st.selectbox("State", ["All", "OPEN", "CLOSED"])

    with col2:
        repo_filter = st.selectbox("Repository", ["All"] + sorted(data["repositories"].keys()))

    # Filter issues
    filtered_issues = data["issues"]

    if state_filter != "All":
        filtered_issues = [i for i in filtered_issues if i.get("state") == state_filter]

    if repo_filter != "All":
        filtered_issues = [i for i in filtered_issues if i.get("repository") == repo_filter]

    # Display issues
    st.caption(f"Showing {len(filtered_issues)} of {len(data['issues'])} issues")

    for issue in filtered_issues[:20]:  # Show first 20
        state_emoji = "🟢" if issue.get("state") == "OPEN" else "⚪"
        labels = ", ".join([l.get("name", "") for l in issue.get("labels", [])[:3]])

        with st.expander(f"{state_emoji} #{issue.get('number')} - {issue.get('title')}"):
            col1, col2 = st.columns(2)

            with col1:
                st.caption(f"**Repository:** {issue.get('repository', 'Unknown')}")
                st.caption(f"**State:** {issue.get('state', 'Unknown')}")

            with col2:
                if labels:
                    st.caption(f"**Labels:** {labels}")
                if issue.get("milestone"):
                    st.caption(f"**Milestone:** {issue['milestone'].get('title', 'Unknown')}")

            if issue.get("url"):
                st.caption(f"[View on GitHub]({issue['url']})")

else:
    st.info("No issues in this snapshot")

# Footer
st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
