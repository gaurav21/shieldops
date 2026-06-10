from __future__ import annotations

"""ShieldOps — Trust Control Plane for Autonomous Security Remediation.

Devin does the judgment-heavy work Dependabot can't. Datadog proves the fleet is safe to run.
"""

import asyncio
import hmac
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

from .config import Config
from .scanner.vulnerability_scanner import VulnerabilityScanner
from .scanner.issue_creator import IssueCreator
from .scanner.models import Vulnerability, Severity, VulnerabilityType, RemediationStatus
from .orchestrator.devin_client import DevinClient
from .orchestrator.session_manager import SessionManager, RemediationTask
from .orchestrator.triage import TriageEngine
from .orchestrator.prompt_builder import PromptBuilder
from .orchestrator.policy import evaluate as policy_evaluate, PolicyDecision
from .observability.metrics import (
    EventEmitter,
    record_scan_completed,
    record_vulnerability_counts,
    record_vulnerability_by_severity,
    record_session_created,
    record_session_completed,
    record_session_failed,
    record_active_sessions,
    record_policy_decision,
    record_breaking_change_handled,
    record_confidence,
    record_acu_cost,
    record_reviewer_minutes_saved,
    record_unreachable_vuln_deprioritized,
)
from .observability.dashboard import DashboardBuilder
from .observability.monitors import MonitorBuilder
from .reporting.evidence_bundle import build as build_evidence, DevinSessionResult, VulnerabilityContext
from .reporting.github_reporter import GitHubReporter
from .webhooks.github_webhook import router as webhook_router, configure as configure_webhooks
from .webhooks.scheduler import ScanScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("shieldops")


