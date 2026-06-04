from __future__ import annotations

"""GitHub webhook handler — the event-driven trigger for remediation."""

import hashlib
import hmac
import json
import logging
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhooks"])

# These get set by the app on startup
_orchestrator = None
_webhook_secret = None


def configure(orchestrator, webhook_secret: str):
    """Configure the webhook handler with dependencies."""
    global _orchestrator, _webhook_secret
    _orchestrator = orchestrator
    _webhook_secret = webhook_secret


def _verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature."""
    if not secret:
        return True  # Skip verification if no secret configured

    expected = "sha256=" + hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle GitHub webhook events.
    
    Triggers remediation when:
    1. An issue is labeled with 'devin-auto-fix'
    2. An issue is created with the 'security' label
    """
    # Verify signature
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    if _webhook_secret and not _verify_signature(body, signature, _webhook_secret):
        raise HTTPException(status_code=403, detail="Invalid signature")

    event_type = request.headers.get("X-GitHub-Event", "")
    payload = json.loads(body)

    if event_type == "issues":
        action = payload.get("action")
        issue = payload.get("issue", {})
        labels = [l["name"] for l in issue.get("labels", [])]

        # Trigger on: issue labeled with 'devin-auto-fix'
        if action == "labeled" and "devin-auto-fix" in labels:
            logger.info(f"Issue #{issue['number']} labeled for auto-fix: {issue['title']}")
            background_tasks.add_task(
                _handle_issue_remediation,
                issue_number=issue["number"],
                issue_title=issue["title"],
                issue_body=issue.get("body", ""),
                labels=labels,
            )
            return {"status": "accepted", "message": f"Remediation triggered for #{issue['number']}"}

        # Trigger on: new issue with 'security' label
        if action == "opened" and "security" in labels:
            logger.info(f"New security issue #{issue['number']}: {issue['title']}")
            background_tasks.add_task(
                _handle_issue_remediation,
                issue_number=issue["number"],
                issue_title=issue["title"],
                issue_body=issue.get("body", ""),
                labels=labels,
            )
            return {"status": "accepted", "message": f"Remediation triggered for #{issue['number']}"}

    elif event_type == "pull_request":
        action = payload.get("action")
        pr = payload.get("pull_request", {})

        # Track PR merges for metrics
        if action == "closed" and pr.get("merged"):
            logger.info(f"PR #{pr['number']} merged: {pr['title']}")
            if _orchestrator:
                background_tasks.add_task(
                    _orchestrator.handle_pr_merged,
                    pr_number=pr["number"],
                    pr_title=pr["title"],
                )
            return {"status": "accepted", "message": f"PR merge tracked"}

    return {"status": "ignored", "event": event_type}


async def _handle_issue_remediation(
    issue_number: int,
    issue_title: str,
    issue_body: str,
    labels: list[str],
):
    """Background task: create a Devin session for the issue."""
    if not _orchestrator:
        logger.error("Orchestrator not configured")
        return

    try:
        await _orchestrator.remediate_issue(
            issue_number=issue_number,
            issue_title=issue_title,
            issue_body=issue_body,
            labels=labels,
        )
    except Exception as e:
        logger.error(f"Failed to remediate issue #{issue_number}: {e}")
