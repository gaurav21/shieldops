"""Tests for src/orchestrator/policy.py — PolicyEngine trust boundary decisions."""

from __future__ import annotations

from datetime import datetime

import pytest

from src.orchestrator.policy import (
    PolicyEngine,
    PolicyDecision,
    PolicyResult,
    UpgradeType,
    SENSITIVE_PATHS,
)
from src.scanner.models import Severity, Vulnerability, VulnerabilityType


def _make_vuln(**kwargs) -> Vulnerability:
    defaults = dict(
        id="v1", title="test", description="d",
        severity=Severity.HIGH,
        vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
        package_name="requests", current_version="2.28.0",
        fixed_version="2.28.1",
        discovered_at=datetime(2024, 1, 1),
    )
    defaults.update(kwargs)
    return Vulnerability(**defaults)


def _make_output(**kwargs) -> dict:
    defaults = {
        "status": "success",
        "tests_passed": True,
        "breaking_changes_detected": False,
        "confidence": 0.95,
        "files_touched": ["requirements.txt"],
        "changes_summary": "Bumped requests",
        "reachability_assessment": "reachable",
        "notes": "",
    }
    defaults.update(kwargs)
    return defaults


class TestPolicyEngineAutoMerge:
    def test_simple_patch_upgrade_auto_merges(self):
        engine = PolicyEngine()
        vuln = _make_vuln(current_version="2.28.0", fixed_version="2.28.1")
        output = _make_output()
        result = engine.evaluate(vuln, output, "stopped")
        assert result.decision == PolicyDecision.AUTO_MERGE_READY
        assert result.auto_merge_eligible is True
        assert result.upgrade_type == UpgradeType.PATCH

    def test_minor_upgrade_auto_merges_if_high_confidence(self):
        engine = PolicyEngine()
        vuln = _make_vuln(current_version="2.28.0", fixed_version="2.29.0")
        output = _make_output(confidence=0.95)
        result = engine.evaluate(vuln, output, "stopped")
        assert result.decision == PolicyDecision.AUTO_MERGE_READY

    def test_auto_merge_label(self):
        engine = PolicyEngine()
        vuln = _make_vuln()
        output = _make_output()
        result = engine.evaluate(vuln, output, "stopped")
        assert result.label == "auto-merge-ready"


class TestPolicyEngineBlocked:
    def test_blocked_on_error_status(self):
        engine = PolicyEngine()
        vuln = _make_vuln()
        result = engine.evaluate(vuln, _make_output(), "error")
        assert result.decision == PolicyDecision.BLOCKED

    def test_blocked_on_timed_out(self):
        engine = PolicyEngine()
        vuln = _make_vuln()
        result = engine.evaluate(vuln, _make_output(), "timed_out")
        assert result.decision == PolicyDecision.BLOCKED

    def test_blocked_when_tests_fail(self):
        engine = PolicyEngine()
        vuln = _make_vuln()
        output = _make_output(tests_passed=False)
        result = engine.evaluate(vuln, output, "stopped")
        assert result.decision == PolicyDecision.BLOCKED

    def test_blocked_on_very_low_confidence(self):
        engine = PolicyEngine()
        vuln = _make_vuln()
        output = _make_output(confidence=0.3)
        result = engine.evaluate(vuln, output, "stopped")
        assert result.decision == PolicyDecision.BLOCKED

    def test_blocked_on_devin_reported_failure(self):
        engine = PolicyEngine()
        vuln = _make_vuln()
        output = _make_output(status="failed")
        result = engine.evaluate(vuln, output, "stopped")
        assert result.decision == PolicyDecision.BLOCKED

    def test_blocked_label(self):
        engine = PolicyEngine()
        vuln = _make_vuln()
        result = engine.evaluate(vuln, _make_output(), "error")
        assert result.label == "blocked"

    def test_blocked_when_no_output(self):
        engine = PolicyEngine()
        vuln = _make_vuln()
        result = engine.evaluate(vuln, None, "error")
        assert result.decision == PolicyDecision.BLOCKED