class ShieldOpsOrchestrator:
    """The brain — connects scanner, Devin, policy engine, Datadog, and GitHub."""

    def __init__(self, config: Config):
        self.config = config

        self.scanner = VulnerabilityScanner(
            repo_path=os.getenv("REPO_PATH", "/tmp/superset"),
            scan_types=config.scanner.scan_types,
        )
        self.issue_creator = IssueCreator(config.github)
        self.devin = DevinClient(config.devin)
        self.prompt_builder = PromptBuilder(
            repo_url=config.github.repo_url,
            repo_name=config.github.repo_name,
        )
        self.triage = TriageEngine(
            repo_path=os.getenv("REPO_PATH", "/tmp/superset"),
        )
        self.session_manager = SessionManager(
            devin_client=self.devin,
            prompt_builder=self.prompt_builder,
            max_concurrent=config.devin.max_concurrent_sessions,
            poll_interval=config.devin.poll_interval,
            session_timeout=config.devin.session_timeout,
        )

        # Observability
        self.event_emitter = EventEmitter(config.datadog)
        self.dashboard_builder = DashboardBuilder(config.datadog)
        self.monitor_builder = MonitorBuilder(config.datadog)

        # Reporting
        self.reporter = GitHubReporter(self.issue_creator)

        # Vulnerability store
        self.vulnerabilities: dict[str, Vulnerability] = {}

        # Wire up callbacks
        self.session_manager.on_status_change(self._on_status_change)

    async def _on_status_change(self, task: RemediationTask, event: str):
        """Handle session status changes — emit metrics, run policy, post evidence."""

        if event == "session_created":
            record_session_created(
                task.devin_session.session_id if task.devin_session else "unknown",
                task.vuln.severity.value, task.vuln.package_name)
            await self.event_emitter.send_event(
                f"🤖 Devin session created for {task.vuln.package_name}",
                f"Severity: {task.vuln.severity.value}\nPredicted: {task.decision.predicted_route}",
                "info", [f"severity:{task.vuln.severity.value}", "source:shieldops"])
            await self.reporter.report_session_created(task)

        elif event in ("session_failed", "session_timeout"):
            record_session_failed(
                task.devin_session.session_id if task.devin_session else "unknown",
                task.vuln.severity.value)
            await self.event_emitter.send_event(
                f"❌ Session failed for {task.vuln.package_name}",
                f"Error: {task.error}", "error",
                [f"severity:{task.vuln.severity.value}", "source:shieldops"])
            await self.reporter.report_failure(task)

        elif event == "intervention":
            await self.event_emitter.send_event(
                f"🔧 Intervention for {task.vuln.package_name}",
                f"Count: {task.intervention_count}", "warning",
                ["source:shieldops"])

        # Update active session gauge
        record_active_sessions(len(self.session_manager.active_tasks))

    async def _process_completed_session(self, task: RemediationTask):
        """Post-session processing: policy evaluation → metrics → evidence bundle → GitHub."""
        structured = task.devin_output or {}
        tests_passed = structured.get("tests_passed", False)
        breaking_changes_detected = structured.get("breaking_changes_detected", False)
        confidence = structured.get("confidence", 0.0)
        files_touched = structured.get("files_touched", [])
        changes_summary = structured.get("changes_summary", "No summary provided.")
        breaking_changes_notes = structured.get("breaking_changes_notes", "")
        reachability_assessment = structured.get("reachability_assessment", "")
        notes = structured.get("notes", "")
        devin_status = structured.get("status", "failed")

        session_id = task.devin_session.session_id if task.devin_session else "unknown"
        severity = task.vuln.severity.value

        # Determine upgrade type
        upgrade_type = "patch"
        if task.vuln.fixed_version and task.vuln.current_version:
            try:
                curr = int(task.vuln.current_version.split(".")[0])
                fix = int(task.vuln.fixed_version.split(".")[0])
                if fix > curr:
                    upgrade_type = "major"
                elif task.vuln.fixed_version.split(".")[1] != task.vuln.current_version.split(".")[1]:
                    upgrade_type = "minor"
            except (ValueError, IndexError):
                pass

        # Determine vuln_type string for policy
        vuln_type_str = "dependency"
        if task.vuln.vuln_type in (VulnerabilityType.SAST, VulnerabilityType.CODE_QUALITY):
            vuln_type_str = "sast"
        elif task.vuln.vuln_type == VulnerabilityType.CONTAINER:
            vuln_type_str = "container"

        # 1. Run policy engine
        policy_result = policy_evaluate(
            severity=severity,
            vuln_type=vuln_type_str,
            upgrade_type=upgrade_type,
            tests_passed=tests_passed,
            breaking_changes_detected=breaking_changes_detected,
            confidence=confidence,
            files_touched=files_touched,
            reachability_assessment=reachability_assessment,
            devin_status=devin_status,
        )

        logger.info(f"Policy: {policy_result.decision.value} for {task.vuln.package_name} — {policy_result.reason}")

        # 2. Emit metrics
        record_session_completed(session_id, severity, task.duration_seconds or 0)
        record_policy_decision(policy_result.decision.value, severity, upgrade_type)
        record_confidence(confidence, policy_result.decision.value)

        acu_used = structured.get("acu_used", 0.0)
        if acu_used:
            record_acu_cost(acu_used, session_id, severity)

        if breaking_changes_detected and policy_result.decision != PolicyDecision.BLOCKED:
            record_breaking_change_handled(task.vuln.package_name, severity)

        # Estimate reviewer minutes saved
        baseline_minutes = 120 if upgrade_type == "major" else 45
        if policy_result.decision == PolicyDecision.AUTO_MERGE_READY:
            record_reviewer_minutes_saved(baseline_minutes, "auto_merge_ready")
        elif policy_result.decision == PolicyDecision.HUMAN_REVIEW:
            record_reviewer_minutes_saved(baseline_minutes * 0.8, "human_review")

        # 3. Build evidence bundle and post to GitHub
        evidence_md = build_evidence(
            vuln=VulnerabilityContext(
                cve_id=task.vuln.cve_id or "N/A",
                package=task.vuln.package_name,
                current_version=task.vuln.current_version,
                fixed_version=task.vuln.fixed_version or "latest",
                severity=severity,
                advisory_url=task.vuln.advisory_url or "",
                upgrade_type=upgrade_type,
            ),
            result=DevinSessionResult(
                session_id=session_id,
                pr_url=task.pr_url,
                status=devin_status,
                changes_summary=changes_summary,
                tests_passed=tests_passed,
                breaking_changes_detected=breaking_changes_detected,
                breaking_changes_notes=breaking_changes_notes,
                reachability_assessment=reachability_assessment,
                confidence=confidence,
                files_touched=files_touched,
                notes=notes,
                duration_seconds=int(task.duration_seconds or 0),
                acu_used=acu_used,
            ),
            policy=policy_result,
        )

        # Post evidence to GitHub issue
        if task.vuln.github_issue_number:
            await self.issue_creator.comment_on_issue(task.vuln.github_issue_number, evidence_md)

        # Emit Datadog event
        decision_emoji = {"auto_merge_ready": "🟢", "human_review": "🟡", "blocked": "🔴"}
        await self.event_emitter.send_event(
            f"{decision_emoji.get(policy_result.decision.value, '⚪')} Policy: "
            f"{policy_result.decision.value} — {task.vuln.package_name}",
            f"Reason: {policy_result.reason}\nConfidence: {confidence:.0%}\n"
            f"Breaking changes: {'Yes' if breaking_changes_detected else 'No'}",
            "success" if policy_result.decision == PolicyDecision.AUTO_MERGE_READY else
            "warning" if policy_result.decision == PolicyDecision.HUMAN_REVIEW else "error",
            [f"severity:{severity}", f"decision:{policy_result.decision.value}", "source:shieldops"],
        )

        # Update vulnerability status
        if policy_result.decision == PolicyDecision.AUTO_MERGE_READY:
            task.vuln.status = RemediationStatus.AUTO_MERGE_READY
        elif policy_result.decision == PolicyDecision.HUMAN_REVIEW:
            task.vuln.status = RemediationStatus.HUMAN_REVIEW
        elif policy_result.decision == PolicyDecision.BLOCKED:
            task.vuln.status = RemediationStatus.BLOCKED

        return policy_result

    async def run_full_pipeline(self):
        """Run: scan → triage → Devin fleet → policy → evidence → report."""
        logger.info("=" * 60)
        logger.info("SHIELDOPS: Starting full pipeline")
        logger.info("=" * 60)

        # Step 1: Scan
        scan_results = await self.scanner.run_all_scans()
        all_vulns = []
        for scan in scan_results:
            record_scan_completed(scan.scanner, len(scan.vulnerabilities),
                                  scan.duration_seconds or 0)
            await self.event_emitter.send_event(
                f"🔍 Scan: {len(scan.vulnerabilities)} vulns ({scan.scanner})",
                f"Scanner: {scan.scanner}", "info",
                [f"scanner:{scan.scanner}", "source:shieldops"])
            all_vulns.extend(scan.vulnerabilities)

        if not all_vulns:
            logger.info("No vulnerabilities — pipeline complete")
            return

        # Step 2: Create GitHub issues
        for scan in scan_results:
            created = await self.issue_creator.create_issues_from_scan(scan)
            for vuln in created:
                self.vulnerabilities[vuln.id] = vuln

        # Step 3: Triage with reachability
        decisions = self.triage.triage(list(self.vulnerabilities.values()))
        unreachable = sum(1 for d in decisions if d.reachable is False)
        record_unreachable_vuln_deprioritized(unreachable)
        logger.info(f"Triage: {len(decisions)} total, {unreachable} unreachable deprioritized")

        # Step 4: Dispatch to Devin
        tasks = await self.session_manager.remediate_batch(decisions)

        # Step 5: Post-session processing (policy + evidence)
        for task in tasks:
            if task.devin_output is not None:
                try:
                    await self._process_completed_session(task)
                except Exception as e:
                    logger.error(f"Post-session processing failed for {task.vuln.package_name}: {e}")

        # Step 6: Update vulnerability gauges
        open_count = sum(1 for v in self.vulnerabilities.values()
                        if v.status not in (RemediationStatus.AUTO_MERGE_READY,
                                            RemediationStatus.PR_MERGED))
        fixed_count = sum(1 for v in self.vulnerabilities.values()
                         if v.status in (RemediationStatus.AUTO_MERGE_READY,
                                         RemediationStatus.PR_MERGED,
                                         RemediationStatus.HUMAN_REVIEW))
        record_vulnerability_counts(open_count, fixed_count)

        stats = self.session_manager.get_stats()
        logger.info("=" * 60)
        logger.info(f"SHIELDOPS: Pipeline complete — {stats['succeeded']} succeeded, {stats['failed']} failed")
        logger.info("=" * 60)
        return stats

    async def remediate_issue(self, issue_number: int, issue_title: str,
                               issue_body: str, labels: list[str]):
        """Webhook-triggered: remediate a specific GitHub issue."""
        severity = Severity.HIGH
        for s in Severity:
            if s.value in [l.lower() for l in labels]:
                severity = s
                break

        vuln_type = VulnerabilityType.PYTHON_DEPENDENCY
        if "npm" in issue_title.lower() or "frontend" in issue_title.lower():
            vuln_type = VulnerabilityType.NPM_DEPENDENCY

        vuln = Vulnerability(
            id=f"webhook-{issue_number}",
            title=issue_title, description=issue_body,
            severity=severity, vuln_type=vuln_type,
            package_name=self._extract_package_name(issue_title),
            current_version="unknown",
            github_issue_number=issue_number,
        )
        self.vulnerabilities[vuln.id] = vuln
        decisions = self.triage.triage([vuln])
        tasks = await self.session_manager.remediate_batch(decisions)
        for task in tasks:
            if task.devin_output is not None:
                await self._process_completed_session(task)

    async def setup_datadog(self):
        """One-time: create dashboard and monitors."""
        errors = []
        try:
            dashboard_url = await self.dashboard_builder.create_or_update()
        except Exception as e:
            dashboard_url = None
            errors.append(str(e))
        try:
            monitors = await self.monitor_builder.create_all()
        except Exception as e:
            monitors = []
            errors.append(str(e))
        result = {"dashboard_url": dashboard_url, "monitors": monitors}
        if errors:
            result["errors"] = errors
        return result

    @staticmethod
    def _extract_package_name(title: str) -> str:
        for word in title.split():
            if word.startswith("CVE-"):
                continue
            if word.lower() not in {"upgrade", "fix", "security", "vulnerability",
                                     "[high]", "[critical]", "[medium]", "[low]",
                                     "—", "-", "npm", "advisory:", "in"}:
                return word.strip("`").strip(":")
        return "unknown"


