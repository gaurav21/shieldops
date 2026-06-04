#!/usr/bin/env python3
from __future__ import annotations

"""
demo_replay.py — Deterministic demo replay for Loom recording.

Usage:
    python scripts/demo_replay.py --mode replay --issue-url https://github.com/gaurav21/superset/issues/2
    python scripts/demo_replay.py --mode live    # Real Devin session (burns ACU)
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestrator.policy import evaluate as policy_evaluate, PolicyDecision
from src.reporting.evidence_bundle import build as build_evidence, DevinSessionResult, VulnerabilityContext

HERO_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "hero_session")


def narrate(step: int, msg: str):
    """Print timestamped narration line."""
    elapsed = step * 3  # Simulated seconds
    mm, ss = divmod(elapsed, 60)
    print(f"  [{mm:02d}:{ss:02d}] {msg}")


def run_replay(issue_url: str):
    """Replay the hero session from cached artifacts."""
    print("🛡️ ShieldOps Demo — Replay Mode")
    print("=" * 60)

    # Load cached session result
    result_path = os.path.join(HERO_DIR, "session_result.json")
    if not os.path.exists(result_path):
        print(f"❌ No cached session at {result_path}")
        print("   Run a real Devin session first and save artifacts to docs/hero_session/")
        sys.exit(1)

    with open(result_path) as f:
        session_data = json.load(f)

    structured = session_data.get("structured_output", {})

    print()
    narrate(0, "Starting ShieldOps demo replay")
    narrate(1, "Loading vulnerability: CVE-2023-30861 — Flask 2.2.5 → 3.0.3 (MAJOR, HIGH)")

    time.sleep(1)

    # Triage
    narrate(2, "Triage score: 87/100 | Upgrade type: major | Reachable: YES")
    narrate(3, "Devin session: [replaying from cached artifacts]")

    time.sleep(1)

    # Simulate the hero moment
    if structured.get("breaking_changes_detected"):
        narrate(8, "First attempt: tests FAILED — import errors detected")
        narrate(12, "Devin reads Flask 3.0 migration guide...")
        narrate(18, f"Devin fixes {len(structured.get('files_touched', []))} files across the codebase")
        narrate(24, f"Re-running tests... PASSED")
    else:
        narrate(12, "Tests passed on first attempt")

    time.sleep(1)

    # Policy evaluation — using the REAL policy engine
    policy_result = policy_evaluate(
        severity="high",
        vuln_type="dependency",
        upgrade_type="major",
        tests_passed=structured.get("tests_passed", False),
        breaking_changes_detected=structured.get("breaking_changes_detected", False),
        confidence=structured.get("confidence", 0.0),
        files_touched=structured.get("files_touched", []),
        reachability_assessment=structured.get("reachability_assessment", ""),
        devin_status=structured.get("status", "success"),
    )

    narrate(25, f"Policy engine: {policy_result.decision.value.upper()} "
                f"({policy_result.reason[:80]}...)")

    # Build evidence bundle — using the REAL evidence builder
    evidence_md = build_evidence(
        vuln=VulnerabilityContext(
            cve_id="CVE-2023-30861",
            package="flask",
            current_version="2.2.5",
            fixed_version="3.0.3",
            severity="high",
            advisory_url="https://nvd.nist.gov/vuln/detail/CVE-2023-30861",
            upgrade_type="major",
        ),
        result=DevinSessionResult(
            session_id=session_data.get("session_id", "demo"),
            pr_url=structured.get("pr_url"),
            status=structured.get("status", "success"),
            changes_summary=structured.get("changes_summary", ""),
            tests_passed=structured.get("tests_passed", False),
            breaking_changes_detected=structured.get("breaking_changes_detected", False),
            breaking_changes_notes=structured.get("breaking_changes_notes", ""),
            reachability_assessment=structured.get("reachability_assessment", ""),
            confidence=structured.get("confidence", 0.0),
            files_touched=structured.get("files_touched", []),
            notes=structured.get("notes", ""),
            duration_seconds=session_data.get("duration_seconds", 0),
            acu_used=session_data.get("acu_used", 0.0),
        ),
        policy=policy_result,
    )

    narrate(26, f"Evidence bundle built — {len(evidence_md)} chars")
    if issue_url:
        narrate(27, f"Would post to: {issue_url}")
    narrate(28, f"✅ Demo complete. PR URL: {structured.get('pr_url', 'N/A')}")

    print()
    print("=" * 60)
    print("📋 Policy Decision:")
    print(f"   {policy_result.decision.value} — {policy_result.reason}")
    print(f"   Risk flags: {policy_result.risk_flags}")
    print()
    print("📝 Evidence Bundle Preview (first 500 chars):")
    print("-" * 40)
    print(evidence_md[:500])
    print("-" * 40)


def run_live():
    """Run a real Devin session on the Flask hero case."""
    print("🛡️ ShieldOps Demo — Live Mode")
    print("⚠️  This will create a real Devin session and burn ACU budget.")
    print("   Requires DEVIN_API_KEY and GITHUB_TOKEN environment variables.")
    print()
    print("   Not yet implemented — run the full pipeline via:")
    print("   curl -X POST http://localhost:8000/scan")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="ShieldOps Demo Replay")
    parser.add_argument("--mode", choices=["replay", "live"], default="replay")
    parser.add_argument("--issue-url", default="", help="GitHub issue URL to post evidence to")
    args = parser.parse_args()

    if args.mode == "replay":
        run_replay(args.issue_url)
    elif args.mode == "live":
        run_live()


if __name__ == "__main__":
    main()
