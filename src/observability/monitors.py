from __future__ import annotations

"""Datadog monitors — trust-oriented alerting for the agent fleet.

v2: Alert on *trust*, not just failure. These monitors answer:
  "Is the fleet safe to run unsupervised right now?"
"""

import logging
from typing import Optional

import httpx

from ..config import DatadogConfig

logger = logging.getLogger(__name__)

P = "shieldops"

MONITORS = [
    # 1. Fleet needs babysitting
    {
        "name": "[ShieldOps] Intervention Rate Spiking",
        "type": "metric alert",
        "query": f"avg(last_1h):avg:{P}.devin.intervention_rate{{*}} > 40",
        "message": (
            "🤖 ShieldOps: The fleet needs babysitting.\n\n"
            "{{#is_alert}}\n"
            "More than 40% of Devin sessions needed human follow-up messages. "
            "This means the fleet is not running autonomously — investigate prompt quality, "
            "session configs, or repo access issues.\n"
            "{{/is_alert}}\n\n"
            "{{#is_recovery}}\n"
            "✅ Intervention rate back to normal — fleet running autonomously.\n"
            "{{/is_recovery}}"
        ),
        "tags": ["shieldops", "trust", "fleet"],
        "options": {"thresholds": {"critical": 40, "warning": 25}, "notify_no_data": False},
    },
    # 2. Policy safety net — should never fire, proves the boundary works
    {
        "name": "[ShieldOps] Low-Confidence Change Auto-Merged",
        "type": "metric alert",
        "query": (
            f"avg(last_15m):avg:{P}.remediation.confidence{{decision:auto_merge_ready}} < 0.8"
        ),
        "message": (
            "🚨 ShieldOps: A change was routed to auto-merge with confidence below 80%.\n\n"
            "{{#is_alert}}\n"
            "The policy boundary may have a gap. This monitor should *never* fire — "
            "if it does, review the policy engine logic immediately.\n"
            "{{/is_alert}}"
        ),
        "tags": ["shieldops", "trust", "safety-net"],
        "options": {"thresholds": {"critical": 0.8}, "notify_no_data": False},
    },
    # 3. Agent stuck
    {
        "name": "[ShieldOps] Devin Session Stuck > 30 Minutes",
        "type": "metric alert",
        "query": f"avg(last_30m):avg:{P}.devin.sessions.active{{*}} > 0",
        "message": (
            "⏱️ ShieldOps: A Devin session appears stuck.\n\n"
            "{{#is_alert}}\n"
            "A session has been active for >30 minutes. Check if it's blocked "
            "and needs a human intervention message.\n"
            "{{/is_alert}}"
        ),
        "tags": ["shieldops", "fleet", "health"],
        "options": {"thresholds": {"critical": 0}, "notify_no_data": False},
    },
    # 4. Cost guardrail
    {
        "name": "[ShieldOps] ACU Cost Per Fix Exceeding Budget",
        "type": "metric alert",
        "query": f"avg(last_1h):avg:{P}.devin.cost_acu{{*}} > 8",
        "message": (
            "💰 ShieldOps: Cost per fix is exceeding budget.\n\n"
            "{{#is_alert}}\n"
            "Average ACU cost per session is above 8 ACU. Review session prompts "
            "and max_acu_limit settings. Consider narrowing prompt scope.\n"
            "{{/is_alert}}"
        ),
        "tags": ["shieldops", "cost", "budget"],
        "options": {"thresholds": {"critical": 8, "warning": 5}, "notify_no_data": False},
    },
    # 5. Critical vuln SLO
    {
        "name": "[ShieldOps] Critical Vulnerability Open > 4 Hours",
        "type": "metric alert",
        "query": f"avg(last_4h):avg:{P}.vulnerabilities.by_severity{{severity:critical}} > 0",
        "message": (
            "⚠️ ShieldOps: Critical vulnerability unresolved for 4+ hours.\n\n"
            "{{#is_alert}}\n"
            "Review the ShieldOps dashboard and check Devin session status.\n"
            "{{/is_alert}}"
        ),
        "tags": ["shieldops", "security", "slo"],
        "options": {"thresholds": {"critical": 0}, "notify_no_data": False},
    },
    # 6. Scanner health
    {
        "name": "[ShieldOps] No Scans Completed in 24 Hours",
        "type": "metric alert",
        "query": f"sum(last_24h):sum:{P}.scan.vulnerabilities_found{{*}}.as_count() < 1",
        "message": (
            "🔍 ShieldOps: Scanner may be down.\n\n"
            "{{#is_alert}}\n"
            "No scans completed in 24h. Verify the ShieldOps container is running.\n"
            "{{/is_alert}}"
        ),
        "tags": ["shieldops", "scanner", "health"],
        "options": {"thresholds": {"critical": 1}, "notify_no_data": True, "no_data_timeframe": 1440},
    },
]


class MonitorBuilder:
    """Creates trust-oriented Datadog monitors."""

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
