from __future__ import annotations

"""ShieldOps Datadog Dashboard — the Agent Trust Control Plane.

v2: Fleet-first, posture-last. The dashboard answers:
  Row 1: What's the fleet doing right now?
  Row 2: Is it safe to run?
  Row 3: What can it do that Dependabot can't?
  Row 4: What is it worth?
  Row 5: Security posture (supporting cast)
  Row 6: Full audit trail
"""

import logging
from typing import Optional

import httpx

from ..config import DatadogConfig

logger = logging.getLogger(__name__)

P = "shieldops"  # metric prefix

DASHBOARD_CONFIG = {
    "title": "🛡️ ShieldOps — Agent Trust Control Plane",
    "description": (
        "Trust dashboard for an autonomous security remediation fleet. "
        "Powered by Devin AI + Datadog. Fleet first, posture second."
    ),
    "layout_type": "ordered",
    "tags": ["shieldops", "security", "devin", "trust"],
    "widgets": [
        # ======== ROW 1: THE FLEET RIGHT NOW ========
        {
            "definition": {
                "type": "group",
                "layout_type": "ordered",
                "title": "🤖 THE FLEET RIGHT NOW",
                "widgets": [
                    {
                        "definition": {
                            "title": "Active Sessions",
                            "type": "query_value",
                            "requests": [{"q": f"avg:{P}.devin.sessions.active{{*}}", "aggregator": "last"}],
                            "precision": 0,
                        },
                        "layout": {"x": 0, "y": 0, "width": 3, "height": 2},
                    },
                    {
                        "definition": {
                            "title": "Intervention Rate",
                            "type": "query_value",
                            "requests": [{"q": f"avg:{P}.devin.intervention_rate{{*}}", "aggregator": "last"}],
                            "precision": 1,
                            "custom_unit": "%",
                        },
                        "layout": {"x": 3, "y": 0, "width": 3, "height": 2},
                    },
                    {
                        "definition": {
                            "title": "Avg Confidence",
                            "type": "query_value",
                            "requests": [{"q": f"avg:{P}.remediation.avg_confidence{{*}}", "aggregator": "last"}],
                            "precision": 0,
                            "custom_unit": "%",
                        },
                        "layout": {"x": 6, "y": 0, "width": 3, "height": 2},
                    },
                    {
                        "definition": {
                            "title": "Success Rate",
                            "type": "query_value",
                            "requests": [{"q": f"avg:{P}.remediation.success_rate{{*}}", "aggregator": "last"}],
                            "precision": 1,
                            "custom_unit": "%",
                        },
                        "layout": {"x": 9, "y": 0, "width": 3, "height": 2},
                    },
                    {
                        "definition": {
                            "title": "Session Throughput",
                            "type": "timeseries",
                            "requests": [
                                {"q": f"sum:{P}.devin.sessions.created{{*}}.as_count()", "display_type": "bars", "style": {"palette": "blue"}},
                                {"q": f"sum:{P}.devin.sessions.completed{{*}}.as_count()", "display_type": "bars", "style": {"palette": "green"}},
                                {"q": f"sum:{P}.devin.sessions.failed{{*}}.as_count()", "display_type": "bars", "style": {"palette": "red"}},
                            ],
                        },
                        "layout": {"x": 0, "y": 2, "width": 12, "height": 3},
                    },
                ],
            },
        },

        # ======== ROW 2: IS IT SAFE TO RUN? (Trust Split) ========
        {
            "definition": {
                "type": "group",
                "layout_type": "ordered",
                "title": "🔒 IS IT SAFE TO RUN? — Trust Split",
                "widgets": [
                    {
                        "definition": {
                            "title": "Policy Routing (Auto vs Human vs Blocked)",
                            "type": "toplist",
                            "requests": [{
                                "q": f"sum:{P}.policy.auto_merge_ready{{*}}.as_count(), "
                                     f"sum:{P}.policy.human_review{{*}}.as_count(), "
                                     f"sum:{P}.policy.blocked{{*}}.as_count()",
                            }],
                        },
                        "layout": {"x": 0, "y": 0, "width": 6, "height": 3},
                    },
                    {
                        "definition": {
                            "title": "Confidence Distribution",
                            "type": "timeseries",
                            "requests": [{
                                "q": f"avg:{P}.remediation.confidence{{*}} by {{severity}}",
                                "display_type": "line",
                            }],
                        },
                        "layout": {"x": 6, "y": 0, "width": 6, "height": 3},
                    },
                ],
            },
        },

        # ======== ROW 3: THE THING DEPENDABOT CAN'T DO ========
        {
            "definition": {
                "type": "group",
                "layout_type": "ordered",
                "title": "⚡ THE THING DEPENDABOT CAN'T DO",
                "widgets": [
                    {
                        "definition": {
                            "title": "Breaking Changes Handled by Devin",
                            "type": "query_value",
                            "requests": [{"q": f"sum:{P}.remediation.breaking_changes_handled{{*}}.as_count()", "aggregator": "sum"}],
                            "precision": 0,
                        },
                        "layout": {"x": 0, "y": 0, "width": 4, "height": 2},
                    },
                    {
                        "definition": {
                            "title": "Time to Merged & Verified Fix",
                            "type": "timeseries",
                            "requests": [{
                                "q": f"avg:{P}.remediation.time_to_merged_verified_seconds{{*}}",
                                "display_type": "line",
                                "style": {"palette": "orange", "line_width": "thick"},
                            }],
                            "markers": [{"value": "y = 3600", "display_type": "error dashed", "label": "1h target"}],
                        },
                        "layout": {"x": 4, "y": 0, "width": 8, "height": 3},
                    },
                    {
                        "definition": {
                            "title": "Breaking Changes Trend",
                            "type": "timeseries",
                            "requests": [{
                                "q": f"sum:{P}.remediation.breaking_changes_handled{{*}}.as_count()",
                                "display_type": "bars",
                                "style": {"palette": "purple"},
                            }],
                        },
                        "layout": {"x": 0, "y": 2, "width": 4, "height": 3},
                    },
                ],
            },
        },

        # ======== ROW 4: WHAT IS IT WORTH? ========
        {
            "definition": {
                "type": "group",
                "layout_type": "ordered",
                "title": "💰 WHAT IS IT WORTH?",
                "widgets": [
                    {
                        "definition": {
                            "title": "Cost per Fix (ACU)",
                            "type": "timeseries",
                            "requests": [{
                                "q": f"avg:{P}.devin.cost_acu{{*}} by {{severity}}",
                                "display_type": "bars",
                                "style": {"palette": "warm"},
                            }],
                        },
                        "layout": {"x": 0, "y": 0, "width": 6, "height": 3},
                    },
                    {
                        "definition": {
                            "title": "Session Duration by Complexity",
                            "type": "timeseries",
                            "requests": [{
                                "q": f"avg:{P}.devin.session.duration_seconds{{*}} by {{complexity}}",
                                "display_type": "line",
                            }],
                        },
                        "layout": {"x": 6, "y": 0, "width": 6, "height": 3},
                    },
                ],
            },
        },

        # ======== ROW 5: SECURITY POSTURE (supporting cast) ========
        {
            "definition": {
                "type": "group",
                "layout_type": "ordered",
                "title": "🛡️ SECURITY POSTURE",
                "widgets": [
                    {
                        "definition": {
                            "title": "Vulnerability Burn-Down",
                            "type": "timeseries",
                            "requests": [
                                {"q": f"avg:{P}.vulnerabilities.open{{*}}", "display_type": "area", "style": {"palette": "warm"}},
                                {"q": f"avg:{P}.vulnerabilities.fixed{{*}}", "display_type": "bars", "style": {"palette": "green"}},
                                {"q": f"avg:{P}.vulnerabilities.unreachable_deprioritized{{*}}", "display_type": "line", "style": {"palette": "gray"}},
                            ],
                        },
                        "layout": {"x": 0, "y": 0, "width": 6, "height": 3},
                    },
                    {
                        "definition": {
                            "title": "Vulnerabilities by Severity",
                            "type": "toplist",
                            "requests": [{"q": f"avg:{P}.vulnerabilities.by_severity{{*}} by {{severity}}"}],
                        },
                        "layout": {"x": 6, "y": 0, "width": 6, "height": 3},
                    },
                ],
            },
        },

        # ======== ROW 6: AUDIT TRAIL ========
        {
            "definition": {
                "type": "group",
                "layout_type": "ordered",
                "title": "📋 AUDIT TRAIL",
                "widgets": [
                    {
                        "definition": {
                            "title": "Every Scan, Session, Policy Decision, Merge",
                            "type": "event_stream",
                            "query": "source:shieldops",
                            "event_size": "s",
                        },
                        "layout": {"x": 0, "y": 0, "width": 12, "height": 4},
                    },
                ],
            },
        },

        # ======== INFO NOTE ========
        {
            "definition": {
                "type": "note",
                "content": (
                    "## 🛡️ ShieldOps — Agent Trust Control Plane\n\n"
                    "This dashboard monitors an autonomous security remediation fleet. "
                    "Devin does the judgment-heavy work Dependabot can't — breaking-change upgrades, "
                    "call-site fixes, reachability analysis — and routes every result through a "
                    "policy boundary so humans only review what genuinely needs their judgment.\n\n"
                    "**Metrics prefix:** `shieldops.*` | **Events:** `source:shieldops`\n\n"
                    "---\n"
                    "*Powered by [Devin AI](https://devin.ai) + [Datadog](https://datadoghq.com)*"
                ),
                "background_color": "white",
                "font_size": "14",
                "text_align": "left",
                "show_tick": False,
            },
            "layout": {"x": 0, "y": 0, "width": 12, "height": 2},
        },
    ],
}


