from __future__ import annotations

"""
policy.py — Trust Boundary for ShieldOps
Routes each Devin remediation result to one of three outcomes:
  AUTO_MERGE_READY → safe to merge without human review
  HUMAN_REVIEW → PR created, labeled needs-human, reviewer packet attached
  BLOCKED → no PR merged, issue commented, Datadog alert fired
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional

from ..shared.constants import SENSITIVE_PATHS

SENSITIVE_KEYWORDS = ["auth", "crypto", "password", "token", "secret", "sql", "injection"]


class PolicyDecision(str, Enum):
    AUTO_MERGE_READY = "auto_merge_ready"
    HUMAN_REVIEW = "human_review"
    BLOCKED = "blocked"


@dataclass
class PolicyResult:
    decision: PolicyDecision
    reason: str
    risk_flags: list[str]
    reviewer_notes: str


def evaluate(
    severity: str,
    vuln_type: str,
    upgrade_type: str,
    tests_passed: bool,
    breaking_changes_detected: bool,
    confidence: float,
    files_touched: list[str],
    reachability_assessment: Optional[str] = None,
    devin_status: str = "success",
) -> PolicyResult:
    """
    Apply routing logic and return a PolicyResult.
    Logic is explicit and ordered — first matching rule wins.
    """
    risk_flags = []

    # --- Collect all risk flags ---
    if not tests_passed:
        risk_flags.append("tests_failed")
    if confidence < 0.5:
        risk_flags.append("low_confidence")
    if devin_status in ("error", "timed_out", "failed"):
        risk_flags.append(f"devin_status_{devin_status}")
    if breaking_changes_detected:
        risk_flags.append("breaking_changes_detected")
    if upgrade_type == "major":
        risk_flags.append("major_version_bump")
    if vuln_type in ("sast", "container"):
        risk_flags.append(f"complex_vuln_type_{vuln_type}")
    if any(_is_sensitive(f) for f in files_touched):
        risk_flags.append("sensitive_path_touched")

    # --- BLOCKED: agent could not produce a trustworthy result ---
    if not tests_passed:
        return PolicyResult(
            decision=PolicyDecision.BLOCKED,
            reason="Tests did not pass — no PR should be merged.",
            risk_flags=risk_flags,
            reviewer_notes="Devin session produced a failing build. Investigate manually or re-queue.",
        )
    if confidence < 0.5:
        return PolicyResult(
            decision=PolicyDecision.BLOCKED,
            reason=f"Devin confidence too low ({confidence:.0%}) to trust the output.",
            risk_flags=risk_flags,
            reviewer_notes="Confidence below 50%. The fix may be incomplete or incorrect. Do not merge.",
        )
    if devin_status in ("error", "timed_out", "failed"):
        return PolicyResult(
            decision=PolicyDecision.BLOCKED,
            reason=f"Devin session ended with status '{devin_status}'.",
            risk_flags=risk_flags,
            reviewer_notes="Session did not complete successfully. No PR should exist. Retry or escalate.",
        )

    # --- HUMAN_REVIEW: agent succeeded but change needs a human eye ---
    human_review_reasons = []
    if upgrade_type == "major":
        human_review_reasons.append("major version bump")
    if breaking_changes_detected:
        human_review_reasons.append("breaking changes detected and remediated by Devin")
    if vuln_type in ("sast", "container"):
        human_review_reasons.append(f"vulnerability type '{vuln_type}' involves code logic, not a dependency pin")
    if any(_is_sensitive(f) for f in files_touched):
        human_review_reasons.append("sensitive path touched (auth/SQL/crypto/views)")
    if 0.5 <= confidence < 0.8:
        human_review_reasons.append(f"confidence {confidence:.0%} — within acceptable range but not high")

    if human_review_reasons:
        return PolicyResult(
            decision=PolicyDecision.HUMAN_REVIEW,
            reason="Human review required: " + "; ".join(human_review_reasons),
            risk_flags=risk_flags,
            reviewer_notes=(
                "PR is labeled `needs-human`. Review the evidence bundle below. "
                "Expected review time: ~2 minutes. All tests pass."
            ),
        )

    # --- AUTO_MERGE_READY: low-risk, high-confidence, tests green ---
    return PolicyResult(
        decision=PolicyDecision.AUTO_MERGE_READY,
        reason=(
            f"Patch/minor dependency fix, tests pass, confidence {confidence:.0%}, "
            "no sensitive paths, no breaking changes."
        ),
        risk_flags=risk_flags,
        reviewer_notes="Safe to auto-merge. No human action required.",
    )


def _is_sensitive(filepath: str) -> bool:
    """Return True if the file touches a sensitive area of the codebase."""
    for pattern in SENSITIVE_PATHS:
        if filepath.startswith(pattern):
            return True
    lower = filepath.lower()
    return any(kw in lower for kw in SENSITIVE_KEYWORDS)
