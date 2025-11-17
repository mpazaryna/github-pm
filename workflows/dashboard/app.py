"""Streamlit dashboard for GitHub PM analytics."""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from workflows.code_analysis.daily_activity import DailyActivityReportGenerator
from workflows.code_analysis.period_comparison import PeriodComparisonGenerator
from workflows.metrics.velocity_tracker import VelocityTracker
from workflows.planning.roadmap_generator import RoadmapGenerator

# Page config
st.set_page_config(
    page_title="Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize collectors
@st.cache_resource
def get_collectors():
    """Get cached data collectors."""
    return {
        "activity": DailyActivityReportGenerator(),
        "comparison": PeriodComparisonGenerator(),
        "velocity": VelocityTracker(),
        "roadmap": RoadmapGenerator(),
    }

collectors = get_collectors()

# Sidebar - Date Selection
st.sidebar.header("📅 Period Selection")

preset = st.sidebar.selectbox(
    "Preset",
    ["Today", "Yesterday", "Last 7 Days", "Last 14 Days", "Last 30 Days", "Last 90 Days", "Custom Range"],
    index=0,
)

# Calculate dates based on preset
now = datetime.now()
if preset == "Today":
    since_date = now - timedelta(days=1)
    until_date = now
elif preset == "Yesterday":
    until_date = now - timedelta(days=1)
    since_date = until_date - timedelta(days=1)
elif preset == "Last 7 Days":
    since_date = now - timedelta(days=7)
    until_date = now
elif preset == "Last 14 Days":
    since_date = now - timedelta(days=14)
    until_date = now
elif preset == "Last 30 Days":
    since_date = now - timedelta(days=30)
    until_date = now
elif preset == "Last 90 Days":
    since_date = now - timedelta(days=90)
    until_date = now
else:  # Custom Range
    col1, col2 = st.sidebar.columns(2)
    with col1:
        since_date = st.date_input(
            "From",
            value=now - timedelta(days=7),
            max_value=now,
        )
    with col2:
        until_date = st.date_input(
            "To",
            value=now,
            max_value=now,
        )

# Convert to strings
since = since_date.strftime("%Y-%m-%d")
until = until_date.strftime("%Y-%m-%d")

st.sidebar.info(f"📆 **{since}** to **{until}**")

# Refresh button
if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Main content
st.title("📊 Dashboard")

# Load data with caching
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_activity_data(since_str, until_str):
    """Load activity data."""
    since_dt = datetime.strptime(since_str, "%Y-%m-%d")
    until_dt = datetime.strptime(until_str, "%Y-%m-%d")
    days = (until_dt - since_dt).days

    try:
        data = collectors["activity"].generate_report(
            "config/collection/production.yaml",
            days=max(days, 1),
            format_type="both",
        )
        return {
            "commits": data["totals"]["commits"],
            "issues": len(data["totals"]["issues_referenced"]),
            "repos_active": len(data["repositories"]),
            "conventional_pct": (
                (data["totals"]["conventional_commits"] / data["totals"]["commits"] * 100)
                if data["totals"]["commits"] > 0
                else 0
            ),
            "repositories": data["repositories"],
            "commit_types": data["totals"]["commit_types"],
        }
    except Exception as e:
        st.error(f"Error loading activity data: {e}")
        return None

@st.cache_data(ttl=300)
def load_comparison_data(since_str, until_str):
    """Load comparison data."""
    since_dt = datetime.strptime(since_str, "%Y-%m-%d")
    until_dt = datetime.strptime(until_str, "%Y-%m-%d")
    days = (until_dt - since_dt).days

    try:
        comparison = collectors["comparison"].compare_periods(
            "config/collection/production.yaml",
            days=max(days, 1),
        )
        return {
            "current_commits": comparison["changes"]["commits"]["current"],
            "previous_commits": comparison["changes"]["commits"]["previous"],
            "commit_change": comparison["changes"]["commits"]["difference"],
            "current_issues": comparison["changes"]["issues"]["current"],
            "previous_issues": comparison["changes"]["issues"]["previous"],
            "issue_change": comparison["changes"]["issues"]["current"] - comparison["changes"]["issues"]["previous"],
        }
    except Exception as e:
        st.error(f"Error loading comparison data: {e}")
        return None

@st.cache_data(ttl=300)
def load_velocity_data():
    """Load velocity data."""
    try:
        report = collectors["velocity"].generate_velocity_report(
            "config/collection/production.yaml",
            cycles=6,
            cycle_length=7,
        )
        return {
            "avg_issues": report["averages"]["issues_per_cycle"],
            "avg_commits": report["averages"]["commits_per_cycle"],
            "quality_pct": report["averages"]["conventional_percentage"],
            "trend": report["trends"]["velocity"]["trend"] if report.get("trends") else "unknown",
        }
    except Exception as e:
        st.error(f"Error loading velocity data: {e}")
        return None

@st.cache_data(ttl=300)
def load_roadmap_data():
    """Load roadmap data."""
    try:
        roadmap = collectors["roadmap"].generate_roadmap(
            "config/collection/production.yaml",
            velocity_days=30,
        )

        critical = [
            m for m in roadmap["all_milestones"]
            if m["health"] in ["overdue", "at_risk"]
        ]

        return {
            "total_milestones": len(roadmap["all_milestones"]),
            "open_milestones": sum(1 for m in roadmap["all_milestones"] if m["state"] == "open"),
            "critical_milestones": critical,
        }
    except Exception as e:
        st.error(f"Error loading roadmap data: {e}")
        return None

# Load all data
with st.spinner("Loading dashboard data..."):
    activity = load_activity_data(since, until)
    comparison = load_comparison_data(since, until)
    velocity = load_velocity_data()
    roadmap = load_roadmap_data()

# Metrics Row 1 - Activity
if activity:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Commits",
            activity["commits"],
            delta=comparison["commit_change"] if comparison else None,
        )

    with col2:
        st.metric(
            "Issues Worked On",
            activity["issues"],
            delta=comparison["issue_change"] if comparison else None,
        )

    with col3:
        st.metric(
            "Active Repos",
            activity["repos_active"],
        )

    with col4:
        st.metric(
            "Code Quality",
            f"{activity['conventional_pct']:.1f}%",
        )

