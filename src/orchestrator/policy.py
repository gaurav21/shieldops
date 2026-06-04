from __future__ import annotations

"""Policy / Trust boundary — the component that makes a VP comfortable running an agent fleet.

Routes each Devin remediation result through a policy-as-code decision:
  AUTO_MERGE_READY — safe to merge without human review
  HUMAN_REVIEW     — PR created but labeled `needs-human`, evidence bundle attached
  BLOCKED          — nothing merged, issue commented, alert fired

This is the core differentiator: not "can Devin open a PR?" but "can you *trust* what it opens?"
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ..scanner.models import Vulnerability, VulnerabilityType, Severity

logger = logging.getLogger(__name__)


class PolicyDecision(str, Enum):
    AUTO_MERGE_READY = "auto_merge_ready"
    HUMAN_REVIEW = "human_review"
    BLOCKED = "blocked"


class UpgradeType(str, Enum):
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"
    UNKNOWN = "unknown"


# Paths that always require human review — auth, SQL, crypto, user-facing views
SENSITIVE_PATHS = {
    "superset/sql_lab.py",
    "superset/views/",
    "superset/security/",
    "superset/models/core.py",
    "superset/connectors/",
    "superset/db_engine_specs/",
    "superset/utils/encrypt.py",
}


@dataclass
class PolicyResult:
    """The output of the trust boundary evaluation."""
    decision: PolicyDecision
    reason: str
    confidence: float                  # Devin's self-reported confidence (0.0-1.0)
    breaking_changes_detected: bool
    sensitive_paths_touched: list[str]  # which sensitive paths Devin modified
    files_touched: list[str]
    upgrade_type: UpgradeType
    auto_merge_eligible: bool          # pre-policy: would this *qualify* for auto-merge?
    evidence_summary: str              # one-line for dashboards/events

    @property
    def label(self) -> str:
        """GitHub label to apply."""
        return {
            PolicyDecision.AUTO_MERGE_READY: "auto-merge-ready",
            PolicyDecision.HUMAN_REVIEW: "needs-human",
            PolicyDecision.BLOCKED: "blocked",
        }[self.decision]


class PolicyEngine:
    """Evaluates Devin's remediation output against trust policies.
    
    The policy is explicit and auditable — every decision has a reason string
    that shows up in the Datadog event stream and the GitHub evidence bundle.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.8,
        block_confidence_threshold: float = 0.5,
        sensitive_paths: Optional[set[str]] = None,
    ):
        self.confidence_threshold = confidence_threshold
        self.block_confidence_threshold = block_confidence_threshold
        self.sensitive_paths = sensitive_paths or SENSITIVE_PATHS

    def evaluate(
        self,
        vuln: Vulnerability,
        devin_output: Optional[dict],
        devin_status: str,
    ) -> PolicyResult:
        """Evaluate a completed Devin session against the trust policy.
        
        Args:
            vuln: The vulnerability being remediated
            devin_output: Devin's structured output (may be None if session failed)
            devin_status: Devin session status (stopped, error, timed_out, etc.)
        """
        # Extract fields from Devin's structured output (with safe defaults)
        output = devin_output or {}
        tests_passed = output.get("tests_passed", False)
        breaking_changes = output.get("breaking_changes_detected", False)
        confidence = output.get("confidence", 0.0)
        files_touched = output.get("files_touched", [])
        changes_summary = output.get("changes_summary", "")
        reachability = output.get("reachability_assessment", "")
        notes = output.get("notes", "")
        devin_status_field = output.get("status", "failed")

        # Determine upgrade type from version strings
        upgrade_type = self._classify_upgrade(vuln.current_version, vuln.fixed_version)

        # Find sensitive paths touched
        sensitive_touched = [
            f for f in files_touched
            if any(f.startswith(sp.rstrip("/")) for sp in self.sensitive_paths)
        ]

        # === BLOCKED conditions (checked first — these are hard stops) ===

        if devin_status in ("error", "timed_out"):
            return self._blocked(
                reason=f"Devin session ended with status: {devin_status}",
                confidence=confidence,
                breaking_changes=breaking_changes,
                sensitive_touched=sensitive_touched,
                files_touched=files_touched,
                upgrade_type=upgrade_type,
            )

        if not tests_passed:
            return self._blocked(
                reason="Tests did not pass — cannot trust the change",
                confidence=confidence,
                breaking_changes=breaking_changes,
                sensitive_touched=sensitive_touched,
                files_touched=files_touched,
                upgrade_type=upgrade_type,
            )

        if confidence < self.block_confidence_threshold:
            return self._blocked(
                reason=f"Confidence too low ({confidence:.2f} < {self.block_confidence_threshold})",
                confidence=confidence,
                breaking_changes=breaking_changes,
                sensitive_touched=sensitive_touched,
                files_touched=files_touched,
                upgrade_type=upgrade_type,
            )

        if devin_status_field == "failed":
            return self._blocked(
                reason="Devin reported failure in structured output",
                confidence=confidence,
                breaking_changes=breaking_changes,
                sensitive_touched=sensitive_touched,
                files_touched=files_touched,
                upgrade_type=upgrade_type,
            )

        # === HUMAN_REVIEW conditions ===

        human_reasons = []

        if upgrade_type == UpgradeType.MAJOR:
            human_reasons.append("major version upgrade")

        if breaking_changes:
            human_reasons.append("breaking changes detected and fixed")

        if vuln.vuln_type in (VulnerabilityType.SAST, VulnerabilityType.CODE_QUALITY):
            human_reasons.append(f"code-level fix ({vuln.vuln_type.value})")

        if sensitive_touched:
            human_reasons.append(f"sensitive paths touched: {', '.join(sensitive_touched)}")

        if confidence < self.confidence_threshold:
            human_reasons.append(f"confidence below threshold ({confidence:.2f} < {self.confidence_threshold})")

        if human_reasons:
            reason = "Human review required: " + "; ".join(human_reasons)
            evidence = (
                f"{vuln.package_name} {vuln.current_version}→{vuln.fixed_version or 'latest'} "
                f"({upgrade_type.value}): {', '.join(human_reasons)}"
            )
            return PolicyResult(
                decision=PolicyDecision.HUMAN_REVIEW,
                reason=reason,
                confidence=confidence,
                breaking_changes_detected=breaking_changes,
                sensitive_paths_touched=sensitive_touched,
                files_touched=files_touched,
                upgrade_type=upgrade_type,
                auto_merge_eligible=False,
                evidence_summary=evidence,
            )

        # === AUTO_MERGE_READY — all checks passed ===

        # Final guard: only dependency upgrades can auto-merge
        if vuln.vuln_type not in (VulnerabilityType.PYTHON_DEPENDENCY, VulnerabilityType.NPM_DEPENDENCY):
            return PolicyResult(
                decision=PolicyDecision.HUMAN_REVIEW,
                reason=f"Non-dependency fix ({vuln.vuln_type.value}) always requires human review",
                confidence=confidence,
                breaking_changes_detected=breaking_changes,
                sensitive_paths_touched=sensitive_touched,
                files_touched=files_touched,
                upgrade_type=upgrade_type,
                auto_merge_eligible=False,
                evidence_summary=f"{vuln.package_name}: non-dependency fix",
            )

        evidence = (
            f"{vuln.package_name} {vuln.current_version}→{vuln.fixed_version or 'latest'} "
            f"({upgrade_type.value}): tests pass, confidence {confidence:.2f}, "
            f"no breaking changes, no sensitive paths"
        )

        logger.info(f"AUTO_MERGE_READY: {vuln.package_name} — {evidence}")

        return PolicyResult(
            decision=PolicyDecision.AUTO_MERGE_READY,
            reason="All auto-merge criteria met: tests pass, no breaking changes, "
                   f"confidence {confidence:.2f} ≥ {self.confidence_threshold}, "
                   f"{upgrade_type.value} upgrade, dependency type, no sensitive paths",
            confidence=confidence,
            breaking_changes_detected=False,
            sensitive_paths_touched=[],
            files_touched=files_touched,
            upgrade_type=upgrade_type,
            auto_merge_eligible=True,
            evidence_summary=evidence,
        )

    def _blocked(self, reason: str, confidence: float, breaking_changes: bool,
                 sensitive_touched: list, files_touched: list,
                 upgrade_type: UpgradeType) -> PolicyResult:
        logger.warning(f"BLOCKED: {reason}")
        return PolicyResult(
            decision=PolicyDecision.BLOCKED,
            reason=reason,
            confidence=confidence,
            breaking_changes_detected=breaking_changes,
            sensitive_paths_touched=sensitive_touched,
            files_touched=files_touched,
            upgrade_type=upgrade_type,
            auto_merge_eligible=False,
            evidence_summary=f"BLOCKED: {reason}",
        )

    @staticmethod
    def _classify_upgrade(current: str, target: Optional[str]) -> UpgradeType:
        """Classify upgrade as patch, minor, or major based on semver."""
        if not target or not current or current == "unknown":
            return UpgradeType.UNKNOWN

        try:
            curr_parts = [int(x) for x in current.split(".")[:3]]
            tgt_parts = [int(x) for x in target.split(".")[:3]]

            # Pad to length 3
            while len(curr_parts) < 3:
                curr_parts.append(0)
            while len(tgt_parts) < 3:
                tgt_parts.append(0)

            if tgt_parts[0] > curr_parts[0]:
                return UpgradeType.MAJOR
            elif tgt_parts[1] > curr_parts[1]:
                return UpgradeType.MINOR
            else:
                return UpgradeType.PATCH
        except (ValueError, IndexError):
            return UpgradeType.UNKNOWN
