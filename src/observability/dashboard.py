from __future__ import annotations

"""
Dashboard builder — creates the "ShieldOps — Agent Trust Control Plane" dashboard via Datadog API.
V2 widget order: Fleet → Trust → Dependabot-Can't → Cost → Posture → Audit.
"""

import logging
from typing import Optional

import httpx

from ..config import DatadogConfig
from .datadog_base import DatadogBaseClient

logger = logging.getLogger(__name__)

P = "shieldops"


def _qv(title, q, unit=None):
    """Query value widget shorthand."""
    w = {"definition": {"title": title, "type": "query_value",
         "requests": [{"q": q, "aggregator": "last"}], "precision": 0, "autoscale": True}}
    if unit:
        w["definition"]["custom_unit"] = unit
    return w


def _ts(title, requests):
    """Timeseries widget shorthand."""
    return {"definition": {"title": title, "type": "timeseries", "requests": requests}}


DASHBOARD_TITLE = "ShieldOps — Agent Trust Control Plane"

DASHBOARD_CONFIG = {
    "title": DASHBOARD_TITLE,
    "description": "Trust dashboard for an autonomous security remediation fleet. Devin AI + Datadog.",
    "layout_type": "ordered",
    "tags": ["shieldops", "security", "devin", "trust"],
    "widgets": [
        # === ROW 1: THE FLEET RIGHT NOW ===
        _qv("Active Sessions", f"avg:{P}.devin.sessions.active{{*}}"),
        _qv("Blocked / Stuck", f"avg:{P}.devin.sessions.blocked{{*}}"),
        _qv("ACU Burn Rate (1h)", f"sum:{P}.devin.cost_acu{{*}}", "ACU"),
        _qv("Intervention Rate", f"avg:{P}.devin.needed_intervention{{*}}", "%"),

        # === ROW 2: IS IT SAFE TO RUN? ===
        {"definition": {
            "title": "Trust Split: Auto vs Human vs Blocked",
            "type": "toplist",
            "requests": [{"q": f"sum:{P}.policy.decision{{*}} by {{decision}}.as_count()"}],
        }},
        _ts("Confidence Distribution", [
            {"q": f"avg:{P}.remediation.confidence{{*}} by {{decision}}", "display_type": "line"},
        ]),

        # === ROW 3: THE THING DEPENDABOT CAN'T DO ===
        _qv("Breaking Changes Handled", f"sum:{P}.remediation.breaking_changes_handled{{*}}.as_count()"),
        _ts("Time to Merged & Verified", [
            {"q": f"avg:{P}.remediation.time_to_merged_verified_seconds{{*}}",
             "display_type": "line", "style": {"palette": "orange", "line_width": "thick"}},
        ]),

        # === ROW 4: WHAT IS IT WORTH? ===
        _qv("Reviewer-Minutes Saved (Total)",
            f"sum:{P}.remediation.reviewer_minutes_saved_cumulative{{*}}.as_count()", "min"),
        _ts("ACU Cost per Session", [
            {"q": f"avg:{P}.devin.cost_acu{{*}} by {{session_id}}", "display_type": "bars",
             "style": {"palette": "warm"}},
        ]),

        # === ROW 5: SECURITY POSTURE (supporting cast) ===
        _ts("Open Vulnerabilities (Burn-Down)", [
            {"q": f"avg:{P}.vulnerabilities.open{{*}} by {{severity}}", "display_type": "area",
             "style": {"palette": "warm"}},
        ]),
        _ts("Vulns Found per Scan", [
            {"q": f"avg:{P}.scan.vulnerabilities_found{{*}} by {{scanner}}", "display_type": "bars"},
        ]),

        # === ROW 6: AUDIT ===
        {"definition": {
            "title": "Full Audit Trail (Every Scan, Session, Policy Decision, Merge)",
            "type": "event_stream",
            "query": "source:shieldops",
            "event_size": "s",
        }},
    ],
}


class DashboardBuilder(DatadogBaseClient):
    """Creates and manages the ShieldOps Datadog dashboard."""

    def __init__(self, config: DatadogConfig):
        super().__init__(config, api_version="v1", needs_app_key=True)

    async def create_or_update(self) -> Optional[str]:
        if not self.has_keys(need_app_key=True):
            logger.warning("No DD keys — skipping dashboard creation")
            return None

        existing_id = await self._find_existing()
        try:
            if existing_id:
                resp = await self._put(f"dashboard/{existing_id}",
                                       json=DASHBOARD_CONFIG, timeout=30)
            else:
                resp = await self._post("dashboard",
                                        json=DASHBOARD_CONFIG, timeout=30)
            if resp:
                resp.raise_for_status()
                data = resp.json()
                url = data.get("url", f"https://app.datadoghq.com/dashboard/{data.get('id')}")
                logger.info(f"Dashboard {'updated' if existing_id else 'created'}: {url}")
                return url
        except httpx.HTTPError as e:
            logger.error(f"Dashboard creation failed: {e}")
        return None

    async def _find_existing(self) -> Optional[str]:
        try:
            resp = await self._get("dashboard")
            if resp:
                resp.raise_for_status()
                for dash in resp.json().get("dashboards", []):
                    if "ShieldOps" in dash.get("title", ""):
                        return dash["id"]
        except httpx.HTTPError:
            pass
        return None
