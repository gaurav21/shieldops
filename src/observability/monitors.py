from __future__ import annotations

"""
Datadog monitors — trust-oriented alerting for the agent fleet.
V1 monitors kept, V2 trust monitors added.
"""

import logging
from typing import Optional

import httpx

from ..config import DatadogConfig

logger = logging.getLogger(__name__)

P = "shieldops"

MONITORS = [
    # === V1 (kept) ===
    {
        "name": "[ShieldOps] Devin Session Failure Rate High",
        "type": "metric alert",
        "query": (
            f"sum(last_1h):sum:{P}.devin.sessions.failed{{*}}.as_count() / "
            f"sum:{P}.devin.sessions.created{{*}}.as_count() * 100 > 30"
        ),
        "message": "🚨 ShieldOps: >30% of Devin sessions are failing in the last hour.",
        "tags": ["shieldops", "devin", "security"],
        "options": {"thresholds": {"critical": 30, "warning": 20}, "notify_no_data": False},
    },
    {
        "name": "[ShieldOps] Critical Vulnerability Open > 4 Hours",
        "type": "metric alert",
        "query": f"avg(last_4h):avg:{P}.vulnerabilities.by_severity{{severity:critical}} > 0",
        "message": "⚠️ ShieldOps: Critical vulnerability unresolved for 4+ hours.",
        "tags": ["shieldops", "security", "slo"],
        "options": {"thresholds": {"critical": 0}, "notify_no_data": False},
    },
    {
        "name": "[ShieldOps] No Scans Completed in 24 Hours",
        "type": "metric alert",
        "query": f"sum(last_24h):sum:{P}.scan.vulnerabilities_found{{*}}.as_count() < 1",
        "message": "🔍 ShieldOps: Scanner may be down — no scans in 24h.",
        "tags": ["shieldops", "scanner", "health"],
        "options": {"thresholds": {"critical": 1}, "notify_no_data": True, "no_data_timeframe": 1440},
    },

    # === V2 Trust monitors (new) ===
    {
        "name": "[ShieldOps] Devin Fleet Needs Babysitting",
        "type": "metric alert",
        "query": f"avg(last_15m):avg:{P}.devin.needed_intervention{{*}} > 0.4",
        "message": (
            "More than 40% of active Devin sessions required a follow-up message in the last "
            "15 minutes. The fleet may be stuck on a hard class of vulnerability. "
            "@slack-shieldops-alerts"
        ),
        "tags": ["shieldops", "trust", "intervention"],
        "options": {"thresholds": {"critical": 0.4, "warning": 0.25}, "notify_no_data": False},
    },
    {
        "name": "[ShieldOps] ⚠️ Auto-Merge Fired with Low Confidence — Policy Boundary Breach",
        "type": "metric alert",
        "query": (
            f"avg(last_5m):avg:{P}.remediation.confidence{{decision:auto_merge_ready}} < 0.8"
        ),
        "message": (
            "A change was routed to AUTO_MERGE_READY with confidence below 0.8. "
            "This should never happen if the policy engine is working correctly. "
            "Investigate immediately. @pagerduty-shieldops"
        ),
        "tags": ["shieldops", "trust", "policy-breach"],
        "options": {"thresholds": {"critical": 0.8}, "notify_no_data": False},
    },
    {
        "name": "[ShieldOps] Devin Session Stuck",
        "type": "metric alert",
        "query": f"min(last_30m):min:{P}.devin.sessions.active{{*}} > 0",
        "message": (
            "A Devin session has been active for > 30 minutes without reaching a terminal state. "
            "It may be stuck. Session ID available in the event stream. @slack-shieldops-alerts"
        ),
        "tags": ["shieldops", "trust", "stuck"],
        "options": {"thresholds": {"critical": 1}, "notify_no_data": False},
    },
]


class MonitorBuilder:
    """Creates Datadog monitors."""

    def __init__(self, config: DatadogConfig):
        self.config = config
        self.base_url = f"https://api.{config.site}/api/v1"
        self.headers = {
            "DD-API-KEY": config.api_key,
            "DD-APPLICATION-KEY": config.app_key,
            "Content-Type": "application/json",
        }

    async def create_all(self) -> list[dict]:
        if not self.config.api_key or not self.config.app_key:
            logger.warning("No DD keys — skipping monitor creation")
            return []

        created = []
        async with httpx.AsyncClient(timeout=15) as client:
            for monitor_def in MONITORS:
                try:
                    resp = await client.post(f"{self.base_url}/monitor",
                                            headers=self.headers, json=monitor_def)
                    resp.raise_for_status()
                    data = resp.json()
                    created.append({"id": data["id"], "name": data["name"]})
                    logger.info(f"Created monitor: {data['name']} (ID: {data['id']})")
                except httpx.HTTPError as e:
                    logger.error(f"Failed to create monitor '{monitor_def['name']}': {e}")
        return created
