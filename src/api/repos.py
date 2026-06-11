"""Repository management API endpoints."""

import os
import logging
from datetime import datetime
from typing import List, Optional
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, desc
from pydantic import BaseModel

from ..db.database import get_db_session
from ..db.models import Repository, Vulnerability, VulnStatus, VulnSeverity, RemediationSession
from .auth import AuthContext, require_viewer_auth, require_reviewer_auth, require_admin_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/repos", tags=["repositories"])


# Pydantic models
class ScanConfig(BaseModel):
    scan_types: List[str]
    schedule: str
    auto_fix: bool
    excluded_paths: List[str]
    severity_threshold: str


class PolicyOverrides(BaseModel):
    auto_merge_enabled: Optional[bool] = None
    min_confidence_threshold: Optional[float] = None
    require_breaking_change_approval: Optional[bool] = None


class UpdateRepoConfig(BaseModel):
    scan_config: Optional[ScanConfig] = None
    policy_overrides: Optional[PolicyOverrides] = None


class VulnSummary(BaseModel):
    total: int
    by_severity: dict
    by_status: dict


class RepoSummary(BaseModel):
    id: str
    github_repo_id: int
    full_name: str
    default_branch: str
    is_active: bool
    last_scan_at: Optional[datetime]
    next_scan_at: Optional[datetime]
    vuln_summary: VulnSummary
    active_sessions: int
    scan_config: dict
    policy_overrides: dict


class RepoDetail(RepoSummary):
    vulnerabilities: List[dict]
    recent_sessions: List[dict]


@router.get("", response_model=List[RepoSummary])
@router.get("/", response_model=List[RepoSummary], include_in_schema=False)
async def list_repositories(
    active_only: bool = True,
    auth: AuthContext = Depends(require_viewer_auth),
    db: AsyncSession = Depends(get_db_session)
):
    """List repositories for current organization."""
    query = select(Repository).where(Repository.org_id == auth.org_id)
    
    if active_only:
        query = query.where(Repository.is_active == True)
    
    query = query.options(
        selectinload(Repository.vulnerabilities),
        selectinload(Repository.remediation_sessions)
    ).order_by(desc(Repository.updated_at))
    
    result = await db.execute(query)
    repos = result.scalars().all()
    
    # Build repository summaries
    summaries = []
    for repo in repos:
        # Calculate vulnerability summary
        vulns = repo.vulnerabilities
        vuln_summary = VulnSummary(
            total=len(vulns),
            by_severity={
                severity.value: sum(1 for v in vulns if v.severity == severity)
                for severity in VulnSeverity
            },
            by_status={
                status.value: sum(1 for v in vulns if v.status == status)
                for status in VulnStatus
            }
        )
        
        # Count active sessions
        active_sessions = sum(
            1 for session in repo.remediation_sessions
            if session.status.value in ["pending", "running"]
        )
        
        summaries.append(RepoSummary(
            id=str(repo.id),
            github_repo_id=repo.github_repo_id,
            full_name=repo.full_name,
            default_branch=repo.default_branch,
            is_active=repo.is_active,
            last_scan_at=repo.last_scan_at,
            next_scan_at=repo.next_scan_at,
            vuln_summary=vuln_summary,
            active_sessions=active_sessions,
            scan_config=repo.scan_config,
            policy_overrides=repo.policy_overrides,
        ))
    
    return summaries


class ConnectRepoRequest(BaseModel):
    owner: str
    repo: str


