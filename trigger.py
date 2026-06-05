"""ShieldOps Event-Driven Webhook Orchestrator.

This is the NEW entry point for the demo flow. It replaces src/main.py
for event-driven operation where GitHub issues trigger Devin sessions.

Run: uvicorn trigger:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.config import Config
from src.orchestrator.devin_client import DevinClient
from src.orchestrator.policy import evaluate as policy_evaluate, PolicyDecision
from src.orchestrator.prompt_builder import PromptBuilder, STRUCTURED_OUTPUT_SCHEMA, STRUCTURED_OUTPUT_INSTRUCTION
from src.reporting.evidence_bundle import build as build_evidence, DevinSessionResult, VulnerabilityContext
from src.observability.state import State
from src.observability.metrics import (
    record_session_created,
    record_session_completed,
    record_session_failed,
    record_active_sessions,
    record_policy_decision,
    record_confidence,
    record_acu_cost,
    record_breaking_change_handled,
    record_reviewer_minutes_saved,
    EventEmitter,
)

load_dotenv()

logging.basicConfig(
    level=os.getenv("SHIELDOPS_LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("shieldops.trigger")


# ---------------------------------------------------------------------------
# Config extensions (reads new env vars on top of existing Config)
# ---------------------------------------------------------------------------
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
TRIGGER_LABEL = os.getenv("TRIGGER_LABEL", "shieldops")
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "15"))
SESSION_TIMEOUT_SECONDS = int(os.getenv("SESSION_TIMEOUT_SECONDS", "3600"))
MAX_CONCURRENT_SESSIONS = int(os.getenv("MAX_CONCURRENT_SESSIONS", "3"))
SKIP_SIGNATURE_CHECK = os.getenv("SKIP_SIGNATURE_CHECK", "0") == "1"


# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
state = State()
_semaphore: asyncio.Semaphore | None = None
_devin_client: DevinClient | None = None
_event_emitter: EventEmitter | None = None
_config: Config | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _verify_signature(payload: bytes, signature: str) -> bool:
    """Verify GitHub HMAC-SHA256 webhook signature."""
    if SKIP_SIGNATURE_CHECK:
        return True
    if not GITHUB_WEBHOOK_SECRET:
        logger.warning("No GITHUB_WEBHOOK_SECRET configured — skipping signature check")
        return True
    expected = "sha256=" + hmac.new(
        GITHUB_WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _build_devin_prompt(issue: dict) -> str:
    """Build a Devin prompt from the GitHub issue payload."""
    title = issue.get("title", "")
    body = issue.get("body", "") or ""
    number = issue.get("number", "?")
    labels = [l["name"] for l in issue.get("labels", [])]

    repo_owner = os.getenv("GITHUB_REPO_OWNER", "gaurav21")
    repo_name = os.getenv("GITHUB_REPO_NAME", "superset")
    repo_url = f"https://github.com/{repo_owner}/{repo_name}"

    prompt = f"""You are an autonomous security engineer. A GitHub issue has been filed
requesting a security remediation.

**Repository:** {repo_url}
**Issue #{number}:** {title}
**Labels:** {', '.join(labels)}

**Issue Description:**
{body}

**Your task:**
1. Clone the repository: {repo_url}
2. Read the issue description carefully — it describes a security vulnerability.
3. Investigate the vulnerability. Determine if the affected code is reachable.
4. Apply the fix:
   - For dependency upgrades: read the CHANGELOG between versions, fix any breaking changes.
   - For code fixes: apply the minimal, targeted fix.
5. Run the test suite. If tests fail, read the errors and fix your changes. Iterate until green.
6. Create a pull request with:
   - Title referencing the issue: "fix(security): <description> (closes #{number})"
   - Description explaining the vulnerability, what you changed, and why.
7. Be honest about your confidence level (0.0–1.0).