# === FastAPI Application ===

@asynccontextmanager
async def lifespan(app: FastAPI):
    config = Config.from_env()
    orchestrator = ShieldOpsOrchestrator(config)
    app.state.orchestrator = orchestrator
    app.state.config = config

    configure_webhooks(
        orchestrator, config.github.webhook_secret,
        skip_signature_check=config.skip_signature_check,
    )

    scheduler = ScanScheduler(orchestrator, interval_hours=24)
    app.state.scheduler = scheduler
    if os.getenv("SHIELDOPS_AUTO_SCAN", "true").lower() == "true":
        scheduler.start()

    logger.info("🛡️ ShieldOps v2 — Agent Trust Control Plane — started")
    yield
    scheduler.stop()


app = FastAPI(
    title="🛡️ ShieldOps",
    description="Trust Control Plane for Autonomous Security Remediation — Devin AI + Datadog",
    version="2.0.0",
    lifespan=lifespan,
)

_allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
_origins_list = [o.strip() for o in _allowed_origins.split(",") if o.strip()] if _allowed_origins else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins_list,
    allow_credentials=bool(_origins_list),
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Hub-Signature-256", "X-API-Key"],
)
app.include_router(webhook_router)

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def _require_api_key(
    api_key: Optional[str] = Security(_api_key_header),
) -> str:
    """Dependency that enforces API-key auth on sensitive endpoints.

    If SHIELDOPS_API_KEY is not set the check is skipped so that local
    development still works out of the box.
    """
    expected = os.getenv("SHIELDOPS_API_KEY", "")
    if not expected:
        return ""  # no key configured — allow (dev mode)
    if not api_key or not hmac.compare_digest(api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key


@app.get("/")
async def root():
    return {"name": "ShieldOps", "version": "2.0.0",
            "tagline": "Trust Control Plane for Autonomous Security Remediation"}


@app.get("/health")
async def health():
    o: ShieldOpsOrchestrator = app.state.orchestrator
    devin_healthy = await o.devin.is_healthy()
    return {"status": "healthy" if devin_healthy else "degraded",
            "devin_api": "connected" if devin_healthy else "unreachable",
            "active_sessions": len(o.session_manager.active_tasks)}


@app.get("/status", dependencies=[Security(_require_api_key)])
async def status():
    """The VP endpoint — full fleet + trust + posture status."""
    o: ShieldOpsOrchestrator = app.state.orchestrator
    stats = o.session_manager.get_stats()
    vulns = [{"id": v.id, "title": v.title, "severity": v.severity.value,
              "status": v.status.value, "package": v.package_name,
              "reachable": v.reachable, "policy_decision": v.policy_decision,
              "issue": v.github_issue_number}
             for v in o.vulnerabilities.values()]
    return {"fleet": stats, "vulnerabilities": {"total": len(vulns), "items": vulns},
            "timestamp": datetime.utcnow().isoformat()}


@app.post("/scan", dependencies=[Security(_require_api_key)])
async def trigger_scan(background_tasks: BackgroundTasks):
    scheduler: ScanScheduler = app.state.scheduler
    background_tasks.add_task(scheduler.trigger_manual_scan)
    return {"status": "scan_triggered"}


@app.post("/setup/datadog", dependencies=[Security(_require_api_key)])
async def setup_datadog():
    o: ShieldOpsOrchestrator = app.state.orchestrator
    return await o.setup_datadog()


@app.get("/metrics", dependencies=[Security(_require_api_key)])
async def get_metrics():
    o: ShieldOpsOrchestrator = app.state.orchestrator
    return o.session_manager.get_stats()