class DashboardBuilder:
    """Creates and manages the ShieldOps Datadog dashboard."""

    def __init__(self, config: DatadogConfig):
        self.config = config
        self.base_url = f"https://api.{config.site}/api/v1"
        self.headers = {
            "DD-API-KEY": config.api_key,
            "DD-APPLICATION-KEY": config.app_key,
            "Content-Type": "application/json",
        }

    async def create_or_update(self) -> Optional[str]:
        if not self.config.api_key or not self.config.app_key:
            logger.warning("No DD keys — skipping dashboard creation")
            return None

        existing_id = await self._find_existing()
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if existing_id:
                    resp = await client.put(f"{self.base_url}/dashboard/{existing_id}",
                                           headers=self.headers, json=DASHBOARD_CONFIG)
                else:
                    resp = await client.post(f"{self.base_url}/dashboard",
                                            headers=self.headers, json=DASHBOARD_CONFIG)
                resp.raise_for_status()
                data = resp.json()
                url = data.get("url", f"https://app.datadoghq.com/dashboard/{data.get('id')}")
                logger.info(f"Dashboard {'updated' if existing_id else 'created'}: {url}")
                return url
            except httpx.HTTPError as e:
                logger.error(f"Dashboard creation failed: {e}")
                return None

    async def _find_existing(self) -> Optional[str]:
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(f"{self.base_url}/dashboard", headers=self.headers)
                resp.raise_for_status()
                for dash in resp.json().get("dashboards", []):
                    if "ShieldOps" in dash.get("title", ""):
                        return dash["id"]
            except httpx.HTTPError:
                pass
        return None