@router.get("/search/")
async def search_github_repos(
    q: str = "",
    auth: AuthContext = Depends(require_viewer_auth),
    db: AsyncSession = Depends(get_db_session),
):
    """Search GitHub repos accessible with the configured token."""
    gh_token = os.getenv("GITHUB_TOKEN", "")
    if not gh_token:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN not configured on server")

    headers = {"Authorization": f"token {gh_token}", "Accept": "application/vnd.github.v3+json"}

    async with httpx.AsyncClient(timeout=15) as client:
        if q:
            # Search repos the authenticated user can access
            resp = await client.get(
                f"https://api.github.com/search/repositories?q={q}+in:name+user:@me+fork:true&per_page=20",
                headers=headers,
            )
            if resp.status_code != 200:
                # Fallback: search all public repos matching query
                resp = await client.get(
                    f"https://api.github.com/search/repositories?q={q}&per_page=20",
                    headers=headers,
                )
            items = resp.json().get("items", [])
        else:
            # List repos for the authenticated user
            resp = await client.get(
                "https://api.github.com/user/repos?per_page=30&sort=updated&affiliation=owner,collaborator,organization_member",
                headers=headers,
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail=f"GitHub API error: {resp.status_code}")
            items = resp.json()

    # Check which are already connected
    result = await db.execute(select(Repository.github_repo_id).where(Repository.org_id == auth.org_id))
    connected_ids = {row[0] for row in result.all()}

    return [
        {
            "github_repo_id": r["id"],
            "full_name": r["full_name"],
            "description": r.get("description"),
            "language": r.get("language"),
            "default_branch": r.get("default_branch", "main"),
            "already_connected": r["id"] in connected_ids,
        }
        for r in items
    ]


