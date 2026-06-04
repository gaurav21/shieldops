from __future__ import annotations

"""GitHub reporting — comments on issues with Devin session status."""

import logging
from typing import TYPE_CHECKING, Optional

from ..scanner.issue_creator import IssueCreator

if TYPE_CHECKING:
    from ..orchestrator.session_manager import RemediationTask

logger = logging.getLogger(__name__)


class GitHubReporter:
    """Reports remediation progress back to GitHub issues."""

    def __init__(self, issue_creator: IssueCreator):
        self.issues = issue_creator

    async def report_session_created(self, task: RemediationTask):
        if not task.vuln.github_issue_number:
            return
        body = (
            f"🤖 **ShieldOps: Remediation Started**\n\n"
            f"Devin is now working on this vulnerability.\n\n"
            f"- **Session:** [{task.devin_session.session_id}]({task.devin_session.url})\n"
            f"- **Priority Score:** {task.decision.priority_score}/100\n"
            f"- **Complexity:** {task.decision.estimated_complexity}\n"
            f"- **Predicted Route:** {task.decision.predicted_route}\n\n"
            f"I'll update this issue when the fix is ready."
        )
        await self.issues.comment_on_issue(task.vuln.github_issue_number, body)

    async def report_pr_created(self, task: RemediationTask):
        if not task.vuln.github_issue_number:
            return
        duration = f"{task.duration_seconds:.0f}s" if task.duration_seconds else "N/A"
        body = (
            f"✅ **ShieldOps: Fix Ready**\n\n"
            f"- **PR:** {task.pr_url}\n"
            f"- **Duration:** {duration}\n"
            f"- **Session:** [{task.devin_session.session_id}]({task.devin_session.url})\n"
        )
        await self.issues.comment_on_issue(task.vuln.github_issue_number, body)

    async def report_failure(self, task: RemediationTask):
        if not task.vuln.github_issue_number:
            return
        body = (
            f"❌ **ShieldOps: Remediation Failed**\n\n"
            f"- **Error:** {task.error or 'Unknown'}\n"
            f"- **Session:** [{task.devin_session.session_id}]({task.devin_session.url})\n\n"
            f"Manual intervention may be required."
        )
        await self.issues.comment_on_issue(task.vuln.github_issue_number, body)
