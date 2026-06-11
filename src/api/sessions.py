"""Remediation session management API endpoints."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import desc, and_
from pydantic import BaseModel

from ..db.database import get_db_session
from ..db.models import RemediationSession, Repository, Vulnerability, SessionStatus
from .auth import AuthContext, require_viewer_auth

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class SessionListItem(BaseModel):
    id: str
    agent_type: str
    status: str
    repository: str  # full_name
    vulnerability_title: str
    package_name: str
    policy_decision: Optional[str]
    pr_url: Optional[str]
    duration_seconds: Optional[int]
    acu_cost: Optional[float]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime


class SessionDetail(SessionListItem):
    repo_id: str
    vuln_id: str
    agent_session_id: Optional[str]
    prompt: Optional[str]
    structured_output: Optional[dict]
    policy_reason: Optional[str]
    pr_number: Optional[int]
    evidence_bundle: Optional[str]
    vulnerability: dict


@router.get("", response_model=List[SessionListItem])
@router.get("/", response_model=List[SessionListItem], include_in_schema=False)
async def list_sessions(
    repo_id: Optional[str] = Query(None, description="Filter by repository ID"),
    status: Optional[SessionStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    auth: AuthContext = Depends(require_viewer_auth),
    db: AsyncSession = Depends(get_db_session)
):
    """List remediation sessions with filtering."""
    # Base query - only sessions from repos in current org
    query = (
        select(RemediationSession)
        .join(Repository)
        .where(Repository.org_id == auth.org_id)
        .options(
            selectinload(RemediationSession.repository),
            selectinload(RemediationSession.vulnerability)
        )
    )
    
    # Apply filters
    if repo_id:
        query = query.where(RemediationSession.repo_id == repo_id)
    
    if status:
        query = query.where(RemediationSession.status == status)
    
    # Order by most recent first
    query = query.order_by(desc(RemediationSession.created_at))
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    # Build response
    session_list = []
    for session in sessions:
        session_list.append(SessionListItem(
            id=str(session.id),
            agent_type=session.agent_type,
            status=session.status.value,
            repository=session.repository.full_name,
            vulnerability_title=session.vulnerability.title,
            package_name=session.vulnerability.package_name,
            policy_decision=session.policy_decision,
            pr_url=session.pr_url,
            duration_seconds=session.duration_seconds,
            acu_cost=session.acu_cost,
            started_at=session.started_at,
            completed_at=session.completed_at,
            created_at=session.created_at,
        ))
    
    return session_list


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(
    session_id: str,
    auth: AuthContext = Depends(require_viewer_auth),
    db: AsyncSession = Depends(get_db_session)
):
    """Get detailed session information."""
    # Query session with all related data
    query = (
        select(RemediationSession)
        .join(Repository)
        .where(
            and_(
                RemediationSession.id == session_id,
                Repository.org_id == auth.org_id
            )
        )
        .options(
            selectinload(RemediationSession.repository),
            selectinload(RemediationSession.vulnerability)
        )
    )
    
    result = await db.execute(query)
    session = result.scalars().first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Build vulnerability data
    vuln = session.vulnerability
    vulnerability_data = {
        "id": str(vuln.id),
        "cve_id": vuln.cve_id,
        "package_name": vuln.package_name,
        "current_version": vuln.current_version,
        "fixed_version": vuln.fixed_version,
        "severity": vuln.severity.value,
        "status": vuln.status.value,
        "title": vuln.title,
        "description": vuln.description,
        "reachable": vuln.reachable,
        "github_issue_number": vuln.github_issue_number,
    }
    
    return SessionDetail(
        id=str(session.id),
        repo_id=str(session.repo_id),
        vuln_id=str(session.vuln_id),
        agent_type=session.agent_type,
        agent_session_id=session.agent_session_id,
        status=session.status.value,
        prompt=session.prompt,
        structured_output=session.structured_output,
        policy_decision=session.policy_decision,
        policy_reason=session.policy_reason,
        pr_url=session.pr_url,
        pr_number=session.pr_number,
        evidence_bundle=session.evidence_bundle,
        duration_seconds=session.duration_seconds,
        acu_cost=session.acu_cost,
        started_at=session.started_at,
        completed_at=session.completed_at,
        created_at=session.created_at,
        repository=session.repository.full_name,
        vulnerability_title=vuln.title,
        package_name=vuln.package_name,
        vulnerability=vulnerability_data,
    )