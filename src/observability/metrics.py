from __future__ import annotations

"""
Datadog metrics via DogStatsD.
V2: Fleet health, trust split, cost, breaking-change metrics alongside V1 vulnerability metrics.
"""

import logging
import time
from typing import Optional

from datadog import statsd
import httpx

from ..config import DatadogConfig

logger = logging.getLogger(__name__)


# ========== V1 — Vulnerability posture (kept) ==========

def record_scan_completed(scanner: str, vuln_count: int, duration_seconds: float):
    statsd.gauge("shieldops.scan.vulnerabilities_found", vuln_count, tags=[f"scanner:{scanner}"])
    statsd.gauge("shieldops.scan.duration_seconds", duration_seconds, tags=[f"scanner:{scanner}"])


def record_vulnerability_counts(open_count: int, fixed_count: int):
    statsd.gauge("shieldops.vulnerabilities.open", open_count)
    statsd.gauge("shieldops.vulnerabilities.fixed", fixed_count)


def record_vulnerability_by_severity(severity: str, count: int):
    statsd.gauge("shieldops.vulnerabilities.by_severity", count, tags=[f"severity:{severity}"])


def record_session_created(session_id: str, severity: str, package: str):
    statsd.increment("shieldops.devin.sessions.created",
                     tags=[f"session_id:{session_id}", f"severity:{severity}", f"package:{package}"])


def record_session_completed(session_id: str, severity: str, duration_seconds: float):
    statsd.increment("shieldops.devin.sessions.completed",
                     tags=[f"session_id:{session_id}", f"severity:{severity}"])
    statsd.gauge("shieldops.devin.session.duration_seconds", duration_seconds,
                 tags=[f"session_id:{session_id}", f"severity:{severity}"])


def record_session_failed(session_id: str, severity: str):
    statsd.increment("shieldops.devin.sessions.failed",
                     tags=[f"session_id:{session_id}", f"severity:{severity}"])


def record_active_sessions(count: int):
    statsd.gauge("shieldops.devin.sessions.active", count)


# ========== V2 — Fleet trust metrics (new) ==========

def record_policy_decision(decision: str, severity: str, upgrade_type: str):
    """Emit when the policy engine routes a remediation."""
    statsd.increment(
        "shieldops.policy.decision",
        tags=[
            f"decision:{decision}",
            f"severity:{severity}",
            f"upgrade_type:{upgrade_type}",
        ],
    )


def record_breaking_change_handled(package: str, severity: str):
    """Emit when Devin successfully handles a breaking-change upgrade."""
    statsd.increment(
        "shieldops.remediation.breaking_changes_handled",
        tags=[f"package:{package}", f"severity:{severity}"],
    )


def record_time_to_merged_verified(seconds: int, severity: str, upgrade_type: str):
    """
    Real MTTR: time from vulnerability detected to PR merged and verified.
    This is the metric that replaces 'time to open a PR'.
    """
    statsd.gauge(
        "shieldops.remediation.time_to_merged_verified_seconds",
        seconds,
        tags=[f"severity:{severity}", f"upgrade_type:{upgrade_type}"],
    )


def record_confidence(confidence: float, decision: str):
    """Distribution of Devin's self-reported confidence per session."""
    statsd.gauge(
        "shieldops.remediation.confidence",
        confidence,
        tags=[f"decision:{decision}"],
    )


def record_acu_cost(acu_used: float, session_id: str, severity: str):
    """Cost per session in ACU units — feeds cost-per-fix calculation."""
    statsd.gauge(
        "shieldops.devin.cost_acu",
        acu_used,
        tags=[f"session_id:{session_id}", f"severity:{severity}"],
    )


def record_reviewer_minutes_saved(minutes_saved: float, decision: str):
    """
    Estimated review time saved vs. manual remediation.
    Baseline assumption: manual fix = 45 min for patch/minor, 120 min for major.
    Auto-merge-ready saves the full baseline. Human-review saves 80%.
    """
    statsd.gauge(
        "shieldops.remediation.reviewer_minutes_saved",
        minutes_saved,
        tags=[f"decision:{decision}"],
    )
    statsd.increment(
        "shieldops.remediation.reviewer_minutes_saved_cumulative",
        int(minutes_saved),
        tags=[f"decision:{decision}"],
    )


def record_unreachable_vuln_deprioritized(count: int):
    """Track how many CVEs were deprioritized because the code path is unreachable."""
    statsd.gauge("shieldops.triage.unreachable_deprioritized", count)


# ========== Datadog Event API (for lifecycle events) ==========

class EventEmitter:
    """Sends events to Datadog via HTTP API (events don't go through StatsD)."""

    def __init__(self, config: DatadogConfig):
        self.config = config
        self.base_url = f"https://api.{config.site}/api/v1"
        self.headers = {
            "DD-API-KEY": config.api_key,
            "Content-Type": "application/json",
        }

    async def send_event(self, title: str, text: str, alert_type: str = "info",
                         tags: Optional[list[str]] = None):
        if not self.config.api_key:
            logger.debug(f"No DD API key — event: {title}")
            return
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{self.base_url}/events", headers=self.headers,
                    json={"title": title, "text": text, "alert_type": alert_type,
                          "source_type_name": "shieldops", "tags": tags or []})
                if resp.status_code in (200, 202):
                    logger.debug(f"Event sent: {title}")
        except Exception as e:
            logger.error(f"Failed to send event: {e}")
