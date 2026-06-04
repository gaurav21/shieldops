from __future__ import annotations

"""Session manager — lifecycle management for Devin remediation sessions.

Tracks interventions (follow-up messages) as a fleet health metric.
Policy evaluation happens in main.py after session completes — this module
just manages the Devin session lifecycle and returns results.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Callable, Awaitable

from datadog import statsd

from .devin_client import DevinClient, DevinSession
from .prompt_builder import PromptBuilder, STRUCTURED_OUTPUT_SCHEMA
from .triage import TriageDecision
from ..scanner.models import RemediationStatus, Vulnerability

logger = logging.getLogger(__name__)


@dataclass
class RemediationTask:
    """Tracks a single vulnerability remediation lifecycle."""
    decision: TriageDecision
    devin_session: Optional[DevinSession] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    pr_url: Optional[str] = None
    error: Optional[str] = None
    devin_output: Optional[dict] = None
    intervention_count: int = 0

    @property
    def vuln(self) -> Vulnerability:
        return self.decision.vulnerability

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_complete(self) -> bool:
        return self.vuln.status in (
            RemediationStatus.PR_CREATED, RemediationStatus.PR_MERGED,
            RemediationStatus.AUTO_MERGE_READY, RemediationStatus.HUMAN_REVIEW,
            RemediationStatus.BLOCKED, RemediationStatus.FAILED,
            RemediationStatus.SKIPPED,
        )


# Callback type for status updates
StatusCallback = Callable[[RemediationTask, str], Awaitable[None]]


class SessionManager:
    """Manages Devin sessions for vulnerability remediation."""

    def __init__(
        self,
        devin_client: DevinClient,
        prompt_builder: PromptBuilder,
        max_concurrent: int = 3,
        poll_interval: int = 15,
        session_timeout: int = 3600,
    ):
        self.devin = devin_client
        self.prompts = prompt_builder
        self.max_concurrent = max_concurrent
        self.poll_interval = poll_interval
        self.session_timeout = session_timeout
        self.active_tasks: dict[str, RemediationTask] = {}
        self.completed_tasks: list[RemediationTask] = []
        self._status_callbacks: list[StatusCallback] = []
        self._semaphore = asyncio.Semaphore(max_concurrent)

    def on_status_change(self, callback: StatusCallback):
        self._status_callbacks.append(callback)

    async def _notify(self, task: RemediationTask, event: str):
        for cb in self._status_callbacks:
            try:
                await cb(task, event)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    async def remediate_batch(self, decisions: list[TriageDecision]) -> list[RemediationTask]:
        """Process a batch of triage decisions through Devin."""
        actionable = [d for d in decisions if d.should_remediate]
        logger.info(f"Starting remediation batch: {len(actionable)} vulnerabilities")

        tasks = []
        for decision in actionable:
            task = asyncio.create_task(self._remediate_one(decision))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        completed = []
        for decision, r in zip(actionable, results):
            if isinstance(r, Exception):
                logger.error(
                    f"Remediation task failed for {decision.vulnerability.package_name} "
                    f"({type(r).__name__}): {r}"
                )
            elif r:
                completed.append(r)
        return completed

    async def _remediate_one(self, decision: TriageDecision) -> RemediationTask:
        """Remediate a single vulnerability via Devin session."""
        task = RemediationTask(decision=decision)

        async with self._semaphore:
            try:
                task.started_at = datetime.utcnow()
                task.vuln.status = RemediationStatus.IN_PROGRESS

                prompt = self.prompts.build_prompt(task.vuln)

                tags = [
                    f"severity:{task.vuln.severity.value}",
                    f"type:{task.vuln.vuln_type.value}",
                    f"package:{task.vuln.package_name}",
                    f"predicted:{decision.predicted_route}",
                    "shieldops",
                ]
                if task.vuln.github_issue_number:
                    tags.append(f"issue:{task.vuln.github_issue_number}")

                session = await self.devin.create_session(
                    prompt=prompt,
                    title=f"[ShieldOps] {task.vuln.title}",
                    tags=tags,
                    max_acu_limit=10,
                    structured_output_schema=STRUCTURED_OUTPUT_SCHEMA,
                )

                task.devin_session = session
                task.vuln.devin_session_id = session.session_id
                self.active_tasks[session.session_id] = task

                await self._notify(task, "session_created")
                logger.info(f"Devin session {session.session_id} for {task.vuln.package_name} — {session.url}")

                # Poll for completion
                await self._poll_session(task)

            except Exception as e:
                task.error = str(e)
                task.vuln.status = RemediationStatus.FAILED
                task.completed_at = datetime.utcnow()
                await self._notify(task, "session_failed")
                logger.error(f"Remediation failed for {task.vuln.package_name}: {e}")

            finally:
                # Emit intervention metrics at session close
                session_id = task.devin_session.session_id if task.devin_session else "unknown"
                severity = task.vuln.severity.value
                statsd.gauge(
                    "shieldops.devin.intervention_count",
                    task.intervention_count,
                    tags=[f"session_id:{session_id}", f"severity:{severity}"],
                )
                statsd.gauge(
                    "shieldops.devin.needed_intervention",
                    1 if task.intervention_count > 0 else 0,
                    tags=[f"session_id:{session_id}"],
                )

                if task.devin_session:
                    self.active_tasks.pop(task.devin_session.session_id, None)
                self.completed_tasks.append(task)

        return task

    async def _poll_session(self, task: RemediationTask):
        """Poll a Devin session until completion or timeout."""
        session_id = task.devin_session.session_id
        start = datetime.utcnow()
        consecutive_errors = 0
        max_consecutive_errors = 5

        while True:
            elapsed = (datetime.utcnow() - start).total_seconds()
            if elapsed > self.session_timeout:
                task.error = f"Session timed out after {self.session_timeout}s"
                task.vuln.status = RemediationStatus.FAILED
                task.completed_at = datetime.utcnow()
                await self._notify(task, "session_timeout")
                return

            await asyncio.sleep(self.poll_interval)

            try:
                session = await self.devin.get_session(session_id)
                task.devin_session = session
                consecutive_errors = 0

                if session.status in ("running", "blocked"):
                    if session.status == "blocked":
                        logger.info(f"Session {session_id} is blocked — may need intervention")
                    continue

                # Session completed
                task.completed_at = datetime.utcnow()
                task.devin_output = session.structured_output or {}

                if session.pull_request_url:
                    task.pr_url = session.pull_request_url
                elif task.devin_output.get("pr_url"):
                    task.pr_url = task.devin_output["pr_url"]

                if session.status == "stopped":
                    task.vuln.status = RemediationStatus.PR_CREATED if task.pr_url else RemediationStatus.FAILED
                    if not task.pr_url:
                        task.error = "Session completed without creating a PR"
                elif session.status in ("error", "timed_out"):
                    task.vuln.status = RemediationStatus.FAILED
                    task.error = f"Session ended with status: {session.status}"

                return

            except Exception as e:
                consecutive_errors += 1
                logger.warning(
                    f"Poll error for {session_id} "
                    f"({consecutive_errors}/{max_consecutive_errors}): {e}"
                )
                if consecutive_errors >= max_consecutive_errors:
                    task.error = (
                        f"Polling abandoned after {max_consecutive_errors} "
                        f"consecutive errors, last: {e}"
                    )
                    task.vuln.status = RemediationStatus.FAILED
                    task.completed_at = datetime.utcnow()
                    await self._notify(task, "session_failed")
                    return

    async def send_intervention(self, session_id: str, message: str) -> bool:
        """Send a follow-up message to a Devin session (counts as intervention)."""
        task = self.active_tasks.get(session_id)
        if task:
            task.intervention_count += 1
            logger.info(f"Intervention #{task.intervention_count} for {session_id}")

        success = await self.devin.send_message(session_id, message)
        if success and task:
            await self._notify(task, "intervention")
        return success

    def get_stats(self) -> dict:
        """Get current fleet statistics."""
        completed = self.completed_tasks
        succeeded = [t for t in completed if t.vuln.status in (
            RemediationStatus.PR_CREATED, RemediationStatus.AUTO_MERGE_READY,
            RemediationStatus.HUMAN_REVIEW)]
        failed = [t for t in completed if t.vuln.status in (
            RemediationStatus.FAILED, RemediationStatus.BLOCKED)]

        durations = [t.duration_seconds for t in succeeded if t.duration_seconds]
        avg_duration = sum(durations) / len(durations) if durations else 0

        total_interventions = sum(t.intervention_count for t in completed)
        intervention_rate = (sum(1 for t in completed if t.intervention_count > 0)
                            / max(len(completed), 1) * 100)

        return {
            "active_sessions": len(self.active_tasks),
            "completed": len(completed),
            "succeeded": len(succeeded),
            "failed": len(failed),
            "success_rate": len(succeeded) / max(len(completed), 1) * 100,
            "avg_duration_seconds": avg_duration,
            "intervention_rate": intervention_rate,
            "total_interventions": total_interventions,
            "prs_created": len(succeeded),
        }