{STRUCTURED_OUTPUT_INSTRUCTION}
"""
    return prompt


def _triage_issue(issue: dict) -> dict:
    """Lightweight triage of an issue based on labels and title."""
    title = (issue.get("title", "") or "").lower()
    labels = [l["name"].lower() for l in issue.get("labels", [])]

    # Determine severity from labels
    severity = "high"  # default
    for s in ("critical", "high", "medium", "low"):
        if s in labels:
            severity = s
            break

    # Determine type from title/labels
    vuln_type = "python_dependency"
    if any(kw in title for kw in ("npm", "frontend", "javascript", "node")):
        vuln_type = "npm_dependency"
    elif any(kw in title for kw in ("dockerfile", "container", "docker", "image")):
        vuln_type = "container"
    elif any(kw in title for kw in ("sast", "injection", "xss")):
        vuln_type = "sast"

    # Predict route
    predicted_route = "human_review"
    if vuln_type in ("python_dependency", "npm_dependency") and severity in ("high", "medium"):
        predicted_route = "auto_merge"

    return {
        "severity": severity,
        "vuln_type": vuln_type,
        "predicted_route": predicted_route,
        "should_remediate": True,
    }


# ---------------------------------------------------------------------------
# Session lifecycle (background tasks)
# ---------------------------------------------------------------------------

async def _launch_session(issue: dict, triage_result: dict):
    """Launch a Devin session for a GitHub issue. Runs as a background task."""
    repo_owner = os.getenv("GITHUB_REPO_OWNER", "gaurav21")
    repo_name = os.getenv("GITHUB_REPO_NAME", "superset")
    issue_number = issue.get("number", 0)
    issue_key = f"{repo_owner}/{repo_name}#{issue_number}"

    # Dedup check
    if state.has_session(issue_key):
        logger.info(f"Duplicate launch ignored for {issue_key}")
        return

    assert _semaphore is not None
    assert _devin_client is not None

    async with _semaphore:
        try:
            prompt = _build_devin_prompt(issue)
            title = f"[ShieldOps] {issue.get('title', 'Security fix')}"
            tags = [
                f"severity:{triage_result['severity']}",
                f"type:{triage_result['vuln_type']}",
                f"issue:{issue_number}",
                "shieldops",
            ]

            session = await _devin_client.create_session(
                prompt=prompt,
                title=title,
                tags=tags,
                idempotent=True,
                max_acu_limit=10,
                structured_output_schema=STRUCTURED_OUTPUT_SCHEMA,
            )

            state.register_session(
                issue_key=issue_key,
                session_id=session.session_id,
                session_url=session.url,
                triage=triage_result,
                issue=issue,
            )

            record_session_created(session.session_id, triage_result["severity"], issue.get("title", ""))
            record_active_sessions(state.counters["active"])

            logger.info(
                f"✅ Devin session {session.session_id} launched for {issue_key} → {session.url}"
            )

            if _event_emitter:
                await _event_emitter.send_event(
                    title=f"🤖 Devin session launched for {issue_key}",
                    text=f"Issue: {issue.get('title')}\nSeverity: {triage_result['severity']}\n"
                         f"Session: {session.url}",
                    alert_type="info",
                    tags=tags + ["source:shieldops", "shieldops:session_created"],
                )

            # Start polling
            await _poll_session(issue_key, session.session_id, triage_result)

        except Exception as e:
            logger.error(f"Failed to launch session for {issue_key}: {e}")
            state.complete_session(issue_key, error=str(e))
            record_active_sessions(state.counters["active"])


async def _poll_session(issue_key: str, session_id: str, triage_result: dict):
    """Poll a Devin session until terminal status or timeout.

    v3 API completion detection:
    - Complete when: status_detail == "waiting_for_user" AND structured_output is not None
    - Also complete when: status in ("finished", "stopped", "suspended") AND structured_output is not None
    - Failed when: status in ("error", "timed_out")
    - Still running when: status == "running" AND status_detail != "waiting_for_user"
    """
    assert _devin_client is not None

    hard_terminal = {"error", "timed_out"}
    soft_terminal = {"finished", "stopped", "suspended"}
    start = datetime.now(timezone.utc)

    while True:
        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        if elapsed > SESSION_TIMEOUT_SECONDS:
            logger.warning(f"Session {session_id} timed out after {SESSION_TIMEOUT_SECONDS}s")
            state.complete_session(issue_key, error=f"Timed out after {SESSION_TIMEOUT_SECONDS}s")
            record_session_failed(session_id, triage_result["severity"])
            record_active_sessions(state.counters["active"])
            return

        await asyncio.sleep(POLL_INTERVAL_SECONDS)

        try:
            session = await _devin_client.get_session(session_id)
            detail = session.status_detail or ""
            state.record_event(
                issue_key, "poll",
                f"status={session.status}, status_detail={detail}, "
                f"has_output={session.structured_output is not None}",
            )

            # Hard failure — no recovery
            if session.status in hard_terminal:
                logger.info(f"Session {session_id} failed: {session.status}")
                state.complete_session(issue_key, error=f"Session status: {session.status}")
                record_session_failed(session_id, triage_result["severity"])
                record_active_sessions(state.counters["active"])
                return

            # v3 completion: work done, waiting for user, structured output ready
            if detail == "waiting_for_user" and session.structured_output is not None:
                logger.info(
                    f"Session {session_id} completed (v3: status_detail=waiting_for_user, "
                    f"structured_output present)"
                )
                await _process_terminal(issue_key, session_id, session, triage_result)
                return

            # Classic terminal: finished/stopped/suspended with output
            if session.status in soft_terminal and session.structured_output is not None:
                logger.info(f"Session {session_id} reached terminal status: {session.status}")
                await _process_terminal(issue_key, session_id, session, triage_result)
                return

            # Soft terminal without output — still count as done (legacy)
            if session.status in soft_terminal:
                logger.info(f"Session {session_id} terminal ({session.status}) but no structured output")
                await _process_terminal(issue_key, session_id, session, triage_result)
                return

            # Still running
            continue

        except Exception as e:
            logger.warning(f"Poll error for {session_id}: {e}")
            continue


async def _process_terminal(issue_key: str, session_id: str, session, triage_result: dict):
    """Process a terminal Devin session: run policy, emit metrics, post evidence."""
    structured = session.structured_output or {}
    severity = triage_result["severity"]

    tests_passed = structured.get("tests_passed", False)
    breaking_changes = structured.get("breaking_changes_detected", False)
    confidence = structured.get("confidence", 0.0)
    files_touched = structured.get("files_touched", [])
    devin_status = structured.get("status", "failed")
    pr_url = session.pull_request_url or structured.get("pr_url")
    changes_summary = structured.get("changes_summary", "No summary.")
    breaking_notes = structured.get("breaking_changes_notes", "")
    reachability = structured.get("reachability_assessment", "")
    notes = structured.get("notes", "")
    acu_used = structured.get("acu_used", 0.0)
    duration = int((datetime.now(timezone.utc) - datetime.fromisoformat(
        state.sessions.get(issue_key, {}).get("started_at", datetime.now(timezone.utc).isoformat())
    ).replace(tzinfo=timezone.utc)).total_seconds())

    # Determine upgrade type
    upgrade_type = "patch"
    vuln_type_str = "dependency"
    if triage_result["vuln_type"] in ("sast", "code_quality"):
        vuln_type_str = "sast"
    elif triage_result["vuln_type"] == "container":
        vuln_type_str = "container"

    # Run policy engine
    policy_result = policy_evaluate(
        severity=severity,
        vuln_type=vuln_type_str,
        upgrade_type=upgrade_type,
        tests_passed=tests_passed,
        breaking_changes_detected=breaking_changes,
        confidence=confidence,
        files_touched=files_touched,
        reachability_assessment=reachability,
        devin_status=devin_status,
    )

    decision_str = policy_result.decision.value
    logger.info(f"Policy decision for {issue_key}: {decision_str} — {policy_result.reason}")

    # Update state
    state.complete_session(
        issue_key,
        policy_decision=decision_str,
        pr_url=pr_url,
        error=None if session.status in ("finished", "stopped") else f"Session status: {session.status}",
    )

    # Emit metrics
    record_session_completed(session_id, severity, duration)
    record_policy_decision(decision_str, severity, upgrade_type)
    record_confidence(confidence, decision_str)
    record_active_sessions(state.counters["active"])

    if acu_used:
        record_acu_cost(acu_used, session_id, severity)
    if breaking_changes and policy_result.decision != PolicyDecision.BLOCKED:
        record_breaking_change_handled(issue_key, severity)

    baseline_minutes = 120 if upgrade_type == "major" else 45
    if policy_result.decision == PolicyDecision.AUTO_MERGE_READY:
        record_reviewer_minutes_saved(baseline_minutes, "auto_merge_ready")
    elif policy_result.decision == PolicyDecision.HUMAN_REVIEW:
        record_reviewer_minutes_saved(baseline_minutes * 0.8, "human_review")

    # Build evidence bundle
    issue_info = state.sessions.get(issue_key, {}).get("issue", {})
    package_name = _extract_package(issue_info.get("title", ""))

    evidence_md = build_evidence(
        vuln=VulnerabilityContext(
            cve_id="N/A",
            package=package_name,
            current_version="unknown",
            fixed_version="latest",
            severity=severity,
            advisory_url="",
            upgrade_type=upgrade_type,
        ),
        result=DevinSessionResult(
            session_id=session_id,
            pr_url=pr_url,
            status=devin_status,
            changes_summary=changes_summary,
            tests_passed=tests_passed,
            breaking_changes_detected=breaking_changes,
            breaking_changes_notes=breaking_notes,
            reachability_assessment=reachability,
            confidence=confidence,
            files_touched=files_touched,
            notes=notes,
            duration_seconds=duration,
            acu_used=acu_used,
        ),
        policy=policy_result,
    )

    # Post evidence to GitHub issue as comment
    issue_number = issue_info.get("number")
    if issue_number and _config:
        try:
            from src.scanner.issue_creator import IssueCreator
            creator = IssueCreator(_config.github)
            await creator.comment_on_issue(issue_number, evidence_md)
            logger.info(f"Posted evidence bundle to issue #{issue_number}")
        except Exception as e:
            logger.warning(f"Failed to post evidence to issue #{issue_number}: {e}")

    # Post evidence bundle to PR as comment + apply label
    label_map = {
        "auto_merge_ready": "auto-merge-ready",
        "human_review": "needs-human-review",
        "blocked": "blocked",
    }
    label = label_map.get(decision_str)

    if pr_url and _config:
        await _post_evidence_to_pr(pr_url, evidence_md, label)
    elif label and issue_number and _config:
        # Fallback: apply label to issue if no PR
        try:
            import httpx as _httpx
            headers = {
                "Authorization": f"token {_config.github.token}",
                "Accept": "application/vnd.github.v3+json",
            }
            url = (f"https://api.github.com/repos/{_config.github.repo_owner}/"
                   f"{_config.github.repo_name}/issues/{issue_number}/labels")
            async with _httpx.AsyncClient(timeout=10) as client:
                await client.post(url, headers=headers, json={"labels": [label]})
            logger.info(f"Applied label '{label}' to issue #{issue_number}")
        except Exception as e:
            logger.warning(f"Failed to apply label to issue #{issue_number}: {e}")

    # Emit Datadog event
    if _event_emitter:
        decision_emoji = {"auto_merge_ready": "🟢", "human_review": "🟡", "blocked": "🔴"}
        await _event_emitter.send_event(
            title=f"{decision_emoji.get(decision_str, '⚪')} Policy: {decision_str} — {issue_key}",
            text=f"Reason: {policy_result.reason}\nConfidence: {confidence:.0%}\n"
                 f"PR: {pr_url or 'N/A'}",
            alert_type="success" if decision_str == "auto_merge_ready"
                       else "warning" if decision_str == "human_review"
                       else "error",
            tags=[f"severity:{severity}", f"decision:{decision_str}", "source:shieldops"],
        )

    # Store extended completion info in state for dashboard
    state.update_session(
        issue_key,
        structured_output=structured,
        confidence=confidence,
        evidence_posted=True,
    )

    state.record_event(issue_key, "evidence_posted", f"decision={decision_str}")


async def _post_evidence_to_pr(pr_url: str, evidence_md: str, label: str | None):
    """Post evidence bundle comment and apply label to a GitHub PR."""
    assert _config is not None
    import re

    # Parse owner/repo/number from PR URL
    # Formats: https://github.com/owner/repo/pull/123
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not match:
        logger.warning(f"Cannot parse PR URL: {pr_url}")
        return

    owner, repo, pr_number = match.group(1), match.group(2), match.group(3)
    headers = {
        "Authorization": f"token {_config.github.token}",
        "Accept": "application/vnd.github.v3+json",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        # Post evidence as PR comment (uses issues API which works for PRs)
        try:
            comment_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
            resp = await client.post(
                comment_url,
                headers=headers,
                json={"body": evidence_md},
            )
            resp.raise_for_status()
            logger.info(f"Posted evidence bundle to PR {pr_url}")
        except Exception as e:
            logger.warning(f"Failed to post evidence to PR {pr_url}: {e}")

        # Apply label
        if label:
            try:
                label_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/labels"
                resp = await client.post(
                    label_url,
                    headers=headers,
                    json={"labels": [label]},
                )
                resp.raise_for_status()
                logger.info(f"Applied label '{label}' to PR {pr_url}")
            except Exception as e:
                logger.warning(f"Failed to apply label to PR {pr_url}: {e}")


def _extract_package(title: str) -> str:
    """Best-effort package name extraction from issue title."""
    skip = {"upgrade", "fix", "security", "vulnerability", "[high]", "[critical]",
            "[medium]", "[low]", "—", "-", "npm", "advisory:", "in", "shieldops"}
    for word in title.split():
        clean = word.strip("`").strip(":").lower()
        if clean and clean not in skip and not clean.startswith("["):
            return word.strip("`").strip(":")
    return "unknown"


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _semaphore, _devin_client, _event_emitter, _config
    _config = Config.from_env()
    _devin_client = DevinClient(_config.devin)
    _event_emitter = EventEmitter(_config.datadog)
    _semaphore = asyncio.Semaphore(MAX_CONCURRENT_SESSIONS)
    logger.info(f"🛡️ ShieldOps trigger started — label={TRIGGER_LABEL}, "
                f"max_sessions={MAX_CONCURRENT_SESSIONS}, "
                f"poll_interval={POLL_INTERVAL_SECONDS}s")

    # Resume polling for sessions that were active when we last shut down
    running = state.get_running_sessions()
    if running:
        logger.info(f"🔄 Resuming {len(running)} active session(s) from persisted state")
        for issue_key, session_data in running.items():
            sid = session_data.get("session_id")
            triage = session_data.get("triage", {})
            if sid:
                asyncio.create_task(_poll_session(issue_key, sid, triage))
                logger.info(f"  → Resumed polling for {issue_key} (session {sid})")

    yield
    logger.info("🛡️ ShieldOps trigger shutting down")


app = FastAPI(
    title="🛡️ ShieldOps Trigger",
    description="Event-driven webhook orchestrator — GitHub issues → Devin sessions → Policy → Evidence",
    version="2.1.0",
    lifespan=lifespan,
)

# Mount static files
import pathlib as _pathlib
_static_dir = _pathlib.Path(__file__).parent / "static"
if _static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the ShieldOps control-plane dashboard."""
    html_path = _pathlib.Path(__file__).parent / "static" / "dashboard.html"
    return FileResponse(str(html_path), media_type="text/html")


