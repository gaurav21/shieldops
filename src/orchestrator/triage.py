from __future__ import annotations

"""Triage engine — scores, prioritizes, checks reachability, and pre-routes policy decisions."""

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..scanner.models import Severity, Vulnerability, VulnerabilityType

logger = logging.getLogger(__name__)


@dataclass
class TriageDecision:
    vulnerability: Vulnerability
    priority_score: float  # 0-100
    should_remediate: bool
    reason: str
    estimated_complexity: str  # simple, moderate, complex
    reachable: Optional[bool] = None  # is the vuln code actually used?
    predicted_route: str = "unknown"  # auto_merge / human_review / blocked (pre-policy prediction)


class TriageEngine:
    """Scores and prioritizes vulnerabilities for Devin remediation.
    
    v2 additions:
    - Reachability heuristic: grep for imports to deprioritize unreachable CVEs
    - Policy pre-routing: predict whether the result will be auto/human/blocked
      so the dashboard can show projected reviewer load before sessions run
    """

    SEVERITY_WEIGHT = 0.40
    FIX_AVAILABLE_WEIGHT = 0.25
    TYPE_WEIGHT = 0.20
    AGE_WEIGHT = 0.15

    SIMPLE_TYPES = {VulnerabilityType.PYTHON_DEPENDENCY, VulnerabilityType.NPM_DEPENDENCY}
    MODERATE_TYPES = {VulnerabilityType.CONTAINER}
    COMPLEX_TYPES = {VulnerabilityType.SAST, VulnerabilityType.CODE_QUALITY}

    # Sensitive paths that always force human review
    SENSITIVE_PATHS = {"superset/sql_lab.py", "superset/views/", "superset/security/",
                       "superset/connectors/", "superset/utils/encrypt.py"}

    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = repo_path or os.getenv("REPO_PATH", "/tmp/superset")

    def triage(self, vulnerabilities: list[Vulnerability]) -> list[TriageDecision]:
        """Score, check reachability, predict policy route, and sort by priority."""
        decisions = [self._evaluate(v) for v in vulnerabilities]
        decisions.sort(key=lambda d: d.priority_score, reverse=True)

        reachable_count = sum(1 for d in decisions if d.reachable is True)
        unreachable_count = sum(1 for d in decisions if d.reachable is False)
        actionable_count = sum(1 for d in decisions if d.should_remediate)

        logger.info(
            f"Triage complete: {len(decisions)} vulns — "
            f"{actionable_count} to remediate, "
            f"{reachable_count} reachable, {unreachable_count} deprioritized (unreachable)"
        )
        return decisions

    def _evaluate(self, vuln: Vulnerability) -> TriageDecision:
        """Evaluate a single vulnerability with reachability and policy prediction."""
        # Severity score
        severity_score = vuln.severity.priority_score

        # Fix available bonus
        fix_score = 100 if vuln.fixed_version else 30

        # Type score
        type_scores = {
            VulnerabilityType.PYTHON_DEPENDENCY: 90,
            VulnerabilityType.NPM_DEPENDENCY: 85,
            VulnerabilityType.CONTAINER: 60,
            VulnerabilityType.CODE_QUALITY: 40,
            VulnerabilityType.SAST: 50,
        }
        type_score = type_scores.get(vuln.vuln_type, 50)

        # Age score
        age_hours = (datetime.utcnow() - vuln.discovered_at).total_seconds() / 3600
        age_score = min(100, age_hours * 2)

        # Reachability check (cheap heuristic: grep for the import)
        reachable = self._check_reachability(vuln)
        vuln.reachable = reachable

        # Reachability penalty: unreachable vulns get deprioritized heavily
        reachability_multiplier = 1.0 if reachable is not False else 0.3

        # Weighted total
        priority = (
            severity_score * self.SEVERITY_WEIGHT
            + fix_score * self.FIX_AVAILABLE_WEIGHT
            + type_score * self.TYPE_WEIGHT
            + age_score * self.AGE_WEIGHT
        ) * reachability_multiplier

        # Complexity
        if vuln.vuln_type in self.SIMPLE_TYPES and vuln.fixed_version:
            complexity = "simple"
        elif vuln.vuln_type in self.COMPLEX_TYPES:
            complexity = "complex"
        else:
            complexity = "moderate"

        # Policy pre-routing prediction
        predicted_route = self._predict_policy_route(vuln, complexity)

        # Should remediate?
        should_remediate = (
            priority >= 30
            and vuln.severity in (Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM)
            and reachable is not False  # Skip confirmed-unreachable
        )

        reason = (
            f"Severity={vuln.severity.value}({severity_score:.0f}), "
            f"Fix={'yes' if vuln.fixed_version else 'no'}({fix_score:.0f}), "
            f"Type={vuln.vuln_type.value}({type_score:.0f}), "
            f"Reachable={'yes' if reachable else 'no' if reachable is False else 'unknown'}, "
            f"Complexity={complexity}, "
            f"Predicted={predicted_route}"
        )

        return TriageDecision(
            vulnerability=vuln,
            priority_score=round(priority, 1),
            should_remediate=should_remediate,
            reason=reason,
            estimated_complexity=complexity,
            reachable=reachable,
            predicted_route=predicted_route,
        )

    def _check_reachability(self, vuln: Vulnerability) -> Optional[bool]:
        """Cheap reachability heuristic: grep for the package import in the codebase.
        
        Returns True if found, False if definitely not used, None if can't determine.
        This lets us say "we deprioritized 30 CVEs that aren't reachable" — a line
        every security-aware VP loves.
        """
        if vuln.vuln_type not in (VulnerabilityType.PYTHON_DEPENDENCY, VulnerabilityType.NPM_DEPENDENCY):
            return None  # Can't easily check for non-dependency types

        if not os.path.isdir(self.repo_path):
            return None  # Repo not cloned yet

        import subprocess

        pkg = vuln.package_name.replace("-", "_").replace("-", "_")

        try:
            if vuln.vuln_type == VulnerabilityType.PYTHON_DEPENDENCY:
                # Search for `import pkg` or `from pkg` in Python files
                result = subprocess.run(
                    ["grep", "-r", "-l", "--include=*.py",
                     f"\\(import {pkg}\\|from {pkg}\\)", self.repo_path],
                    capture_output=True, text=True, timeout=10,
                )
                return len(result.stdout.strip()) > 0

            elif vuln.vuln_type == VulnerabilityType.NPM_DEPENDENCY:
                # Search for require('pkg') or import ... from 'pkg'
                frontend = os.path.join(self.repo_path, "superset-frontend")
                search_dir = frontend if os.path.isdir(frontend) else self.repo_path
                result = subprocess.run(
                    ["grep", "-r", "-l", "--include=*.ts", "--include=*.tsx",
                     "--include=*.js", "--include=*.jsx",
                     vuln.package_name, search_dir],
                    capture_output=True, text=True, timeout=10,
                )
                return len(result.stdout.strip()) > 0

        except subprocess.TimeoutExpired:
            logger.warning(f"Reachability check timed out for {vuln.package_name}")
            return None
        except FileNotFoundError:
            logger.warning("grep not available for reachability check")
            return None

        return None

    def _predict_policy_route(self, vuln: Vulnerability, complexity: str) -> str:
        """Predict the likely policy routing before Devin runs.
        
        This lets the dashboard show projected reviewer load upfront.
        """
        # SAST / code quality → always human review
        if vuln.vuln_type in (VulnerabilityType.SAST, VulnerabilityType.CODE_QUALITY):
            return "human_review"

        # Container fixes → usually human review
        if vuln.vuln_type == VulnerabilityType.CONTAINER:
            return "human_review"

        # Major version upgrade → human review
        if vuln.fixed_version and vuln.current_version:
            try:
                curr_major = int(vuln.current_version.split(".")[0])
                fix_major = int(vuln.fixed_version.split(".")[0])
                if fix_major > curr_major:
                    return "human_review"
            except (ValueError, IndexError):
                pass

        # Simple dependency with fix → likely auto-merge
        if vuln.vuln_type in self.SIMPLE_TYPES and vuln.fixed_version and complexity == "simple":
            return "auto_merge"

        return "human_review"  # Default conservative
