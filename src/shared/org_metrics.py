from __future__ import annotations

"""Shared helpers for computing organization-level metrics.

Both ``api/orgs.py`` and ``api/dashboard.py`` aggregate vulnerability and session
data from an organization's repositories.  The core computations (vulns by
severity, fix rate, MTTR, active session count) were duplicated across both
endpoints.  This module provides the canonical implementations.
"""

from datetime import datetime
from typing import Optional, Sequence

from ..db.models import VulnSeverity, VulnStatus, SessionStatus


def vulns_by_severity(vulns: Sequence) -> dict[str, int]:
    """Count vulnerabilities grouped by severity."""
    return {
        severity.value: sum(1 for v in vulns if v.severity == severity)
        for severity in VulnSeverity
    }


def vulns_by_status(vulns: Sequence) -> dict[str, int]:
    """Count vulnerabilities grouped by status."""
    return {
        status.value: sum(1 for v in vulns if v.status == status)
        for status in VulnStatus
    }


def compute_fix_rate(vulns: Sequence) -> float:
    """Percentage of vulnerabilities that are fixed or ignored."""
    total = len(vulns)
    if total == 0:
        return 100.0
    fixed = sum(
        1 for v in vulns
        if v.status in (VulnStatus.FIXED, VulnStatus.IGNORED)
    )
    return (fixed / total) * 100


def count_active_sessions(sessions: Sequence) -> int:
    """Count sessions in a non-terminal state."""
    return sum(
        1 for s in sessions
        if s.status in (SessionStatus.PENDING, SessionStatus.RUNNING)
    )


def compute_mttr_hours(
    sessions: Sequence,
    *,
    since: Optional[datetime] = None,
) -> float:
    """Mean time to resolution in hours from completed sessions.

    Args:
        sessions: Iterable of session model objects.
        since: If provided, only consider sessions completed after this datetime.
    """
    completed = [
        s for s in sessions
        if (
            s.status == SessionStatus.COMPLETED
            and s.duration_seconds
            and (since is None or (s.completed_at and s.completed_at >= since))
        )
    ]
    if not completed:
        return 0.0
    return sum(s.duration_seconds for s in completed) / len(completed) / 3600
