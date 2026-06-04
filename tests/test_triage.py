"""Tests for src/orchestrator/triage.py — scoring, reachability, and policy routing."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from src.orchestrator.triage import TriageEngine, TriageDecision
from src.scanner.models import Severity, Vulnerability, VulnerabilityType


class TestTriageEngine:
    def setup_method(self):
        self.engine = TriageEngine(repo_path="/nonexistent")

    def test_triage_returns_sorted_decisions(self, sample_vuln, critical_vuln):
        decisions = self.engine.triage([sample_vuln, critical_vuln])
        assert len(decisions) == 2
        assert decisions[0].priority_score >= decisions[1].priority_score

    def test_triage_empty_list(self):
        decisions = self.engine.triage([])
        assert decisions == []

    def test_critical_has_highest_score(self, critical_vuln, sample_vuln, low_vuln):
        decisions = self.engine.triage([low_vuln, sample_vuln, critical_vuln])
        assert decisions[0].vulnerability.severity == Severity.CRITICAL

    def test_should_remediate_high_severity(self, sample_vuln):
        decisions = self.engine.triage([sample_vuln])
        assert decisions[0].should_remediate is True

    def test_should_not_remediate_low_severity(self, low_vuln):
        decisions = self.engine.triage([low_vuln])
        assert decisions[0].should_remediate is False

    def test_fix_available_boosts_score(self):
        with_fix = Vulnerability(
            id="a", title="t", description="d",
            severity=Severity.HIGH,
            vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
            package_name="pkg", current_version="1.0",
            fixed_version="2.0",
            discovered_at=datetime(2024, 1, 1),
        )
        without_fix = Vulnerability(
            id="b", title="t", description="d",
            severity=Severity.HIGH,
            vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
            package_name="pkg2", current_version="1.0",
            fixed_version=None,
            discovered_at=datetime(2024, 1, 1),
        )
        decisions = self.engine.triage([with_fix, without_fix])
        scores = {d.vulnerability.id: d.priority_score for d in decisions}
        assert scores["a"] > scores["b"]

    def test_complexity_simple_for_dep_with_fix(self, sample_vuln):
        decisions = self.engine.triage([sample_vuln])
        assert decisions[0].estimated_complexity == "simple"

    def test_complexity_complex_for_sast(self, sast_vuln):
        decisions = self.engine.triage([sast_vuln])
        assert decisions[0].estimated_complexity == "complex"

    def test_complexity_moderate_for_container(self, container_vuln):
        decisions = self.engine.triage([container_vuln])
        assert decisions[0].estimated_complexity == "moderate"

    def test_decision_has_reason_string(self, sample_vuln):
        decisions = self.engine.triage([sample_vuln])
        assert "Severity=high" in decisions[0].reason
        assert "Fix=yes" in decisions[0].reason


class TestTriageReachability:
    def test_reachability_none_when_repo_not_found(self, sample_vuln):
        engine = TriageEngine(repo_path="/nonexistent/path")
        decisions = engine.triage([sample_vuln])
        assert decisions[0].reachable is None

    def test_reachability_none_for_non_dependency(self, sast_vuln):
        engine = TriageEngine(repo_path="/nonexistent")
        decisions = engine.triage([sast_vuln])
        assert decisions[0].reachable is None

    def test_reachability_true_when_import_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = os.path.join(tmpdir, "app.py")
            with open(py_file, "w") as f:
                f.write("import requests\nrequests.get('http://example.com')\n")

            engine = TriageEngine(repo_path=tmpdir)
            vuln = Vulnerability(
                id="x", title="t", description="d",
                severity=Severity.HIGH,
                vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
                package_name="requests", current_version="2.0",
                fixed_version="2.1",
                discovered_at=datetime(2024, 1, 1),
            )
            decisions = engine.triage([vuln])
            assert decisions[0].reachable is True

    def test_reachability_false_when_import_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = os.path.join(tmpdir, "app.py")
            with open(py_file, "w") as f:
                f.write("import os\nprint('hello')\n")

            engine = TriageEngine(repo_path=tmpdir)
            vuln = Vulnerability(
                id="x", title="t", description="d",
                severity=Severity.HIGH,
                vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
                package_name="nonexistent_pkg", current_version="1.0",
                fixed_version="2.0",
                discovered_at=datetime(2024, 1, 1),
            )
            decisions = engine.triage([vuln])
            assert decisions[0].reachable is False

    def test_unreachable_gets_deprioritized(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = os.path.join(tmpdir, "app.py")
            with open(py_file, "w") as f:
                f.write("import flask\n")

            engine = TriageEngine(repo_path=tmpdir)

            reachable_vuln = Vulnerability(
                id="r", title="t", description="d",
                severity=Severity.HIGH,
                vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
                package_name="flask", current_version="2.0", fixed_version="3.0",
                discovered_at=datetime(2024, 1, 1),
            )
            unreachable_vuln = Vulnerability(
                id="u", title="t", description="d",
                severity=Severity.HIGH,
                vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
                package_name="nonexistent_pkg", current_version="1.0", fixed_version="2.0",
                discovered_at=datetime(2024, 1, 1),
            )
            decisions = engine.triage([reachable_vuln, unreachable_vuln])
            scores = {d.vulnerability.id: d.priority_score for d in decisions}
            assert scores["r"] > scores["u"]


class TestPredictPolicyRoute:
    def setup_method(self):
        self.engine = TriageEngine(repo_path="/nonexistent")

    def test_sast_always_human_review(self, sast_vuln):
        decisions = self.engine.triage([sast_vuln])
        assert decisions[0].predicted_route == "human_review"

    def test_container_always_human_review(self, container_vuln):
        decisions = self.engine.triage([container_vuln])
        assert decisions[0].predicted_route == "human_review"

    def test_simple_dep_with_fix_auto_merge(self, sample_vuln):
        decisions = self.engine.triage([sample_vuln])
        assert decisions[0].predicted_route == "auto_merge"

    def test_major_version_upgrade_human_review(self, critical_vuln):
        # flask 2.0.0 -> 3.0.0 is a major upgrade
        decisions = self.engine.triage([critical_vuln])
        assert decisions[0].predicted_route == "human_review"

    def test_dep_without_fix_defaults_to_human(self):
        vuln = Vulnerability(
            id="x", title="t", description="d",
            severity=Severity.HIGH,
            vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
            package_name="pkg", current_version="1.0",
            fixed_version=None,
            discovered_at=datetime(2024, 1, 1),
        )
        engine = TriageEngine(repo_path="/nonexistent")
        decisions = engine.triage([vuln])
        assert decisions[0].predicted_route == "human_review"
