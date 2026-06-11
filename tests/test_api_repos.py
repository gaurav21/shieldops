"""Tests for repository management API."""

import pytest
import pytest_asyncio
from unittest.mock import patch

from src.api.auth import AuthContext
from src.api.repos import router
from src.db.models import Repository, Vulnerability, VulnSeverity, VulnStatus


@pytest_asyncio.fixture
async def auth_context(test_user, test_org):
    """Create mock auth context."""
    return AuthContext(test_user)


@pytest_asyncio.fixture 
@pytest.mark.asyncio
async def test_vulnerabilities(test_session, test_repo):
    """Create test vulnerabilities."""
    vulns = []
    
    # High severity vulnerability
    vuln1 = Vulnerability(
        repo_id=test_repo.id,
        package_name="high-vuln",
        severity=VulnSeverity.HIGH,
        status=VulnStatus.DETECTED,
        title="High Severity Vulnerability",
        description="A high severity test vulnerability",
        vuln_type="python_dependency",
    )
    test_session.add(vuln1)
    vulns.append(vuln1)
    
    # Medium severity vulnerability (fixed)
    vuln2 = Vulnerability(
        repo_id=test_repo.id,
        package_name="medium-vuln",
        severity=VulnSeverity.MEDIUM,
        status=VulnStatus.FIXED,
        title="Medium Severity Vulnerability",
        description="A medium severity test vulnerability",
        vuln_type="python_dependency",
    )
    test_session.add(vuln2)
    vulns.append(vuln2)
    
    await test_session.commit()
    return vulns


@pytest.mark.asyncio
async def test_list_repositories(test_session, test_repo, test_vulnerabilities, auth_context):
    """Test repository listing."""
    from src.api.repos import list_repositories
    
    # Test listing repositories
    with patch("src.api.repos.require_viewer_auth", return_value=auth_context):
        repos = await list_repositories(auth=auth_context, db=test_session)
    
    assert len(repos) == 1
    repo = repos[0]
    
    assert repo.full_name == "test-org/test-repo" 
    assert repo.is_active is True
    assert repo.vuln_summary.total == 2
    assert repo.vuln_summary.by_severity["high"] == 1
    assert repo.vuln_summary.by_severity["medium"] == 1
    assert repo.vuln_summary.by_status["detected"] == 1
    assert repo.vuln_summary.by_status["fixed"] == 1


@pytest.mark.asyncio
async def test_get_repository_detail(test_session, test_repo, test_vulnerabilities, auth_context):
    """Test repository detail retrieval."""
    from src.api.repos import get_repository
    
    with patch("src.api.repos.require_viewer_auth", return_value=auth_context):
        repo_detail = await get_repository(str(test_repo.id), auth=auth_context, db=test_session)
    
    assert repo_detail.full_name == "test-org/test-repo"
    assert len(repo_detail.vulnerabilities) == 2
    
    # Check vulnerability data
    vuln_names = {v["package_name"] for v in repo_detail.vulnerabilities}
    assert "high-vuln" in vuln_names
    assert "medium-vuln" in vuln_names


@pytest.mark.asyncio
async def test_update_repository_config(test_session, test_repo, auth_context):
    """Test repository configuration update."""
    from src.api.repos import update_repository_config, UpdateRepoConfig, ScanConfig, PolicyOverrides
    
    # Prepare update data
    new_config = UpdateRepoConfig(
        scan_config=ScanConfig(
            scan_types=["pip-audit", "trivy"],
            schedule="weekly",
            auto_fix=False,
            excluded_paths=["/test"],
            severity_threshold="high"
        ),
        policy_overrides=PolicyOverrides(
            auto_merge_enabled=False,
            min_confidence_threshold=0.9,
        )
    )
    
    with patch("src.api.repos.require_admin_auth", return_value=auth_context):
        result = await update_repository_config(
            str(test_repo.id),
            new_config,
            auth=auth_context,
            db=test_session
        )
    
    assert result["status"] == "updated"
    
    # Verify config was updated
    await test_session.refresh(test_repo)
    assert test_repo.scan_config["schedule"] == "weekly"
    assert test_repo.scan_config["auto_fix"] is False
    assert test_repo.policy_overrides["auto_merge_enabled"] is False
    assert test_repo.policy_overrides["min_confidence_threshold"] == 0.9


@pytest.mark.asyncio
async def test_activate_deactivate_repository(test_session, test_repo, auth_context):
    """Test repository activation/deactivation."""
    from src.api.repos import deactivate_repository, activate_repository
    
    # Test deactivation
    with patch("src.api.repos.require_admin_auth", return_value=auth_context):
        result = await deactivate_repository(
            str(test_repo.id),
            auth=auth_context,
            db=test_session
        )
    
    assert result["status"] == "deactivated"
    await test_session.refresh(test_repo)
    assert test_repo.is_active is False
    
    # Test activation
    with patch("src.api.repos.require_admin_auth", return_value=auth_context):
        result = await activate_repository(
            str(test_repo.id),
            auth=auth_context,
            db=test_session
        )
    
    assert result["status"] == "activated"
    await test_session.refresh(test_repo)
    assert test_repo.is_active is True


@pytest.mark.asyncio
async def test_trigger_manual_scan(test_session, test_repo, auth_context):
    """Test manual scan trigger."""
    from src.api.repos import trigger_manual_scan
    
    original_next_scan = test_repo.next_scan_at
    
    with patch("src.api.repos.require_reviewer_auth", return_value=auth_context):
        result = await trigger_manual_scan(
            str(test_repo.id),
            auth=auth_context,
            db=test_session
        )
    
    assert result["status"] == "scan_triggered"
    
    # Verify next_scan_at was updated
    await test_session.refresh(test_repo)
    assert test_repo.next_scan_at != original_next_scan
    assert test_repo.next_scan_at is not None