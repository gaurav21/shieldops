from __future__ import annotations

"""Datadog event tracking — lifecycle + policy decision audit trail.

v2: Every policy decision is an event. This is the compliance story.
"""

import logging

from ..config import DatadogConfig
from ..orchestrator.session_manager import RemediationTask
from ..orchestrator.policy import PolicyResult, PolicyDecision
from ..scanner.models import ScanResult
from ..shared.constants import POLICY_DECISION_EMOJI
from ..shared.task_tags import build_task_tags
from .datadog_base import DatadogBaseClient

logger = logging.getLogger(__name__)


class EventTracker(DatadogBaseClient):
    """Sends lifecycle events to Datadog — the audit trail a VP needs."""

    def __init__(self, config: DatadogConfig):
        super().__init__(config, api_version="v1")

    async def scan_completed(self, scan_result: ScanResult):
        severity_summary = ", ".join(f"{count} {sev}" for sev, count in scan_result.by_severity.items())
        await self.send_event(
            title=f"🔍 Scan completed: {len(scan_result.vulnerabilities)} vulnerabilities found",
            text=f"Scanner: {scan_result.scanner}\nBreakdown: {severity_summary}",
            alert_type="info",
            tags=[f"scanner:{scan_result.scanner}", "shieldops:scan"],
        )

    async def session_created(self, task: RemediationTask):
        await self.send_event(
            title=f"🤖 Devin session created for {task.vuln.package_name}",
            text=(f"Vulnerability: {task.vuln.title}\n"
                  f"Severity: {task.vuln.severity.value}\n"
                  f"Predicted route: {task.decision.predicted_route}\n"
                  f"Reachable: {task.decision.reachable}\n"
                  f"Session: {task.devin_session.url if task.devin_session else 'N/A'}"),
            alert_type="info",
            tags=build_task_tags(task) + ["source:shieldops", "shieldops:session_created"],
        )

    async def policy_decision(self, task: RemediationTask, policy: PolicyResult):
        """The key audit event — every policy routing decision is recorded."""
        emoji = POLICY_DECISION_EMOJI.get(policy.decision, "⚪")
        alert_type = {
            PolicyDecision.AUTO_MERGE_READY: "success",
            PolicyDecision.HUMAN_REVIEW: "warning",
            PolicyDecision.BLOCKED: "error",
        }.get(policy.decision, "info")

        text = (
            f"Package: {task.vuln.package_name}\n"
            f"Decision: {policy.decision.value}\n"
            f"Reason: {policy.reason}\n"
            f"Confidence: {policy.confidence:.0%}\n"
            f"Breaking changes: {'Yes' if policy.breaking_changes_detected else 'No'}\n"
            f"Upgrade type: {policy.upgrade_type.value}\n"
            f"Files touched: {len(policy.files_touched)}\n"
            f"Sensitive paths: {', '.join(policy.sensitive_paths_touched) or 'None'}\n"
        )

        if task.pr_url:
            text += f"PR: {task.pr_url}\n"
        if task.devin_session:
            text += f"Session: {task.devin_session.url}\n"
        if task.duration_seconds:
            text += f"Duration: {task.duration_seconds:.0f}s\n"

        await self.send_event(
            title=f"{emoji} Policy: {policy.decision.value} — {task.vuln.package_name}",
            text=text,
            alert_type=alert_type,
            tags=build_task_tags(task) + [
                "source:shieldops",
                f"shieldops:policy_{policy.decision.value}",
                f"decision:{policy.decision.value}",
                f"upgrade_type:{policy.upgrade_type.value}",
                f"breaking_changes:{'yes' if policy.breaking_changes_detected else 'no'}",
            ],
        )

    async def session_failed(self, task: RemediationTask):
        await self.send_event(
            title=f"❌ Session failed for {task.vuln.package_name}",
            text=f"Error: {task.error or 'Unknown'}\n"
                 f"Session: {task.devin_session.url if task.devin_session else 'N/A'}",
            alert_type="error",
            tags=build_task_tags(task) + ["source:shieldops", "shieldops:session_failed"],
        )

    async def intervention(self, task: RemediationTask):
        await self.send_event(
            title=f"🔧 Intervention #{task.interventions} for {task.vuln.package_name}",
            text=f"A human sent a follow-up message to Devin session.\n"
                 f"Session: {task.devin_session.url if task.devin_session else 'N/A'}",
            alert_type="warning",
            tags=build_task_tags(task) + ["source:shieldops", "shieldops:intervention"],
        )
