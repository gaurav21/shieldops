"""Tests for database models."""

import pytest
import pytest_asyncio
from datetime import datetime

from src.db.models import (
    Organization, Repository, Vulnerability, RemediationSession, User, AuditLog,
    PlanType, VulnStatus, VulnSeverity, SessionStatus, UserRole
)


@pytest_asyncio.fixture
@pytest.mark.asyncio
async def test_models_data(test_session, test_org, test_repo, test_user):
    """Create test data for model tests."""
    # Create vulnerability
    vuln = Vulnerability(
        repo_id=test_repo.id,
        cve_id="CVE-2024-12345",
        package_name="test-package",
        current_version="1.0.0",
        fixed_version="1.1.0",
        severity=VulnSeverity.HIGH,
        vuln_type="python_dependency",
        title="Test Vulnerability",
        description="A test vulnerability for testing purposes.",
    )
    test_session.add(vuln)
    await test_session.flush()  # flush to get vuln.id assigned
    
    # Create remediation session
    session = RemediationSession(
        vuln_id=vuln.id,
        repo_id=test_repo.id,
        agent_type="devin",
        status=SessionStatus.COMPLETED,
        policy_decision="auto_merge_ready",
        policy_reason="Tests passed, no breaking changes",
        duration_seconds=300,
        acu_cost=2.5,
    )
    test_session.add(session)
    
    # Create audit log
    audit = AuditLog(
        org_id=test_org.id,
        repo_id=test_repo.id,
        event_type="vulnerability_detected",
        actor="system",
        details={"package": "test-package", "severity": "high"},
    )
    test_session.add(audit)
    
    await test_session.commit()
    
    return {
        "vuln": vuln,
        "session": session,
        "audit": audit,
    }


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_organization_model(test_org):
    """Test Organization model."""
    assert test_org.github_org_id == 12345
    assert test_org.name == "Test Organization"
    assert test_org.slug == "test-org"
    assert test_org.plan == PlanType.PRO
    assert test_org.installation_id == 67890


@pytest.mark.asyncio
async def test_repository_model(test_repo, test_org):
    """Test Repository model and relationships."""
    assert test_repo.github_repo_id == 11111
    assert test_repo.full_name == "test-org/test-repo"
    assert test_repo.default_branch == "main"
    assert test_repo.is_active is True
    assert test_repo.org_id == test_org.id
    
    # Test default scan_config
    assert "scan_types" in test_repo.scan_config
    assert "daily" in test_repo.scan_config.get("schedule", "")


@pytest.mark.asyncio
async def test_vulnerability_model(test_models_data):
    """Test Vulnerability model."""
    vuln = test_models_data["vuln"]
    
    assert vuln.cve_id == "CVE-2024-12345"
    assert vuln.package_name == "test-package"
    assert vuln.severity == VulnSeverity.HIGH
    assert vuln.status == VulnStatus.DETECTED  # default
    assert vuln.title == "Test Vulnerability"
    assert vuln.vuln_type == "python_dependency"


@pytest.mark.asyncio
async def test_remediation_session_model(test_models_data):
    """Test RemediationSession model."""
    session = test_models_data["session"]
    
    assert session.agent_type == "devin"
    assert session.status == SessionStatus.COMPLETED
    assert session.policy_decision == "auto_merge_ready"
    assert session.duration_seconds == 300
    assert session.acu_cost == 2.5


@pytest.mark.asyncio
async def test_user_model(test_user, test_org):
    """Test User model."""
    assert test_user.github_user_id == 22222
    assert test_user.login == "testuser"
    assert test_user.email == "test@example.com"
    assert test_user.role == UserRole.ADMIN
    assert test_user.org_id == test_org.id


@pytest.mark.asyncio
async def test_audit_log_model(test_models_data, test_org, test_repo):
    """Test AuditLog model."""
    audit = test_models_data["audit"]
    
    assert audit.org_id == test_org.id
    assert audit.repo_id == test_repo.id
    assert audit.event_type == "vulnerability_detected"
    assert audit.actor == "system"
    assert "package" in audit.details
    assert audit.details["severity"] == "high"


@pytest.mark.asyncio
async def test_model_relationships(test_session, test_models_data, test_org, test_repo):
    """Test model relationships."""
    # Test organization -> repositories relationship
    await test_session.refresh(test_org, ["repositories"])
    assert len(test_org.repositories) == 1
    assert test_org.repositories[0].id == test_repo.id
    
    # Test repository -> vulnerabilities relationship
    await test_session.refresh(test_repo, ["vulnerabilities"])
    assert len(test_repo.vulnerabilities) == 1
    assert test_repo.vulnerabilities[0].id == test_models_data["vuln"].id
    
    # Test vulnerability -> remediation_sessions relationship
    vuln = test_models_data["vuln"]
    await test_session.refresh(vuln, ["remediation_sessions"])
    assert len(vuln.remediation_sessions) == 1
    assert vuln.remediation_sessions[0].id == test_models_data["session"].id


@pytest.mark.asyncio
async def test_model_timestamps(test_session, test_org, test_repo, test_models_data):
    """Test automatic timestamps."""
    # Refresh to load server-generated defaults
    await test_session.refresh(test_org)
    await test_session.refresh(test_repo)
    
    # Organizations and repositories should have timestamps
    assert test_org.created_at is not None
    assert test_org.updated_at is not None
    assert test_repo.created_at is not None
    assert test_repo.updated_at is not None
    
    # Vulnerabilities should have first_detected_at
    vuln = test_models_data["vuln"]
    await test_session.refresh(vuln)
    assert vuln.first_detected_at is not None
    
    # Sessions should have created_at
    session = test_models_data["session"]
    await test_session.refresh(session)
    assert session.created_at is not None