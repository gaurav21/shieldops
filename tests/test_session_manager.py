"""Tests for src/orchestrator/session_manager.py — RemediationTask and SessionManager.get_stats."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from src.orchestrator.session_manager import RemediationTask, SessionManager, STRUCTURED_OUTPUT_SCHEMA
from src.orchestrator.triage import TriageDecision
from src.orchestrator.policy import PolicyDecision, PolicyResult, UpgradeType
from src.scanner.models import Severity, Vulnerability, VulnerabilityType, RemediationStatus


def _make_decision(status=RemediationStatus.PENDING, **vuln_kwargs) -> TriageDecision:
    defaults = dict(
        id="v1", title="test", description="d",
        severity=Severity.HIGH,
        vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
        package_name="requests", current_version="2.28.0",
        fixed_version="2.28.1",
        discovered_at=datetime(2024, 1, 1),
        status=status,
    )
    defaults.update(vuln_kwargs)
    vuln = Vulnerability(**defaults)
    return TriageDecision(
        vulnerability=vuln,
        priority_score=75.0,
        should_remediate=True,
        reason="test",
        estimated_complexity="simple",
        reachable=True,
        predicted_route="auto_merge",
    )


class TestRemediationTask:
    def test_vuln_property(self):
        decision = _make_decision()
        task = RemediationTask(decision=decision)
        assert task.vuln is decision.vulnerability

    def test_duration_seconds(self):
        decision = _make_decision()
        task = RemediationTask(
            decision=decision,
            started_at=datetime(2024, 1, 1, 0, 0, 0),
            completed_at=datetime(2024, 1, 1, 0, 10, 0),
        )
        assert task.duration_seconds == 600.0

    def test_duration_seconds_none_when_incomplete(self):
        decision = _make_decision()
        task = RemediationTask(decision=decision, started_at=datetime.utcnow())
        assert task.duration_seconds is None

    @pytest.mark.parametrize("status, expected", [
        (RemediationStatus.PR_CREATED, True),
        (RemediationStatus.PR_MERGED, True),
        (RemediationStatus.AUTO_MERGE_READY, True),
        (RemediationStatus.HUMAN_REVIEW, True),
        (RemediationStatus.BLOCKED, True),
        (RemediationStatus.FAILED, True),
        (RemediationStatus.SKIPPED, True),
        (RemediationStatus.PENDING, False),
        (RemediationStatus.IN_PROGRESS, False),
        (RemediationStatus.SCANNING, False),
        (RemediationStatus.TRIAGED, False),
    ])
    def test_is_complete(self, status, expected):
        decision = _make_decision(status=status)
        task = RemediationTask(decision=decision)
        assert task.is_complete is expected

    def test_default_interventions(self):
        task = RemediationTask(decision=_make_decision())
        assert task.interventions == 0


class TestStructuredOutputSchema:
    def test_schema_has_required_fields(self):
        props = STRUCTURED_OUTPUT_SCHEMA["properties"]
        expected_fields = {
            "status", "pr_url", "changes_summary", "tests_passed",
            "breaking_changes_detected", "breaking_changes_notes",
            "reachability_assessment", "confidence", "files_touched", "notes",
        }
        assert set(props.keys()) == expected_fields

    def test_schema_types(self):
        props = STRUCTURED_OUTPUT_SCHEMA["properties"]
        assert props["status"]["type"] == "string"
        assert props["tests_passed"]["type"] == "boolean"
        assert props["confidence"]["type"] == "number"
        assert props["files_touched"]["type"] == "array"


class TestSessionManagerGetStats:
    def _make_manager_with_tasks(self, tasks):
        """Create a SessionManager mock with completed tasks injected."""
        from unittest.mock import MagicMock
        manager = SessionManager.__new__(SessionManager)
        manager.active_tasks = {}
        manager.completed_tasks = tasks
        return manager

    def test_empty_stats(self):
        manager = self._make_manager_with_tasks([])
        stats = manager.get_stats()
        assert stats["completed"] == 0
        assert stats["succeeded"] == 0
        assert stats["failed"] == 0
        assert stats["success_rate"] == 0
        assert stats["avg_duration_seconds"] == 0
        assert stats["prs_created"] == 0

    def test_stats_with_successful_tasks(self):
        decision = _make_decision(status=RemediationStatus.PR_CREATED)
        task = RemediationTask(
            decision=decision,
            started_at=datetime(2024, 1, 1, 0, 0, 0),
            completed_at=datetime(2024, 1, 1, 0, 10, 0),
            policy_result=PolicyResult(
                decision=PolicyDecision.AUTO_MERGE_READY,
                reason="ok", confidence=0.95,
                breaking_changes_detected=False,
                sensitive_paths_touched=[],
                files_touched=["f.txt"],
                upgrade_type=UpgradeType.PATCH,
                auto_merge_eligible=True,
                evidence_summary="ok",
            ),
        )
        manager = self._make_manager_with_tasks([task])
        stats = manager.get_stats()

        assert stats["completed"] == 1
        assert stats["succeeded"] == 1
        assert stats["failed"] == 0
        assert stats["success_rate"] == 100.0
        assert stats["auto_merge_ready"] == 1
        assert stats["avg_confidence"] == 0.95

    def test_stats_with_failed_task(self):
        decision = _make_decision(status=RemediationStatus.FAILED)
        task = RemediationTask(decision=decision)
        manager = self._make_manager_with_tasks([task])
        stats = manager.get_stats()

        assert stats["failed"] == 1
        assert stats["succeeded"] == 0

    def test_breaking_changes_handled_metric(self):
        decision = _make_decision(status=RemediationStatus.AUTO_MERGE_READY)
        task = RemediationTask(
            decision=decision,
            started_at=datetime(2024, 1, 1),
            completed_at=datetime(2024, 1, 1, 0, 5),
            policy_result=PolicyResult(
                decision=PolicyDecision.AUTO_MERGE_READY,
                reason="ok", confidence=0.9,
                breaking_changes_detected=True,
                sensitive_paths_touched=[],
                files_touched=[],
                upgrade_type=UpgradeType.MINOR,
                auto_merge_eligible=True,
                evidence_summary="ok",
            ),
        )
        manager = self._make_manager_with_tasks([task])
        stats = manager.get_stats()
        assert stats["breaking_changes_handled"] == 1

    def test_intervention_rate(self):
        decision = _make_decision(status=RemediationStatus.PR_CREATED)
        task = RemediationTask(decision=decision, interventions=2)
        manager = self._make_manager_with_tasks([task])
        stats = manager.get_stats()
        assert stats["intervention_rate"] == 100.0
        assert stats["total_interventions"] == 2