@router.post("/connect/")
async def connect_repo(
    req: ConnectRepoRequest,
    auth: AuthContext = Depends(require_admin_auth),
    db: AsyncSession = Depends(get_db_session),
):
    """Connect a GitHub repo by owner/name."""
    gh_token = os.getenv("GITHUB_TOKEN", "")
    if not gh_token:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN not configured on server")

    # Fetch repo info from GitHub
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"https://api.github.com/repos/{req.owner}/{req.repo}",
            headers={"Authorization": f"token {gh_token}", "Accept": "application/vnd.github.v3+json"},
        )

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail=f"Repository {req.owner}/{req.repo} not found on GitHub")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"GitHub API error: {resp.status_code}")

    gh_repo = resp.json()

    # Check if already connected
    existing = await db.execute(
        select(Repository).where(
            Repository.github_repo_id == gh_repo["id"],
            Repository.org_id == auth.org_id,
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Repository already connected")

    repo = Repository(
        org_id=auth.org_id,
        github_repo_id=gh_repo["id"],
        full_name=gh_repo["full_name"],
        default_branch=gh_repo.get("default_branch", "main"),
        is_active=True,
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    logger.info(f"Connected repo: {repo.full_name} (id={repo.id})")

    return {
        "id": str(repo.id),
        "github_repo_id": repo.github_repo_id,
        "full_name": repo.full_name,
        "default_branch": repo.default_branch,
        "is_active": repo.is_active,
    }


@router.get("/{repo_id}", response_model=RepoDetail)
async def get_repository(
    repo_id: str,
    auth: AuthContext = Depends(require_viewer_auth),
    db: AsyncSession = Depends(get_db_session)
):
    """Get detailed repository information."""
    query = (
        select(Repository)
        .where(Repository.id == repo_id, Repository.org_id == auth.org_id)
        .options(
            selectinload(Repository.vulnerabilities),
            selectinload(Repository.remediation_sessions)
        )
    )
    
    result = await db.execute(query)
    repo = result.scalars().first()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Calculate vulnerability summary
    vulns = repo.vulnerabilities
    vuln_summary = VulnSummary(
        total=len(vulns),
        by_severity={
            severity.value: sum(1 for v in vulns if v.severity == severity)
            for severity in VulnSeverity
        },
        by_status={
            status.value: sum(1 for v in vulns if v.status == status)
            for status in VulnStatus
        }
    )
    
    # Count active sessions
    active_sessions = sum(
        1 for session in repo.remediation_sessions
        if session.status.value in ["pending", "running"]
    )
    
    # Get recent vulnerabilities (last 50)
    vulnerabilities = [
        {
            "id": str(vuln.id),
            "cve_id": vuln.cve_id,
            "package_name": vuln.package_name,
            "current_version": vuln.current_version,
            "fixed_version": vuln.fixed_version,
            "severity": vuln.severity.value,
            "status": vuln.status.value,
            "title": vuln.title,
            "reachable": vuln.reachable,
            "github_issue_number": vuln.github_issue_number,
            "first_detected_at": vuln.first_detected_at,
            "resolved_at": vuln.resolved_at,
        }
        for vuln in sorted(vulns, key=lambda v: v.first_detected_at, reverse=True)[:50]
    ]
    
    # Get recent sessions (last 20)
    sessions = sorted(repo.remediation_sessions, key=lambda s: s.created_at, reverse=True)[:20]
    recent_sessions = [
        {
            "id": str(session.id),
            "agent_type": session.agent_type,
            "status": session.status.value,
            "policy_decision": session.policy_decision,
            "pr_url": session.pr_url,
            "duration_seconds": session.duration_seconds,
            "acu_cost": session.acu_cost,
            "started_at": session.started_at,
            "completed_at": session.completed_at,
        }
        for session in sessions
    ]
    
    return RepoDetail(
        id=str(repo.id),
        github_repo_id=repo.github_repo_id,
        full_name=repo.full_name,
        default_branch=repo.default_branch,
        is_active=repo.is_active,
        last_scan_at=repo.last_scan_at,
        next_scan_at=repo.next_scan_at,
        vuln_summary=vuln_summary,
        active_sessions=active_sessions,
        scan_config=repo.scan_config,
        policy_overrides=repo.policy_overrides,
        vulnerabilities=vulnerabilities,
        recent_sessions=recent_sessions,
    )


@router.post("/{repo_id}/scan")
async def trigger_manual_scan(
    repo_id: str,
    auth: AuthContext = Depends(require_reviewer_auth),
    db: AsyncSession = Depends(get_db_session)
):
    """Trigger manual scan for repository."""
    query = select(Repository).where(Repository.id == repo_id, Repository.org_id == auth.org_id)
    result = await db.execute(query)
    repo = result.scalars().first()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    if not repo.is_active:
        raise HTTPException(status_code=400, detail="Repository is not active")
    
    # TODO: Integrate with existing scanner
    # For now, just update next_scan_at to trigger scan
    repo.next_scan_at = datetime.utcnow()
    await db.commit()
    
    return {"status": "scan_triggered", "repository": repo.full_name}


@router.patch("/{repo_id}/config")
async def update_repository_config(
    repo_id: str,
    config_update: UpdateRepoConfig,
    auth: AuthContext = Depends(require_admin_auth),
    db: AsyncSession = Depends(get_db_session)
):
    """Update repository scan configuration."""
    query = select(Repository).where(Repository.id == repo_id, Repository.org_id == auth.org_id)
    result = await db.execute(query)
    repo = result.scalars().first()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Update scan config
    if config_update.scan_config:
        repo.scan_config = config_update.scan_config.dict()
    
    # Update policy overrides
    if config_update.policy_overrides:
        current_overrides = repo.policy_overrides or {}
        current_overrides.update(
            {k: v for k, v in config_update.policy_overrides.dict().items() if v is not None}
        )
        repo.policy_overrides = current_overrides
    
    repo.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"status": "updated", "repository": repo.full_name}


@router.post("/{repo_id}/activate")
async def activate_repository(
    repo_id: str,
    auth: AuthContext = Depends(require_admin_auth),
    db: AsyncSession = Depends(get_db_session)
):
    """Enable ShieldOps for this repository."""
    query = select(Repository).where(Repository.id == repo_id, Repository.org_id == auth.org_id)
    result = await db.execute(query)
    repo = result.scalars().first()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    repo.is_active = True
    repo.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"status": "activated", "repository": repo.full_name}


@router.post("/{repo_id}/deactivate")
async def deactivate_repository(
    repo_id: str,
    auth: AuthContext = Depends(require_admin_auth),
    db: AsyncSession = Depends(get_db_session)
):
    """Disable ShieldOps for this repository."""
    query = select(Repository).where(Repository.id == repo_id, Repository.org_id == auth.org_id)
    result = await db.execute(query)
    repo = result.scalars().first()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    repo.is_active = False
    repo.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"status": "deactivated", "repository": repo.full_name}