# ---------------------------------------------------------------------------
# Simulation / demo endpoints (for the dashboard)
# ---------------------------------------------------------------------------

_DEMO_ISSUES = {
    "flask": {
        "number": 101,
        "title": "[CRITICAL] Flask 2.3.3 EOL — upgrade to Flask 3.x",
        "body": "Flask 2.3.3 has reached end-of-life.  Upgrade to 3.1.1.\nBreaking API changes expected.",
        "labels": [{"name": "shieldops"}, {"name": "critical"}, {"name": "security"}],
    },
    "paramiko": {
        "number": 102,
        "title": "[LOW] Paramiko CVE-2026-44405 — SSH key validation bypass",
        "body": "Paramiko < 5.0.0 SSH key validation bypass.  Major version bump.",
        "labels": [{"name": "shieldops"}, {"name": "low"}, {"name": "security"}],
    },
    "dockerfile": {
        "number": 103,
        "title": "[MEDIUM] Dockerfile hardening — SHA256 digests & remove dev packages",
        "body": "Pin base image digest, remove dev packages, add HEALTHCHECK, non-root user.",
        "labels": [{"name": "shieldops"}, {"name": "medium"}, {"name": "security"}, {"name": "container"}],
    },
    "npm": {
        "number": 104,
        "title": "[HIGH] npm audit findings — multiple frontend dependency vulnerabilities",
        "body": "postcss, semver, word-wrap ReDoS vulnerabilities in superset-frontend.",
        "labels": [{"name": "shieldops"}, {"name": "high"}, {"name": "security"}, {"name": "frontend"}],
    },
}


