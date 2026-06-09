"""Tests for src/reporting/evidence_bundle.py — PR descriptions and issue comments."""

from __future__ import annotations

from datetime import datetime

import pytest

from src.reporting.evidence_bundle import EvidenceBundle
from src.orchestrator.policy import PolicyDecision, PolicyResult, UpgradeType
from src.scanner.models import Severity, Vulnerability, VulnerabilityType


def _make_vuln(**kwargs) -> Vulnerability:
    defaults = dict(
        id="v1", title="Upgrade requests — CVE-2024-001",
        description="HTTP smuggling",
        severity=Severity.HIGH,
        vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
        package_name="requests", current_version="2.28.0",
        fixed_version="2.28.1",
        cve_id="CVE-2024-001",
        advisory_url="https://nvd.nist.gov/vuln/CVE-2024-001",
        discovered_at=datetime(2024, 1, 1),
    )
    defaults.update(kwargs)
    return Vulnerability(**defaults)


def _make_policy(decision: PolicyDecision, **kwargs) -> PolicyResult:
    defaults = dict(
        decision=decision,
        reason="test reason",
        confidence=0.95,
        breaking_changes_detected=False,
        sensitive_paths_touched=[],
        files_touched=["requirements.txt"],
        upgrade_type=UpgradeType.PATCH,
        auto_merge_eligible=(decision == PolicyDecision.AUTO_MERGE_READY),
        evidence_summary="test evidence",
    )
    defaults.update(kwargs)
    return PolicyResult(**defaults)


class TestBuildPrDescription:
    def setup_method(self):
        self.bundle = EvidenceBundle()

    def test_auto_merge_pr_description(self):
        vuln = _make_vuln()
        policy = _make_policy(PolicyDecision.AUTO_MERGE_READY)
        output = {"tests_passed": True, "changes_summary": "Bumped requests",
                  "reachability_assessment": "reachable", "notes": ""}
        desc = self.bundle.build_pr_description(vuln, policy, output)

        assert "Auto Merge Ready" in desc
        assert "requests" in desc
        assert "CVE-2024-001" in desc
        assert "2.28.0" in desc
        assert "2.28.1" in desc
        assert "Reviewer Action" in desc
        assert "auto-merge criteria" in desc

    def test_human_review_pr_description(self):
        vuln = _make_vuln(current_version="2.0.0", fixed_version="3.0.0")
        policy = _make_policy(
            PolicyDecision.HUMAN_REVIEW,
            reason="major version upgrade",
            upgrade_type=UpgradeType.MAJOR,
        )
        output = {"tests_passed": True, "changes_summary": "Major upgrade"}
        desc = self.bundle.build_pr_description(vuln, policy, output)

        assert "Human Review" in desc
        assert "Reviewer Action Required" in desc

    def test_blocked_pr_description(self):
        vuln = _make_vuln()
        policy = _make_policy(
            PolicyDecision.BLOCKED,
            reason="Tests did not pass",
        )
        output = {"tests_passed": False}
        desc = self.bundle.build_pr_description(vuln, policy, output)

        assert "Blocked" in desc
        assert "Manual Intervention Required" in desc

    def test_breaking_changes_section(self):
        vuln = _make_vuln()
        policy = _make_policy(
            PolicyDecision.HUMAN_REVIEW,
            breaking_changes_detected=True,
            reason="breaking changes detected",
        )
        output = {
            "tests_passed": True,
            "breaking_changes_notes": "API changed from v1 to v2",
            "changes_summary": "Fixed breaking changes",
        }
        desc = self.bundle.build_pr_description(vuln, policy, output)

        assert "Breaking Changes Detected" in desc
        assert "API changed from v1 to v2" in desc
        assert "Dependabot" in desc

    def test_sensitive_paths_in_blast_radius(self):
        vuln = _make_vuln()
        policy = _make_policy(
            PolicyDecision.HUMAN_REVIEW,
            sensitive_paths_touched=["superset/security/manager.py"],
            files_touched=["superset/security/manager.py", "requirements.txt"],
            reason="sensitive paths",
        )
        desc = self.bundle.build_pr_description(vuln, policy)

        assert "sensitive" in desc.lower()
        assert "superset/security/manager.py" in desc

    def test_reachability_section(self):
        vuln = _make_vuln()
        policy = _make_policy(PolicyDecision.AUTO_MERGE_READY)
        output = {"reachability_assessment": "reachable — used in 5 modules"}
        desc = self.bundle.build_pr_description(vuln, policy, output)

        assert "Reachability Assessment" in desc
        assert "reachable" in desc

    def test_no_output_defaults(self):
        vuln = _make_vuln()
        policy = _make_policy(PolicyDecision.AUTO_MERGE_READY)
        desc = self.bundle.build_pr_description(vuln, policy, None)
        assert "No summary available" in desc

    def test_footer_present(self):
        vuln = _make_vuln()
        policy = _make_policy(PolicyDecision.AUTO_MERGE_READY)
        desc = self.bundle.build_pr_description(vuln, policy)
        assert "ShieldOps" in desc
        assert "Devin AI" in desc


class TestBuildIssueComment:
    def setup_method(self):
        self.bundle = EvidenceBundle()

    def test_auto_merge_comment(self):
        vuln = _make_vuln()
        policy = _make_policy(PolicyDecision.AUTO_MERGE_READY)
        comment = self.bundle.build_issue_comment(
            vuln, policy, {"tests_passed": True},
            pr_url="https://github.com/org/repo/pull/1",
            session_url="https://app.devin.ai/sessions/abc",
        )
        assert "auto-merge" in comment.lower()
        assert "https://github.com/org/repo/pull/1" in comment
        assert "Passed" in comment

    def test_human_review_comment(self):
        vuln = _make_vuln()
        policy = _make_policy(
            PolicyDecision.HUMAN_REVIEW,
            reason="breaking changes",
            breaking_changes_detected=True,
        )
        comment = self.bundle.build_issue_comment(vuln, policy)
        assert "human review" in comment.lower()
        assert "breaking changes" in comment.lower()

    def test_blocked_comment(self):
        vuln = _make_vuln()
        policy = _make_policy(PolicyDecision.BLOCKED, reason="Tests failed")
        comment = self.bundle.build_issue_comment(vuln, policy)
        assert "blocked" in comment.lower()
        assert "Tests failed" in comment

    def test_footer_in_comment(self):
        vuln = _make_vuln()
        policy = _make_policy(PolicyDecision.AUTO_MERGE_READY)
        comment = self.bundle.build_issue_comment(vuln, policy)
        assert "ShieldOps" in comment
