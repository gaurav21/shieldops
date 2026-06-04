from __future__ import annotations

"""Datadog metrics — reframed as Agent Trust Control Plane.

v2: Stop observing *vulnerabilities*. Start observing *the autonomous workforce*.
Fleet health, trust split, cost, and the "Dependabot can't" metrics are the headline.
"""

import logging
import time

import httpx

from ..config import DatadogConfig
from ..orchestrator.session_manager import RemediationTask
from ..orchestrator.policy import PolicyResult, PolicyDecision
from ..scanner.models import ScanResult

logger = logging.getLogger(__name__)


class MetricsEmitter:
    """Emits custom metrics to Datadog — the numbers a VP watches."""

    def __init__(self, config: DatadogConfig):
        self.config = config
        self.prefix = config.metric_prefix
        self.base_url = f"https://api.{config.site}/api/v2"
        self.headers = {
            "DD-API-KEY": config.api_key,
            "Content-Type": "application/json",
        }

    # === THE FLEET ===

    async def emit_session_created(self, task: RemediationTask):
        now = int(time.time())
        tags = self._task_tags(task)
        await self._submit([
            self._count(f"{self.prefix}.devin.sessions.created", 1, now, tags),
        ])

    async def emit_session_completed(self, task: RemediationTask):
        now = int(time.time())
        tags = self._task_tags(task)
        series = [self._count(f"{self.prefix}.devin.sessions.completed", 1, now, tags)]

        if task.duration_seconds:
            series.append(self._gauge(f"{self.prefix}.devin.session.duration_seconds",
                                      task.duration_seconds, now, tags))
        if task.interventions > 0:
            series.append(self._count(f"{self.prefix}.devin.interventions", task.interventions, now, tags))

        await self._submit(series)

    async def emit_session_failed(self, task: RemediationTask):
        now = int(time.time())
        tags = self._task_tags(task)
        await self._submit([
            self._count(f"{self.prefix}.devin.sessions.failed", 1, now, tags),
        ])

    # === TRUST SPLIT (the VP's comfort metrics) ===

    async def emit_policy_decision(self, task: RemediationTask, policy: PolicyResult):
        """Emit the policy routing decision — auto-merge vs human vs blocked."""
        now = int(time.time())
        tags = self._task_tags(task) + [f"decision:{policy.decision.value}"]

        series = [
            self._count(f"{self.prefix}.policy.{policy.decision.value}", 1, now, tags),
            self._gauge(f"{self.prefix}.remediation.confidence", policy.confidence, now, tags),
        ]

        # The hero metric: breaking changes handled
        if policy.breaking_changes_detected and policy.decision != PolicyDecision.BLOCKED:
            series.append(self._count(
                f"{self.prefix}.remediation.breaking_changes_handled", 1, now, tags))

        # Cost tracking (ACU approximation — Devin sessions use ACUs)
        if task.duration_seconds:
            # Rough ACU estimate: ~1 ACU per 10 min of session time
            estimated_acu = task.duration_seconds / 600
            series.append(self._gauge(f"{self.prefix}.devin.cost_acu", estimated_acu, now, tags))

        await self._submit(series)

    # === FLEET AGGREGATE STATS ===

    async def emit_fleet_stats(self, stats: dict):
        """Emit aggregate fleet statistics for the dashboard."""
        now = int(time.time())
        tags = ["pipeline:shieldops"]

        series = [
            # Fleet status
            self._gauge(f"{self.prefix}.devin.sessions.active",
                       stats["active_sessions"], now, tags),
            self._gauge(f"{self.prefix}.remediation.success_rate",
                       stats["success_rate"], now, tags),
            self._gauge(f"{self.prefix}.devin.intervention_rate",
                       stats["intervention_rate"], now, tags),
            self._gauge(f"{self.prefix}.remediation.avg_confidence",
                       stats["avg_confidence"], now, tags),

            # Trust split totals
            self._gauge(f"{self.prefix}.policy.auto_merge_ready.total",
                       stats["auto_merge_ready"], now, tags),
            self._gauge(f"{self.prefix}.policy.human_review.total",
                       stats["human_review"], now, tags),
            self._gauge(f"{self.prefix}.policy.blocked.total",
                       stats["blocked"], now, tags),

            # The hero number
            self._gauge(f"{self.prefix}.remediation.breaking_changes_handled.total",
                       stats["breaking_changes_handled"], now, tags),
        ]

        if stats["avg_duration_seconds"] > 0:
            series.append(self._gauge(
                f"{self.prefix}.remediation.time_to_merged_verified_seconds",
                stats["avg_duration_seconds"], now, tags))

        await self._submit(series)

    # === VULNERABILITY POSTURE (demoted to supporting cast) ===

    async def emit_scan_metrics(self, scan_result: ScanResult):
        now = int(time.time())
        tags = [f"scanner:{scan_result.scanner}"]
        series = [
            self._gauge(f"{self.prefix}.scan.vulnerabilities_found",
                       len(scan_result.vulnerabilities), now, tags),
        ]
        if scan_result.duration_seconds:
            series.append(self._gauge(f"{self.prefix}.scan.duration_seconds",
                                      scan_result.duration_seconds, now, tags))
        for severity, count in scan_result.by_severity.items():
            series.append(self._gauge(f"{self.prefix}.vulnerabilities.by_severity",
                                      count, now, tags + [f"severity:{severity}"]))
        await self._submit(series)

    async def emit_vulnerability_gauge(self, open_count: int, fixed_count: int,
                                        unreachable_count: int = 0):
        now = int(time.time())
        tags = ["pipeline:shieldops"]
        series = [
            self._gauge(f"{self.prefix}.vulnerabilities.open", open_count, now, tags),
            self._gauge(f"{self.prefix}.vulnerabilities.fixed", fixed_count, now, tags),
            self._gauge(f"{self.prefix}.vulnerabilities.unreachable_deprioritized",
                       unreachable_count, now, tags),
        ]
        await self._submit(series)

    # === Helpers ===

    def _task_tags(self, task: RemediationTask) -> list[str]:
        return [
            f"severity:{task.vuln.severity.value}",
            f"type:{task.vuln.vuln_type.value}",
            f"package:{task.vuln.package_name}",
            f"complexity:{task.decision.estimated_complexity}",
            f"predicted_route:{task.decision.predicted_route}",
        ]

    def _gauge(self, metric: str, value: float, timestamp: int, tags: list[str]) -> dict:
        return {"metric": metric, "type": 3, "points": [{"timestamp": timestamp, "value": value}], "tags": tags}

    def _count(self, metric: str, value: float, timestamp: int, tags: list[str]) -> dict:
        return {"metric": metric, "type": 1, "points": [{"timestamp": timestamp, "value": value}], "tags": tags}

    async def _submit(self, series: list[dict]):
        if not self.config.api_key:
            logger.debug("No DD API key — skipping metric submission")
            return
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(f"{self.base_url}/series", headers=self.headers, json={"series": series})
                if resp.status_code not in (200, 202):
                    logger.warning(f"Datadog metrics returned {resp.status_code}")
        except Exception as e:
            logger.error(f"Failed to submit metrics: {e}")