@app.post("/api/simulate")
async def simulate_issue(request: Request):
    """Simulate a GitHub webhook from the dashboard UI.

    Accepts {type: "flask"|"paramiko"|"dockerfile"|"npm"|"custom", title?, body?}
    Builds a fake webhook payload and processes it through the triage → session flow.
    """
    data = await request.json()
    issue_type = data.get("type", "flask")

    if issue_type == "custom":
        issue = {
            "number": 199,
            "title": data.get("title", "Custom security issue"),
            "body": data.get("body", "Custom issue submitted from dashboard"),
            "labels": [{"name": "shieldops"}, {"name": "high"}, {"name": "security"}],
        }
    else:
        issue = _DEMO_ISSUES.get(issue_type)
        if not issue:
            return JSONResponse({"detail": f"Unknown issue type: {issue_type}"}, status_code=400)

    # Run through the same triage logic
    triage_result = _triage_issue(issue)
    issue_key = f"sim#{issue['number']}"

    state.record_event(
        issue_key,
        "simulated",
        f"type={issue_type}, triage={triage_result['predicted_route']}",
    )

    # Launch Devin session (will fail gracefully if no API key)
    asyncio.create_task(_launch_session(issue, triage_result))

    return {
        "status": "accepted",
        "issue": issue['number'],
        "title": issue['title'],
        "triage": triage_result,
    }


