"""Shared fixtures for ShieldOps tests."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from src.config import Config, DevinConfig, GitHubConfig, DatadogConfig, ScannerConfig
from src.scanner.models import (
    Severity,
    Vulnerability,
    VulnerabilityType,
    RemediationStatus,
    ScanResult,
)
from src.orchestrator.triage import TriageDecision


@pytest.fixture
def sample_vuln() -> Vulnerability:
    return Vulnerability(
        id="vuln-001",
        title="Upgrade requests — CVE-2023-0001",
        description="HTTP request smuggling in requests",
        severity=Severity.HIGH,
        vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
        package_name="requests",
        current_version="2.28.0",
        fixed_version="2.31.0",
        cve_id="CVE-2023-0001",
        advisory_url="https://nvd.nist.gov/vuln/detail/CVE-2023-0001",
        scanner="pip-audit",
        discovered_at=datetime(2024, 1, 1, 0, 0, 0),
    )


@pytest.fixture
def critical_vuln() -> Vulnerability:
    return Vulnerability(
        id="vuln-002",
        title="RCE in flask",
        description="Remote code execution",
        severity=Severity.CRITICAL,
        vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
        package_name="flask",
        current_version="2.0.0",
        fixed_version="3.0.0",
        cve_id="CVE-2024-9999",
        scanner="pip-audit",
        discovered_at=datetime(2024, 1, 1, 0, 0, 0),
    )


@pytest.fixture
def npm_vuln() -> Vulnerability:
    return Vulnerability(
        id="vuln-003",
        title="XSS in lodash",
        description="Cross-site scripting via template injection",
        severity=Severity.MEDIUM,
        vuln_type=VulnerabilityType.NPM_DEPENDENCY,
        package_name="lodash",
        current_version="4.17.15",
        fixed_version="4.17.21",
        scanner="npm-audit",
        discovered_at=datetime(2024, 1, 1, 0, 0, 0),
    )


@pytest.fixture
def sast_vuln() -> Vulnerability:
    return Vulnerability(
        id="vuln-004",
        title="SQL injection in query builder",
        description="Unsanitized user input in SQL query",
        severity=Severity.HIGH,
        vuln_type=VulnerabilityType.SAST,
        package_name="sql-injection-rule",
        current_version="N/A",
        file_path="superset/sql_lab.py",
        line_number=42,
        scanner="semgrep",
        discovered_at=datetime(2024, 1, 1, 0, 0, 0),
    )


@pytest.fixture
def container_vuln() -> Vulnerability:
    return Vulnerability(
        id="vuln-005",
        title="Trivy: CVE-2024-1234 in openssl",
        description="Buffer overflow in OpenSSL",
        severity=Severity.CRITICAL,
        vuln_type=VulnerabilityType.CONTAINER,
        package_name="openssl",
        current_version="3.0.0",
        fixed_version="3.0.12",
        cve_id="CVE-2024-1234",
        scanner="trivy",
        discovered_at=datetime(2024, 1, 1, 0, 0, 0),
    )


@pytest.fixture
def low_vuln() -> Vulnerability:
    return Vulnerability(
        id="vuln-006",
        title="Info disclosure in urllib3",
        description="Minor information disclosure",
        severity=Severity.LOW,
        vuln_type=VulnerabilityType.PYTHON_DEPENDENCY,
        package_name="urllib3",
        current_version="1.26.0",
        fixed_version="1.26.18",
        scanner="pip-audit",
        discovered_at=datetime(2024, 1, 1, 0, 0, 0),
    )


@pytest.fixture
def sample_scan_result(sample_vuln, npm_vuln) -> ScanResult:
    return ScanResult(
        scan_id="scan-001",
        scanner="pip-audit",
        started_at=datetime(2024, 1, 1, 0, 0, 0),
        completed_at=datetime(2024, 1, 1, 0, 5, 0),
        vulnerabilities=[sample_vuln, npm_vuln],
    )


@pytest.fixture
def sample_triage_decision(sample_vuln) -> TriageDecision:
    return TriageDecision(
        vulnerability=sample_vuln,
        priority_score=75.0,
        should_remediate=True,
        reason="test reason",
        estimated_complexity="simple",
        reachable=True,
        predicted_route="auto_merge",
    )


@pytest.fixture
def default_config() -> Config:
    return Config()


@pytest.fixture
def github_config() -> GitHubConfig:
    return GitHubConfig(
        token="ghp_test_token",
        repo_owner="testowner",
        repo_name="testrepo",
        webhook_secret="test_secret",
    )