class TestPolicyEngineHumanReview:
    def test_major_upgrade_requires_review(self):
        engine = PolicyEngine()
        vuln = _make_vuln(current_version="2.0.0", fixed_version="3.0.0")
        output = _make_output()
        result = engine.evaluate(vuln, output, "stopped")
        assert result.decision == PolicyDecision.HUMAN_REVIEW
        assert "major version upgrade" in result.reason.lower()

    def test_breaking_changes_require_review(self):
        engine = PolicyEngine()
        vuln = _make_vuln()
        output = _make_output(breaking_changes_detected=True)
        result = engine.evaluate(vuln, output, "stopped")
        assert result.decision == PolicyDecision.HUMAN_REVIEW

    def test_sast_fix_requires_review(self):
        engine = PolicyEngine()
        vuln = _make_vuln(vuln_type=VulnerabilityType.SAST)
        output = _make_output()
        result = engine.evaluate(vuln, output, "stopped")
        assert result.decision == PolicyDecision.HUMAN_REVIEW

    def test_code_quality_fix_requires_review(self):
        engine = PolicyEngine()
        vuln = _make_vuln(vuln_type=VulnerabilityType.CODE_QUALITY)
        output = _make_output()
        result = engine.evaluate(vuln, output, "stopped")
        assert result.decision == PolicyDecision.HUMAN_REVIEW

    def test_sensitive_paths_require_review(self):
        engine = PolicyEngine()
        vuln = _make_vuln()
        output = _make_output(
            files_touched=["superset/security/manager.py", "requirements.txt"]
        )
        result = engine.evaluate(vuln, output, "stopped")
        assert result.decision == PolicyDecision.HUMAN_REVIEW
        assert len(result.sensitive_paths_touched) > 0

    def test_low_confidence_requires_review(self):
        engine = PolicyEngine()
        vuln = _make_vuln()
        output = _make_output(confidence=0.65)
        result = engine.evaluate(vuln, output, "stopped")
        assert result.decision == PolicyDecision.HUMAN_REVIEW
        assert "confidence below threshold" in result.reason.lower()

    def test_container_fix_requires_review(self):
        engine = PolicyEngine()
        vuln = _make_vuln(vuln_type=VulnerabilityType.CONTAINER)
        output = _make_output()
        result = engine.evaluate(vuln, output, "stopped")
        assert result.decision == PolicyDecision.HUMAN_REVIEW

    def test_human_review_label(self):
        engine = PolicyEngine()
        vuln = _make_vuln(current_version="2.0.0", fixed_version="3.0.0")
        result = engine.evaluate(vuln, _make_output(), "stopped")
        assert result.label == "needs-human"

    def test_custom_confidence_threshold(self):
        engine = PolicyEngine(confidence_threshold=0.9)
        vuln = _make_vuln()
        output = _make_output(confidence=0.85)
        result = engine.evaluate(vuln, output, "stopped")
        assert result.decision == PolicyDecision.HUMAN_REVIEW


class TestClassifyUpgrade:
    @pytest.mark.parametrize(
        "current, target, expected",
        [
            ("1.0.0", "1.0.1", UpgradeType.PATCH),
            ("1.0.0", "1.1.0", UpgradeType.MINOR),
            ("1.0.0", "2.0.0", UpgradeType.MAJOR),
            ("1.0", "2.0", UpgradeType.MAJOR),
            ("1", "2", UpgradeType.MAJOR),
            (None, "2.0.0", UpgradeType.UNKNOWN),
            ("1.0.0", None, UpgradeType.UNKNOWN),
            ("unknown", "2.0.0", UpgradeType.UNKNOWN),
            ("abc", "def", UpgradeType.UNKNOWN),
        ],
    )
    def test_classify_upgrade(self, current, target, expected):
        result = PolicyEngine._classify_upgrade(current, target)
        assert result == expected


class TestPolicyResult:
    def test_label_property(self):
        for decision, expected_label in [
            (PolicyDecision.AUTO_MERGE_READY, "auto-merge-ready"),
            (PolicyDecision.HUMAN_REVIEW, "needs-human"),
            (PolicyDecision.BLOCKED, "blocked"),
        ]:
            result = PolicyResult(
                decision=decision,
                reason="test",
                confidence=0.9,
                breaking_changes_detected=False,
                sensitive_paths_touched=[],
                files_touched=[],
                upgrade_type=UpgradeType.PATCH,
                auto_merge_eligible=True,
                evidence_summary="test",
            )
            assert result.label == expected_label