@app.post("/api/create-issues")
async def api_create_issues():
    """Create real GitHub issues via the create_issues.py script."""
    import subprocess
    script = _pathlib.Path(__file__).parent / "scripts" / "create_issues.py"
    if not script.exists():
        return JSONResponse({"detail": "create_issues.py not found"}, status_code=404)

    try:
        result = subprocess.run(
            ["python3", str(script)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(script.parent.parent),
        )
        # Parse output for created issue URLs
        created = []
        for line in result.stdout.splitlines():
            if "✅ Created:" in line:
                url = line.split("Created:")[-1].strip()
                created.append({"url": url})

        state.record_event(
            "github",
            "create_issues",
            f"created={len(created)}, exit={result.returncode}",
        )

        return {
            "status": "ok" if result.returncode == 0 else "error",
            "created": created,
            "stdout": result.stdout[-500:] if result.stdout else "",
            "stderr": result.stderr[-300:] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return JSONResponse({"detail": "Script timed out"}, status_code=504)
    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=500)


@app.post("/webhook/github")
async def webhook_github(request: Request):
    """GitHub webhook receiver.

    Verifies HMAC signature, acts on issue events (opened / labeled)
    when the label matches TRIGGER_LABEL. Returns 200 immediately;
    Devin session work happens in a background asyncio task.
    """
    body = await request.body()

    # Signature verification
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not _verify_signature(body, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    event_type = request.headers.get("X-GitHub-Event", "")
    if event_type == "ping":
        return {"status": "pong"}

    if event_type != "issues":
        return {"status": "ignored", "event": event_type}

    payload = json.loads(body)
    action = payload.get("action", "")
    issue = payload.get("issue", {})
    labels = [l["name"] for l in issue.get("labels", [])]

    # Only act on opened/labeled with the trigger label
    if action not in ("opened", "labeled"):
        return {"status": "ignored", "action": action}

    if TRIGGER_LABEL not in labels:
        return {"status": "ignored", "reason": f"label '{TRIGGER_LABEL}' not found"}

    issue_number = issue.get("number", 0)
    logger.info(f"🎯 Webhook triggered: issue #{issue_number} ({action}) — {issue.get('title')}")

    # Triage
    triage_result = _triage_issue(issue)
    state.record_event(
        f"#{issue_number}",
        "webhook_received",
        f"action={action}, labels={labels}, triage={triage_result['predicted_route']}",
    )

    # Launch Devin session in background — MUST NOT block the webhook
    asyncio.create_task(_launch_session(issue, triage_result))

    return {
        "status": "accepted",
        "issue": issue_number,
        "session_launching": True,
        "triage": triage_result,
    }


@app.get("/status")
async def get_status():
    """Live status view — active/completed/blocked counts, session state, audit events.

    This is the 'is it working' view for engineering leaders. Works without Datadog.
    """
    return state.to_dict()


@app.get("/health")
async def health():
    """Health check — is the app running and can it reach Devin?"""
    devin_ok = False
    if _devin_client:
        try:
            devin_ok = await _devin_client.is_healthy()
        except Exception:
            pass
    return {
        "ok": True,
        "devin_api": devin_ok,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
