from __future__ import annotations

#!/usr/bin/env python3
"""Demo script — simulates the full ShieldOps pipeline for recording.

This script demonstrates the end-to-end flow:
1. Scans a repo for vulnerabilities (or uses mock data)
2. Creates GitHub issues
3. Dispatches Devin sessions
4. Emits metrics to Datadog
5. Shows real-time status updates

Usage:
    # With real scanning (needs repo cloned):
    python scripts/demo.py --mode live

    # With mock data (for quick demo):
    python scripts/demo.py --mode mock

    # Just create Datadog dashboard:
    python scripts/demo.py --mode setup
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.scanner.models import (
    ScanResult, Vulnerability, Severity, VulnerabilityType, RemediationStatus,
)
from src.orchestrator.triage import TriageEngine
from src.observability.metrics import MetricsEmitter
from src.observability.events import EventTracker


# Realistic mock vulnerabilities based on common Superset dependencies
MOCK_VULNERABILITIES = [
    Vulnerability(
        id="mock-001",
        title="Upgrade Flask — CVE-2023-30861",
        description="Flask before 2.3.2 has a cookie session vulnerability allowing session fixation.",
        severity=Severity.HIGH,
        vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
        package_name="flask",
        current_version="2.2.5",
        fixed_version="2.3.2",
        cve_id="CVE-2023-30861",
        advisory_url="https://nvd.nist.gov/vuln/detail/CVE-2023-30861",
        file_path="requirements/base.txt",
        scanner="pip-audit",
    ),
    Vulnerability(
        id="mock-002",
        title="Upgrade Werkzeug — CVE-2024-34069",
        description="Werkzeug debugger allows remote code execution when debug mode is enabled.",
        severity=Severity.CRITICAL,
        vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
        package_name="werkzeug",
        current_version="2.3.7",
        fixed_version="3.0.3",
        cve_id="CVE-2024-34069",
        advisory_url="https://nvd.nist.gov/vuln/detail/CVE-2024-34069",
        file_path="requirements/base.txt",
        scanner="pip-audit",
    ),
    Vulnerability(
        id="mock-003",
        title="Upgrade SQLAlchemy — CVE-2024-1135",
        description="SQLAlchemy allows SQL injection through crafted values in certain filter expressions.",
        severity=Severity.CRITICAL,
        vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
        package_name="sqlalchemy",
        current_version="1.4.50",
        fixed_version="1.4.52",
        cve_id="CVE-2024-1135",
        advisory_url="https://nvd.nist.gov/vuln/detail/CVE-2024-1135",
        file_path="requirements/base.txt",
        scanner="pip-audit",
    ),
    Vulnerability(
        id="mock-004",
        title="npm advisory: nth-check — Inefficient Regular Expression Complexity",
        description="nth-check is vulnerable to ReDoS (Regular Expression Denial of Service).",
        severity=Severity.HIGH,
        vuln_type=VulnerabilityType.NPM_DEPENDENCY,
        package_name="nth-check",
        current_version="1.0.2",
        fixed_version="2.0.1",
        advisory_url="https://github.com/advisories/GHSA-rp65-9cf3-cjxr",
        file_path="superset-frontend/package.json",
        scanner="npm-audit",
    ),
    Vulnerability(
        id="mock-005",
        title="npm advisory: postcss — Line return parsing error",
        description="PostCSS line return parsing error could lead to information exposure.",
        severity=Severity.MEDIUM,
        vuln_type=VulnerabilityType.NPM_DEPENDENCY,
        package_name="postcss",
        current_version="8.4.21",
        fixed_version="8.4.31",
        advisory_url="https://github.com/advisories/GHSA-7fh5-64p2-3v2j",
        file_path="superset-frontend/package.json",
        scanner="npm-audit",
    ),
    Vulnerability(
        id="mock-006",
        title="Upgrade Jinja2 — CVE-2024-22195",
        description="Jinja2 before 3.1.3 has XSS via xmlattr filter.",
        severity=Severity.MEDIUM,
        vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
        package_name="jinja2",
        current_version="3.1.2",
        fixed_version="3.1.3",
        cve_id="CVE-2024-22195",
        advisory_url="https://nvd.nist.gov/vuln/detail/CVE-2024-22195",
        file_path="requirements/base.txt",
        scanner="pip-audit",
    ),
    Vulnerability(
        id="mock-007",
        title="Upgrade cryptography — CVE-2024-26130",
        description="cryptography before 42.0.4 has a NULL pointer dereference in PKCS12 parsing.",
        severity=Severity.HIGH,
        vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
        package_name="cryptography",
        current_version="41.0.7",
        fixed_version="42.0.4",
        cve_id="CVE-2024-26130",
        advisory_url="https://nvd.nist.gov/vuln/detail/CVE-2024-26130",
        file_path="requirements/base.txt",
        scanner="pip-audit",
    ),
    Vulnerability(
        id="mock-008",
        title="SAST: Potential SQL injection in custom SQL query handler",
        description="String formatting used for SQL query construction instead of parameterized queries.",
        severity=Severity.HIGH,
        vuln_type=VulnerabilityType.SAST,
        package_name="python.lang.security.audit.formatted-sql-query",
        current_version="N/A",
        file_path="superset/sql_lab.py",
        line_number=142,
        scanner="semgrep",
    ),
]


async def run_mock_demo(config: Config):
    """Run demo with mock data — shows the full pipeline flow."""
    print("🛡️ ShieldOps Demo — Mock Mode")
    print("=" * 60)

    metrics = MetricsEmitter(config.datadog)
    events = EventTracker(config.datadog)
    triage = TriageEngine()

    # Step 1: Simulate scan
    print("\n📡 Step 1: Scanning repository for vulnerabilities...")
    scan = ScanResult(
        scan_id="demo-scan-001",
        scanner="multi-scanner",
        started_at=datetime.utcnow(),
        vulnerabilities=MOCK_VULNERABILITIES,
    )
    scan.completed_at = datetime.utcnow()

    await metrics.emit_scan_metrics(scan)
    await events.scan_completed(scan)

    print(f"   Found {len(scan.vulnerabilities)} vulnerabilities:")
    for v in scan.vulnerabilities:
        print(f"   {'🔴' if v.severity == Severity.CRITICAL else '🟡' if v.severity == Severity.HIGH else '🟢'} "
              f"[{v.severity.value.upper()}] {v.title}")

    # Step 2: Triage
    print(f"\n🎯 Step 2: Triaging {len(scan.vulnerabilities)} vulnerabilities...")
    decisions = triage.triage(scan.vulnerabilities)
    actionable = [d for d in decisions if d.should_remediate]

    print(f"   {len(actionable)} vulnerabilities selected for remediation:")
    for d in decisions:
        emoji = "✅" if d.should_remediate else "⏭️"
        print(f"   {emoji} Score: {d.priority_score:5.1f} | {d.estimated_complexity:8s} | {d.vulnerability.title}")

    # Step 3: Simulate Devin sessions
    print(f"\n🤖 Step 3: Dispatching {len(actionable)} tasks to Devin...")
    for i, d in enumerate(actionable):
        print(f"\n   [{i+1}/{len(actionable)}] Creating session for: {d.vulnerability.package_name}")
        print(f"   Severity: {d.vulnerability.severity.value} | Priority: {d.priority_score}")
        print(f"   ➡️  Devin session would be created here")

        # Emit metrics as if sessions were running
        await metrics.emit_vulnerability_gauge(
            open_count=len(actionable) - i,
            fixed_count=i,
        )

    # Step 4: Summary
    print("\n" + "=" * 60)
    print("📊 Pipeline Summary")
    print("=" * 60)
    print(f"   Vulnerabilities found: {len(scan.vulnerabilities)}")
    print(f"   Actionable:           {len(actionable)}")
    print(f"   Critical:             {sum(1 for v in scan.vulnerabilities if v.severity == Severity.CRITICAL)}")
    print(f"   High:                 {sum(1 for v in scan.vulnerabilities if v.severity == Severity.HIGH)}")
    print(f"   Medium:               {sum(1 for v in scan.vulnerabilities if v.severity == Severity.MEDIUM)}")
    print(f"\n   Metrics sent to Datadog ✅")
    print(f"   Events sent to Datadog ✅")

    # Final vulnerability gauge
    await metrics.emit_pipeline_stats({
        "active_sessions": 0,
        "success_rate": 0,
        "avg_duration_seconds": 0,
    })


async def main():
    parser = argparse.ArgumentParser(description="ShieldOps Demo")
    parser.add_argument("--mode", choices=["mock", "live", "setup"], default="mock",
                       help="Demo mode: mock (simulated), live (real scanning), setup (Datadog only)")
    args = parser.parse_args()

    config = Config.from_env()

    if args.mode == "mock":
        await run_mock_demo(config)
    elif args.mode == "setup":
        from src.observability.dashboard import DashboardBuilder
        from src.observability.monitors import MonitorBuilder

        print("🛡️ Setting up Datadog resources...")
        db = DashboardBuilder(config.datadog)
        url = await db.create_or_update()
        print(f"Dashboard: {url}")

        mb = MonitorBuilder(config.datadog)
        monitors = await mb.create_all()
        print(f"Created {len(monitors)} monitors")
    elif args.mode == "live":
        print("🛡️ Live mode — running full pipeline...")
        # Would import and run the full orchestrator
        print("   (Requires DEVIN_API_KEY and GITHUB_TOKEN)")


if __name__ == "__main__":
    asyncio.run(main())
