"""Vulnerability management API endpoints."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import desc, and_
from pydantic import BaseModel

from ..db.database import get_db_session
from ..db.models import Vulnerability, Repository, VulnStatus, VulnSeverity, RemediationSession
from .auth import AuthContext, require_viewer_auth, require_reviewer_auth

router = APIRouter(prefix="/api/vulns", tags=["vulnerabilities"])


class VulnListItem(BaseModel):
    id: str
    cve_id: Optional[str]
    package_name: str
    current_version: Optional[str]
    fixed_version: Optional[str]
    severity: str
    status: str
    title: str
    reachable: Optional[bool]
    repository: str  # full_name
    github_issue_number: Optional[int]
    first_detected_at: datetime
    resolved_at: Optional[datetime]
    session_count: int
    latest_session_status: Optional[str]


class VulnDetail(VulnListItem):
    description: str
    vuln_type: str
    repo_id: str
    sessions: List[dict]


class UpdateVulnStatus(BaseModel):
    status: VulnStatus
    reason: Optional[str] = None


@router.get("", response_model=List[VulnListItem])
@router.get("/", response_model=List[VulnListItem], include_in_schema=False)
async def list_vulnerabilities(
    repo_id: Optional[str] = Query(None, description="Filter by repository ID"),
    severity: Optional[VulnSeverity] = Query(None, description="Filter by severity"),
    status: Optional[VulnStatus] = Query(None, description="Filter by status"),
    reachable: Optional[bool] = Query(None, description="Filter by reachability"),
    limit: int = Query(100, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    auth: AuthContext = Depends(require_viewer_auth),
    db: AsyncSession = Depends(get_db_session)
):
    """List vulnerabilities across organization with filtering."""
    # Base query - only vulnerabilities from repos in current org
    query = (
        select(Vulnerability)
        .join(Repository)
        .where(Repository.org_id == auth.org_id)
        .options(
            selectinload(Vulnerability.repository),
            selectinload(Vulnerability.remediation_sessions)
        )
    )
    
    # Apply filters
    if repo_id:
        query = query.where(Vulnerability.repo_id == repo_id)
    
    if severity:
        query = query.where(Vulnerability.severity == severity)
    
    if status:
        query = query.where(Vulnerability.status == status)
    
    if reachable is not None:
        query = query.where(Vulnerability.reachable == reachable)
    
    # Order by most recent first
    query = query.order_by(desc(Vulnerability.first_detected_at))
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    vulns = result.scalars().all()
    
    # Build response
    vuln_list = []
    for vuln in vulns:
        sessions = vuln.remediation_sessions
        session_count = len(sessions)
        
        # Get latest session status
        latest_session_status = None
        if sessions:
            latest_session = max(sessions, key=lambda s: s.created_at)
            latest_session_status = latest_session.status.value
        
        vuln_list.append(VulnListItem(
            id=str(vuln.id),
            cve_id=vuln.cve_id,
            package_name=vuln.package_name,
            current_version=vuln.current_version,
            fixed_version=vuln.fixed_version,
            severity=vuln.severity.value,
            status=vuln.status.value,
            title=vuln.title,
            reachable=vuln.reachable,
            repository=vuln.repository.full_name,
            github_issue_number=vuln.github_issue_number,
            first_detected_at=vuln.first_detected_at,
            resolved_at=vuln.resolved_at,
            session_count=session_count,
            latest_session_status=latest_session_status,
        ))
    
    return vuln_list


@router.get("/{vuln_id}", response_model=VulnDetail)
async def get_vulnerability(
    vuln_id: str,
    auth: AuthContext = Depends(require_viewer_auth),
    db: AsyncSession = Depends(get_db_session)
):
    """Get detailed vulnerability information."""
    # Query vulnerability with all related data
    query = (
        select(Vulnerability)
        .join(Repository)
        .where(
            and_(
                Vulnerability.id == vuln_id,
                Repository.org_id == auth.org_id
            )
        )
        .options(
            selectinload(Vulnerability.repository),
            selectinload(Vulnerability.remediation_sessions)
        )
    )
    
    result = await db.execute(query)
    vuln = result.scalars().first()
    
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    # Build sessions data
    sessions = []
    for session in sorted(vuln.remediation_sessions, key=lambda s: s.created_at, reverse=True):
        sessions.append({
            "id": str(session.id),
            "agent_type": session.agent_type,
            "status": session.status.value,
            "policy_decision": session.policy_decision,
            "policy_reason": session.policy_reason,
            "pr_url": session.pr_url,
            "pr_number": session.pr_number,
            "duration_seconds": session.duration_seconds,
            "acu_cost": session.acu_cost,
            "started_at": session.started_at,
            "completed_at": session.completed_at,
            "created_at": session.created_at,
        })
    
    session_count = len(sessions)
    latest_session_status = sessions[0]["status"] if sessions else None
    
    return VulnDetail(
        id=str(vuln.id),
        cve_id=vuln.cve_id,
        package_name=vuln.package_name,
        current_version=vuln.current_version,
        fixed_version=vuln.fixed_version,
        severity=vuln.severity.value,
        status=vuln.status.value,
        title=vuln.title,
        description=vuln.description,
        vuln_type=vuln.vuln_type,
        reachable=vuln.reachable,
        repository=vuln.repository.full_name,
        repo_id=str(vuln.repo_id),
        github_issue_number=vuln.github_issue_number,
        first_detected_at=vuln.first_detected_at,
        resolved_at=vuln.resolved_at,
        session_count=session_count,
        latest_session_status=latest_session_status,
        sessions=sessions,
    )


@router.post("/{vuln_id}/ignore")
async def ignore_vulnerability(
    vuln_id: str,
    reason: Optional[str] = None,
    auth: AuthContext = Depends(require_reviewer_auth),
    db: AsyncSession = Depends(get_db_session)
):
    """Mark vulnerability as ignored."""
    # Query vulnerability
    query = (
        select(Vulnerability)
        .join(Repository)
        .where(
            and_(
                Vulnerability.id == vuln_id,
                Repository.org_id == auth.org_id
            )
        )
    )
    
    result = await db.execute(query)
    vuln = result.scalars().first()
    
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    # Update status
    vuln.status = VulnStatus.IGNORED
    vuln.resolved_at = datetime.utcnow()
    await db.commit()
    
    # TODO: Log audit event
    
    return {
        "status": "ignored",
        "vulnerability": vuln.package_name,
        "reason": reason,
    }


@router.post("/{vuln_id}/retry")
async def retry_vulnerability_remediation(
    vuln_id: str,
    auth: AuthContext = Depends(require_reviewer_auth),
    db: AsyncSession = Depends(get_db_session)
):
    """Re-trigger remediation for a vulnerability."""
    # Query vulnerability
    query = (
        select(Vulnerability)
        .join(Repository)
        .where(
            and_(
                Vulnerability.id == vuln_id,
                Repository.org_id == auth.org_id
            )
        )
    )
    
    result = await db.execute(query)
    vuln = result.scalars().first()
    
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    # Check if vulnerability is in a retryable state
    if vuln.status in [VulnStatus.FIXED, VulnStatus.IGNORED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot retry vulnerability in {vuln.status.value} status"
        )
    
    # Update status to detected (will be picked up by remediation engine)
    vuln.status = VulnStatus.DETECTED
    vuln.resolved_at = None
    await db.commit()
    
    # TODO: Trigger remediation pipeline
    
    return {
        "status": "retry_triggered",
        "vulnerability": vuln.package_name,
    }