st.divider()

# Metrics Row 2 - Velocity & Roadmap
col1, col2, col3, col4 = st.columns(4)

if velocity:
    with col1:
        trend_emoji = {"improving": "📈", "declining": "📉", "stable": "➡️"}.get(velocity["trend"], "❓")
        st.metric(
            "Avg Issues/Week",
            f"{velocity['avg_issues']:.1f}",
            delta=f"{trend_emoji} {velocity['trend']}",
        )

    with col2:
        st.metric(
            "Avg Commits/Week",
            f"{velocity['avg_commits']:.1f}",
        )

if roadmap:
    with col3:
        st.metric(
            "Total Milestones",
            roadmap["total_milestones"],
        )

    with col4:
        critical_count = len(roadmap["critical_milestones"])
        st.metric(
            "Critical Milestones",
            critical_count,
            delta="Needs attention" if critical_count > 0 else "All on track",
            delta_color="inverse" if critical_count > 0 else "normal",
        )

st.divider()

# Two column layout
col1, col2 = st.columns(2)

# Work Distribution Chart
with col1:
    st.subheader("🔨 Work Distribution")
    if activity and activity["commit_types"]:
        import pandas as pd

        df = pd.DataFrame(
            list(activity["commit_types"].items()),
            columns=["Type", "Count"],
        )
        st.bar_chart(df.set_index("Type"))
    else:
        st.info("No commit data available for this period")

# Repository Activity
with col2:
    st.subheader("📂 Repository Activity")
    if activity and activity["repositories"]:
        import pandas as pd

        repo_data = {
            name: info["total_commits"]
            for name, info in activity["repositories"].items()
        }

        df = pd.DataFrame(
            list(repo_data.items()),
            columns=["Repository", "Commits"],
        ).sort_values("Commits", ascending=False)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No repository activity for this period")

# Critical Milestones
if roadmap and roadmap["critical_milestones"]:
    st.divider()
    st.subheader("⚠️ Critical Milestones")

    for milestone in roadmap["critical_milestones"]:
        health_emoji = "❌" if milestone["health"] == "overdue" else "🟠"

        with st.expander(f"{health_emoji} {milestone['title']} - {milestone['repository']}"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Progress", f"{milestone['progress_percentage']:.0f}%")

            with col2:
                st.metric("Completed", f"{milestone['completed']}/{milestone['total_issues']}")

            with col3:
                if milestone["health"] == "overdue":
                    st.metric("Status", f"Overdue by {abs(milestone['days_until_due'])} days")
                else:
                    st.metric("Predicted", f"{milestone['predicted_days_remaining']} days remaining")

            # Progress bar
            st.progress(milestone["progress_percentage"] / 100)

            if milestone.get("description"):
                st.caption(milestone["description"])

# Footer
st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
