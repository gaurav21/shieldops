from __future__ import annotations

"""ShieldOps — Autonomous Security Remediation Platform.

A trust control plane for an autonomous engineering workforce.
Devin does the judgment-heavy work Dependabot can't. Datadog proves the fleet is safe to run.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from .config import Config
from .scanner.vulnerability_scanner import VulnerabilityScanner
from .scanner.issue_creator import IssueCreator
from .scanner.models import Vulnerability, Severity, VulnerabilityType, RemediationStatus
from .orchestrator.devin_client import DevinClient
from .orchestrator.session_manager import SessionManager, RemediationTask
from .orchestrator.triage import TriageEngine
from .orchestrator.prompt_builder import PromptBuilder
from .orchestrator.policy import PolicyEngine, PolicyDecision
from .observability.metrics import MetricsEmitter
from .observability.events import EventTracker
from .observability.dashboard import DashboardBuilder
from .observability.monitors import MonitorBuilder
from .reporting.github_reporter import GitHubReporter
from .reporting.evidence_bundle import EvidenceBundle
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

        # Core components
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
        self.policy = PolicyEngine()
        self.evidence = EvidenceBundle()
        self.session_manager = SessionManager(
            devin_client=self.devin,
            prompt_builder=self.prompt_builder,
            policy_engine=self.policy,
            max_concurrent=config.devin.max_concurrent_sessions,
            poll_interval=config.devin.poll_interval,
            session_timeout=config.devin.session_timeout,
        )

        # Observability
        self.metrics = MetricsEmitter(config.datadog)
        self.events = EventTracker(config.datadog)
        self.dashboard_builder = DashboardBuilder(config.datadog)
        self.monitor_builder = MonitorBuilder(config.datadog)

        # Reporting
        self.reporter = GitHubReporter(self.issue_creator)

        # Vulnerability store
        self.vulnerabilities: dict[str, Vulnerability] = {}

        # Wire up callbacks
        self.session_manager.on_status_change(self._on_status_change)

    async def _on_status_change(self, task: RemediationTask, event: str):
        """Handle session status changes — the event-driven observability loop."""

        if event == "session_created":
            await asyncio.gather(
                self.metrics.emit_session_created(task),
                self.events.session_created(task),
                self.reporter.report_session_created(task),
            )

        elif event in ("auto_merge_ready", "human_review", "blocked"):
            # Policy decision made — the key audit event
            if task.policy_result:
                await asyncio.gather(
                    self.metrics.emit_session_completed(task),
                    self.metrics.emit_policy_decision(task, task.policy_result),
                    self.events.policy_decision(task, task.policy_result),
                )
                # Report to GitHub with evidence bundle
                if event == "auto_merge_ready":
                    comment = self.evidence.build_issue_comment(
                        task.vuln, task.policy_result, task.devin_output,
                        task.pr_url, task.devin_session.url if task.devin_session else None)
                    if task.vuln.github_issue_number:
                        await self.issue_creator.comment_on_issue(
                            task.vuln.github_issue_number, comment)
                elif event == "human_review":
                    comment = self.evidence.build_issue_comment(
                        task.vuln, task.policy_result, task.devin_output,
                        task.pr_url, task.devin_session.url if task.devin_session else None)
                    if task.vuln.github_issue_number:
                        await self.issue_creator.comment_on_issue(
                            task.vuln.github_issue_number, comment)
                elif event == "blocked":
                    comment = self.evidence.build_issue_comment(
                        task.vuln, task.policy_result, task.devin_output,
                        None, task.devin_session.url if task.devin_session else None)
                    if task.vuln.github_issue_number:
                        await self.issue_creator.comment_on_issue(
                            task.vuln.github_issue_number, comment)

        elif event in ("session_failed", "session_timeout"):
            await asyncio.gather(
                self.metrics.emit_session_failed(task),
                self.events.session_failed(task),
                self.reporter.report_failure(task),
            )

        elif event == "intervention":
            await self.events.intervention(task)

        # Always emit fleet stats + vuln gauges
        stats = self.session_manager.get_stats()
        await self.metrics.emit_fleet_stats(stats)

        open_count = sum(1 for v in self.vulnerabilities.values()
                        if v.status not in (RemediationStatus.AUTO_MERGE_READY,
                                            RemediationStatus.PR_MERGED,
                                            RemediationStatus.HUMAN_REVIEW))
        fixed_count = sum(1 for v in self.vulnerabilities.values()
                         if v.status in (RemediationStatus.AUTO_MERGE_READY,
                                         RemediationStatus.PR_MERGED,
                                         RemediationStatus.HUMAN_REVIEW))
        unreachable = sum(1 for v in self.vulnerabilities.values() if v.reachable is False)
        await self.metrics.emit_vulnerability_gauge(open_count, fixed_count, unreachable)

    async def run_full_pipeline(self):
        """Run: scan → triage (with reachability) → Devin fleet → policy → evidence → report."""
        logger.info("=" * 60)
        logger.info("SHIELDOPS: Starting full pipeline")
        logger.info("=" * 60)

        # Step 1: Scan
        logger.info("Step 1: Scanning...")
        scan_results = await self.scanner.run_all_scans()
        all_vulns = []
        for scan in scan_results:
            await self.metrics.emit_scan_metrics(scan)
            await self.events.scan_completed(scan)
            all_vulns.extend(scan.vulnerabilities)
        logger.info(f"Step 1: {len(all_vulns)} vulnerabilities found")

        if not all_vulns:
            logger.info("No vulnerabilities — pipeline complete")
            return

        # Step 2: Create GitHub issues
        logger.info("Step 2: Creating GitHub issues...")
        for scan in scan_results:
            created = await self.issue_creator.create_issues_from_scan(scan)
            for vuln in created:
                self.vulnerabilities[vuln.id] = vuln

        # Step 3: Triage with reachability
        logger.info("Step 3: Triaging (with reachability check)...")
        decisions = self.triage.triage(list(self.vulnerabilities.values()))
        actionable = [d for d in decisions if d.should_remediate]
        unreachable = sum(1 for d in decisions if d.reachable is False)
        logger.info(f"Step 3: {len(actionable)} actionable, {unreachable} deprioritized (unreachable)")

        # Log predicted routes
        predicted = {}
        for d in actionable:
            predicted[d.predicted_route] = predicted.get(d.predicted_route, 0) + 1
        logger.info(f"Step 3: Predicted routes: {predicted}")

        # Step 4: Dispatch to Devin → policy → evidence
        logger.info("Step 4: Dispatching to Devin fleet...")
        tasks = await self.session_manager.remediate_batch(decisions)

        # Step 5: Summary
        stats = self.session_manager.get_stats()
        logger.info("=" * 60)
        logger.info("SHIELDOPS: Pipeline complete")
        logger.info(f"  Scanned:                  {len(all_vulns)}")
        logger.info(f"  Unreachable (skipped):     {unreachable}")
        logger.info(f"  Remediated:               {stats['completed']}")
        logger.info(f"  Auto-merge ready:          {stats['auto_merge_ready']}")
        logger.info(f"  Human review needed:       {stats['human_review']}")
        logger.info(f"  Blocked:                   {stats['blocked']}")
        logger.info(f"  Breaking changes handled:  {stats['breaking_changes_handled']}")
        logger.info(f"  Success rate:              {stats['success_rate']:.1f}%")
        logger.info(f"  Intervention rate:         {stats['intervention_rate']:.1f}%")
        logger.info("=" * 60)
        return stats

    async def remediate_issue(self, issue_number: int, issue_title: str,
                               issue_body: str, labels: list[str]):
        """Webhook-triggered: remediate a specific GitHub issue."""
        logger.info(f"Webhook: Remediating issue #{issue_number}")

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
            title=issue_title,
            description=issue_body,
            severity=severity,
            vuln_type=vuln_type,
            package_name=self._extract_package_name(issue_title),
            current_version="unknown",
            github_issue_number=issue_number,
        )
        self.vulnerabilities[vuln.id] = vuln
        decisions = self.triage.triage([vuln])
        await self.session_manager.remediate_batch(decisions)

    async def setup_datadog(self):
        """One-time: create dashboard and monitors."""
        logger.info("Setting up Datadog resources...")
        dashboard_url = await self.dashboard_builder.create_or_update()
        monitors = await self.monitor_builder.create_all()
        return {"dashboard_url": dashboard_url, "monitors": monitors}

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

    configure_webhooks(orchestrator, config.github.webhook_secret)

    scheduler = ScanScheduler(orchestrator, interval_hours=24)
    app.state.scheduler = scheduler
    if os.getenv("SHIELDOPS_AUTO_SCAN", "true").lower() == "true":
        scheduler.start()

    logger.info("🛡️ ShieldOps v2 — Agent Trust Control Plane — started")
    yield
    scheduler.stop()
    logger.info("🛡️ ShieldOps stopped")


app = FastAPI(
    title="🛡️ ShieldOps",
    description="Trust Control Plane for Autonomous Security Remediation — Devin AI + Datadog",
    version="2.0.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(webhook_router)


@app.get("/")
async def root():
    return {
        "name": "ShieldOps",
        "version": "2.0.0",
        "tagline": "Trust Control Plane for Autonomous Security Remediation",
        "status": "running",
    }


@app.get("/health")
async def health():
    o: ShieldOpsOrchestrator = app.state.orchestrator
    devin_healthy = await o.devin.is_healthy()
    return {
        "status": "healthy" if devin_healthy else "degraded",
        "devin_api": "connected" if devin_healthy else "unreachable",
        "active_sessions": len(o.session_manager.active_tasks),
        "total_vulnerabilities": len(o.vulnerabilities),
    }


@app.get("/status")
async def status():
    """The VP endpoint — full fleet + trust + posture status."""
    o: ShieldOpsOrchestrator = app.state.orchestrator
    stats = o.session_manager.get_stats()

    vulns = [
        {
            "id": v.id, "title": v.title, "severity": v.severity.value,
            "status": v.status.value, "package": v.package_name,
            "reachable": v.reachable, "policy_decision": v.policy_decision,
            "confidence": v.confidence, "issue": v.github_issue_number,
            "devin_session": v.devin_session_id,
        }
        for v in o.vulnerabilities.values()
    ]

    return {
        "fleet": {
            "active_sessions": stats["active_sessions"],
            "success_rate": stats["success_rate"],
            "intervention_rate": stats["intervention_rate"],
            "avg_confidence": stats["avg_confidence"],
        },
        "trust_split": {
            "auto_merge_ready": stats["auto_merge_ready"],
            "human_review": stats["human_review"],
            "blocked": stats["blocked"],
        },
        "the_dependabot_cant_metric": {
            "breaking_changes_handled": stats["breaking_changes_handled"],
        },
        "vulnerabilities": {"total": len(vulns), "items": vulns},
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/scan")
async def trigger_scan(background_tasks: BackgroundTasks):
    scheduler: ScanScheduler = app.state.scheduler
    background_tasks.add_task(scheduler.trigger_manual_scan)
    return {"status": "scan_triggered"}


@app.post("/setup/datadog")
async def setup_datadog():
    o: ShieldOpsOrchestrator = app.state.orchestrator
    return await o.setup_datadog()


@app.get("/metrics")
async def get_metrics():
    o: ShieldOpsOrchestrator = app.state.orchestrator
    return o.session_manager.get_stats()
