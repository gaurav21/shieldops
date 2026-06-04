"""Tests for src/scanner/models.py — enums, data models, and properties."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from src.scanner.models import (
    Severity,
    VulnerabilityType,
    RemediationStatus,
    Vulnerability,
    ScanResult,
)


# ---------- Severity enum ----------

class TestSeverity:
    def test_values(self):
        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"
        assert Severity.UNKNOWN.value == "unknown"

    @pytest.mark.parametrize(
        "severity, expected_score",
        [
            (Severity.CRITICAL, 100),
            (Severity.HIGH, 75),
            (Severity.MEDIUM, 50),
            (Severity.LOW, 25),
            (Severity.UNKNOWN, 10),
        ],
    )
    def test_priority_score(self, severity, expected_score):
        assert severity.priority_score == expected_score

    def test_is_str_enum(self):
        assert isinstance(Severity.HIGH, str)
        assert Severity.HIGH == "high"


# ---------- VulnerabilityType enum ----------

class TestVulnerabilityType:
    def test_values(self):
        assert VulnerabilityType.PYTHON_DEPENDENCY.value == "python_dependency"
        assert VulnerabilityType.NPM_DEPENDENCY.value == "npm_dependency"
        assert VulnerabilityType.CONTAINER.value == "container"
        assert VulnerabilityType.CODE_QUALITY.value == "code_quality"
        assert VulnerabilityType.SAST.value == "sast"


# ---------- RemediationStatus enum ----------

class TestRemediationStatus:
    def test_all_statuses_exist(self):
        expected = {
            "pending", "scanning", "triaged", "in_progress",
            "pr_created", "pr_merged", "auto_merge_ready",
            "human_review", "blocked", "failed", "skipped",
        }
        actual = {s.value for s in RemediationStatus}
        assert actual == expected


# ---------- Vulnerability ----------

class TestVulnerability:
    def test_mttr_seconds_when_remediated(self, sample_vuln):
        sample_vuln.remediated_at = sample_vuln.discovered_at + timedelta(hours=2)
        assert sample_vuln.mttr_seconds == 7200.0

    def test_mttr_seconds_when_not_remediated(self, sample_vuln):
        assert sample_vuln.mttr_seconds is None

    def test_mttr_seconds_no_discovered_at(self):
        vuln = Vulnerability(
            id="x", title="x", description="x",
            severity=Severity.LOW,
            vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
            package_name="x", current_version="1.0",
        )
        vuln.remediated_at = datetime.utcnow()
        assert vuln.mttr_seconds is not None

    def test_to_github_issue_basic(self, sample_vuln):
        issue = sample_vuln.to_github_issue()
        assert "[HIGH]" in issue["title"]
        assert "requests" in issue["body"]
        assert "security" in issue["labels"]
        assert "devin-auto-fix" in issue["labels"]
        assert "high" in issue["labels"]
        assert "dependency" in issue["labels"]

    def test_to_github_issue_sast_no_dependency_label(self, sast_vuln):
        issue = sast_vuln.to_github_issue()
        assert "dependency" not in issue["labels"]
        assert "security" in issue["labels"]

    def test_to_github_issue_includes_file_path(self, sast_vuln):
        issue = sast_vuln.to_github_issue()
        assert "superset/sql_lab.py" in issue["body"]

    def test_to_github_issue_no_fixed_version(self, sample_vuln):
        sample_vuln.fixed_version = None
        issue = sample_vuln.to_github_issue()
        assert "N/A" in issue["body"]

    def test_to_github_issue_no_cve(self, sample_vuln):
        sample_vuln.cve_id = None
        issue = sample_vuln.to_github_issue()
        assert "N/A" in issue["body"]

    def test_default_status_is_pending(self, sample_vuln):
        assert sample_vuln.status == RemediationStatus.PENDING

    def test_default_fields_are_none(self, sample_vuln):
        assert sample_vuln.github_issue_number is None
        assert sample_vuln.devin_session_id is None
        assert sample_vuln.pr_number is None
        assert sample_vuln.reachable is None


# ---------- ScanResult ----------

class TestScanResult:
    def test_duration_seconds(self, sample_scan_result):
        assert sample_scan_result.duration_seconds == 300.0

    def test_duration_seconds_no_completed_at(self):
        sr = ScanResult(
            scan_id="test",
            scanner="pip-audit",
            started_at=datetime.utcnow(),
        )
        assert sr.duration_seconds is None

    def test_by_severity(self, sample_scan_result):
        counts = sample_scan_result.by_severity
        assert counts["high"] == 1
        assert counts["medium"] == 1

    def test_by_severity_empty(self):
        sr = ScanResult(
            scan_id="test", scanner="test",
            started_at=datetime.utcnow(),
        )
        assert sr.by_severity == {}

    def test_error_field(self):
        sr = ScanResult(
            scan_id="test", scanner="test",
            started_at=datetime.utcnow(),
            error="scan failed",
        )
        assert sr.error == "scan failed"
