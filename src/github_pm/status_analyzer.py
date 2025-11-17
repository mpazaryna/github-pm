"""Analyze issue status and flow health."""

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any


class StatusAnalyzer:
    """Analyzes issue status and workflow health."""

    # Common status label patterns
    STATUS_PATTERNS = {
        "backlog": ["backlog", "status:backlog", "status: backlog"],
        "ready": ["ready", "status:ready", "status: ready", "to do", "todo"],
        "in_progress": [
            "in progress",
            "status:in progress",
            "status: in progress",
            "in-progress",
            "status:in-progress",
            "wip",
            "work in progress",
        ],
        "in_review": [
            "in review",
            "status:in review",
            "status: in review",
            "review",
            "status:review",
        ],
        "done": ["done", "status:done", "status: done", "completed"],
    }

    def extract_status(self, issue: dict[str, Any]) -> str:
        """
        Extract status from issue labels.

        Args:
            issue: Issue dictionary

        Returns:
            Status string (backlog, ready, in_progress, in_review, done, unknown)
        """
        labels = issue.get("labels", [])
        label_names = [l.get("name", "").lower() for l in labels]

        # Check each status pattern
        for status, patterns in self.STATUS_PATTERNS.items():
            for pattern in patterns:
                if pattern in label_names:
                    return status

        # Default to backlog if open, done if closed
        state = issue.get("state", "UNKNOWN")
        if state == "CLOSED":
            return "done"
        return "backlog"

    def analyze_status_distribution(
        self, issues: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Analyze status distribution across issues.

        Args:
            issues: List of issues

        Returns:
            Status distribution analysis
        """
        status_counts = Counter()
        issues_by_status = defaultdict(list)

        for issue in issues:
            # Only analyze open issues for workflow statuses
            if issue.get("state") == "CLOSED":
                status = "done"
            else:
                status = self.extract_status(issue)

            status_counts[status] += 1
            issues_by_status[status].append(issue)

        return {
            "counts": dict(status_counts),
            "by_status": dict(issues_by_status),
        }

    def analyze_flow_health(
        self, status_distribution: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Analyze workflow health and identify bottlenecks.

        Args:
            status_distribution: Status distribution from analyze_status_distribution

        Returns:
            Flow health analysis
        """
        counts = status_distribution["counts"]

        # Calculate flow metrics
        ready = counts.get("ready", 0)
        in_progress = counts.get("in_progress", 0)
        in_review = counts.get("in_review", 0)
        backlog = counts.get("backlog", 0)

        bottlenecks = []
        recommendations = []

        # Check for bottlenecks
        if ready > in_progress * 3 and ready > 5:
            bottlenecks.append(
                {
                    "type": "ready_pileup",
                    "severity": "high",
                    "message": f"{ready} issues 'Ready' but only {in_progress} 'In Progress'",
                }
            )
            recommendations.append(
                f"Pick up more 'Ready' work - you have {ready} groomed issues waiting"
            )

        if in_progress > 5 and in_review == 0:
            bottlenecks.append(
                {
                    "type": "no_reviews",
                    "severity": "medium",
                    "message": f"{in_progress} issues 'In Progress' but none 'In Review'",
                }
            )
            recommendations.append(
                "No issues in review - remember to create PRs when work is done"
            )

        if in_review > 5:
            bottlenecks.append(
                {
                    "type": "review_bottleneck",
                    "severity": "high",
                    "message": f"{in_review} issues stuck 'In Review'",
                }
            )
            recommendations.append(
                f"Review bottleneck - prioritize reviewing the {in_review} pending PRs"
            )

        if backlog > ready * 5 and ready < 3:
            bottlenecks.append(
                {
                    "type": "grooming_needed",
                    "severity": "medium",
                    "message": f"{backlog} issues in 'Backlog' but only {ready} 'Ready'",
                }
            )
            recommendations.append(
                "Need grooming session - move backlog issues to 'Ready'"
            )

        # Calculate WIP limit health
        wip_total = in_progress + in_review
        ideal_wip = 3  # Healthy WIP limit for small team
        wip_health = "healthy" if wip_total <= ideal_wip else "overloaded"

        if wip_total > ideal_wip:
            recommendations.append(
                f"WIP too high ({wip_total} items) - focus on finishing before starting new work"
            )

        return {
            "wip_total": wip_total,
            "wip_health": wip_health,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "flow_ratio": {
                "ready": ready,
                "in_progress": in_progress,
                "in_review": in_review,
            },
        }

    def analyze_milestone_progress(
        self, issues: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Analyze progress towards milestones.

        Args:
            issues: List of issues

        Returns:
            Milestone progress analysis
        """
        milestones = defaultdict(lambda: {
            "total": 0,
            "done": 0,
            "in_progress": 0,
            "in_review": 0,
            "ready": 0,
            "backlog": 0,
            "issues": [],
        })

        for issue in issues:
            milestone = issue.get("milestone")
            if not milestone:
                milestone_key = "No Milestone"
                milestone_data = {"title": "No Milestone", "due_on": None}
            else:
                milestone_key = milestone.get("title", "Unknown")
                milestone_data = milestone

            status = self.extract_status(issue)
            milestones[milestone_key]["total"] += 1
            milestones[milestone_key][status] += 1
            milestones[milestone_key]["issues"].append(issue)

            # Store milestone metadata
            if "metadata" not in milestones[milestone_key]:
                milestones[milestone_key]["metadata"] = milestone_data

        # Calculate progress and health for each milestone
        for milestone_name, data in milestones.items():
            total = data["total"]
            done = data["done"]
            progress_pct = (done / total * 100) if total > 0 else 0

            # Calculate health
            due_date = None
            if data.get("metadata") and data["metadata"].get("due_on"):
                try:
                    due_date = datetime.fromisoformat(
                        data["metadata"]["due_on"].replace("Z", "+00:00")
                    )
                    days_remaining = (due_date - datetime.now()).days

                    # Estimate needed velocity
                    remaining_issues = total - done
                    weeks_remaining = max(days_remaining / 7, 0.1)
                    needed_velocity = remaining_issues / weeks_remaining

                    # Current velocity estimate (rough)
                    current_velocity = 1.5  # issues per week (conservative estimate)

                    if days_remaining < 0:
                        health = "overdue"
                    elif needed_velocity > current_velocity * 2:
                        health = "at_risk"
                    elif needed_velocity > current_velocity * 1.5:
                        health = "behind"
                    elif progress_pct > 80:
                        health = "on_track"
                    else:
                        health = "good"

                    data["due_date"] = due_date.strftime("%Y-%m-%d")
                    data["days_remaining"] = days_remaining
                    data["needed_velocity"] = round(needed_velocity, 1)
                except:
                    health = "unknown"
            else:
                health = "no_deadline"

            data["progress_pct"] = round(progress_pct, 1)
            data["health"] = health

        return dict(milestones)

    def get_priority_issues_by_status(
        self, issues: list[dict[str, Any]], status: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Get priority issues for a given status.

        Args:
            issues: List of issues
            status: Status to filter by
            limit: Maximum issues to return

        Returns:
            List of priority issues
        """
        filtered = [i for i in issues if self.extract_status(i) == status]

        # Sort by priority
        # Priority order: has milestone > has priority label > created recently
        def priority_score(issue):
            score = 0

            # Has milestone with due date
            milestone = issue.get("milestone")
            if milestone and milestone.get("due_on"):
                score += 100

            # Has priority label
            labels = [l.get("name", "").lower() for l in issue.get("labels", [])]
            if any(p in labels for p in ["critical", "high-priority", "urgent", "bug"]):
                score += 50

            # Recently created (boost newer issues)
            created = issue.get("createdAt", "")
            if created:
                try:
                    created_date = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    days_old = (datetime.now() - created_date).days
                    score += max(0, 30 - days_old)  # Boost if < 30 days old
                except:
                    pass

            return score

        sorted_issues = sorted(filtered, key=priority_score, reverse=True)
        return sorted_issues[:limit]
