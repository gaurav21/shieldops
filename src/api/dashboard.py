"""Dashboard data API endpoints."""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, and_, desc
from pydantic import BaseModel

from ..db.database import get_db_session
from ..db.models import (
    Organization, Repository, Vulnerability, RemediationSession,
    SessionStatus
)
from ..shared.org_metrics import (
    vulns_by_severity as _vulns_by_severity,
    vulns_by_status as _vulns_by_status,
    compute_fix_rate,
    count_active_sessions,
    compute_mttr_hours,
)
from .auth import AuthContext, require_viewer_auth

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class OverviewStats(BaseModel):
    total_repos: int
    active_repos: int
    total_vulns: int
    vulns_by_severity: Dict[str, int]
    vulns_by_status: Dict[str, int]
    fix_rate: float
    mttr_hours: float
    active_sessions: int
    completed_sessions: int
    total_acu_cost: float
    trend_data: Dict[str, List[Dict[str, Any]]]


class ActivityItem(BaseModel):
    id: str
    type: str  # 'session_created', 'session_completed', 'vuln_detected', etc.
    title: str
    description: str
    timestamp: datetime
    metadata: Dict[str, Any]


@router.get("/overview", response_model=OverviewStats)
async def get_dashboard_overview(
    days: int = Query(30, ge=1, le=365, description="Time range in days"),
    auth: AuthContext = Depends(require_viewer_auth),
    db: AsyncSession = Depends(get_db_session)
):
    """Get organization dashboard overview with metrics and trends."""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Get organization with all related data
    query = (
        select(Organization)
        .where(Organization.id == auth.org_id)
        .options(
            selectinload(Organization.repositories).selectinload(Repository.vulnerabilities),
            selectinload(Organization.repositories).selectinload(Repository.remediation_sessions)
        )
    )
    
    result = await db.execute(query)
    org = result.scalars().first()
    
    if not org:
        return OverviewStats(
            total_repos=0, active_repos=0, total_vulns=0,
            vulns_by_severity={}, vulns_by_status={}, fix_rate=0.0,
            mttr_hours=0.0, active_sessions=0, completed_sessions=0,
            total_acu_cost=0.0, trend_data={}
        )
    
    # Aggregate data
    all_repos = org.repositories
    active_repos = [repo for repo in all_repos if repo.is_active]
    all_vulns = []
    all_sessions = []
    
    for repo in active_repos:
        all_vulns.extend(repo.vulnerabilities)
        all_sessions.extend(repo.remediation_sessions)
    
    # Basic counts
    total_repos = len(all_repos)
    active_repo_count = len(active_repos)
    total_vulns = len(all_vulns)
    
    # Vulnerability metrics
    severity_counts = _vulns_by_severity(all_vulns)
    status_counts = _vulns_by_status(all_vulns)
    fix_rate = compute_fix_rate(all_vulns)

    # Session metrics
    active_sessions = count_active_sessions(all_sessions)
    completed_sessions = sum(
        1 for s in all_sessions
        if s.status == SessionStatus.COMPLETED
    )
    mttr_hours = compute_mttr_hours(all_sessions, since=since_date)

    # ACU cost (from completed sessions in time range)
    completed_recent_sessions = [
        s for s in all_sessions
        if (s.status == SessionStatus.COMPLETED and
            s.completed_at and s.completed_at >= since_date)
    ]
    total_acu_cost = sum(s.acu_cost or 0.0 for s in completed_recent_sessions)
    
    # Generate trend data (daily buckets for the requested period)
    trend_data = await _generate_trend_data(auth.org_id, since_date, days, db)
    
    return OverviewStats(
        total_repos=total_repos,
        active_repos=active_repo_count,
        total_vulns=total_vulns,
        vulns_by_severity=severity_counts,
        vulns_by_status=status_counts,
        fix_rate=round(fix_rate, 1),
        mttr_hours=round(mttr_hours, 1),
        active_sessions=active_sessions,
        completed_sessions=completed_sessions,
        total_acu_cost=round(total_acu_cost, 2),
        trend_data=trend_data,
    )


@router.get("/activity", response_model=List[ActivityItem])
async def get_recent_activity(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of activities"),
    auth: AuthContext = Depends(require_viewer_auth),
    db: AsyncSession = Depends(get_db_session)
):
    """Get recent activity feed."""
    activities = []
    
    # Get recent vulnerabilities (last 30 days)
    recent_vulns_query = (
        select(Vulnerability)
        .join(Repository)
        .where(
            and_(
                Repository.org_id == auth.org_id,
                Vulnerability.first_detected_at >= datetime.utcnow() - timedelta(days=30)
            )
        )
        .options(selectinload(Vulnerability.repository))
        .order_by(desc(Vulnerability.first_detected_at))
        .limit(20)
    )
    
    result = await db.execute(recent_vulns_query)
    recent_vulns = result.scalars().all()
    
    for vuln in recent_vulns:
        activities.append(ActivityItem(
            id=f"vuln-{vuln.id}",
            type="vulnerability_detected",
            title=f"Vulnerability detected: {vuln.package_name}",
            description=f"{vuln.severity.value.upper()} severity vulnerability in {vuln.repository.full_name}",
            timestamp=vuln.first_detected_at,
            metadata={
                "package_name": vuln.package_name,
                "severity": vuln.severity.value,
                "repository": vuln.repository.full_name,
                "cve_id": vuln.cve_id,
            }
        ))
    
    # Get recent sessions (last 30 days)
    recent_sessions_query = (
        select(RemediationSession)
        .join(Repository)
        .where(
            and_(
                Repository.org_id == auth.org_id,
                RemediationSession.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        )
        .options(
            selectinload(RemediationSession.repository),
            selectinload(RemediationSession.vulnerability)
        )
        .order_by(desc(RemediationSession.created_at))
        .limit(20)
    )
    
    result = await db.execute(recent_sessions_query)
    recent_sessions = result.scalars().all()
    
    for session in recent_sessions:
        if session.status == SessionStatus.COMPLETED:
            activities.append(ActivityItem(
                id=f"session-completed-{session.id}",
                type="session_completed",
                title=f"Remediation completed: {session.vulnerability.package_name}",
                description=f"Policy decision: {session.policy_decision or 'pending'}",
                timestamp=session.completed_at or session.created_at,
                metadata={
                    "package_name": session.vulnerability.package_name,
                    "repository": session.repository.full_name,
                    "policy_decision": session.policy_decision,
                    "pr_url": session.pr_url,
                    "duration_seconds": session.duration_seconds,
                }
            ))
        else:
            activities.append(ActivityItem(
                id=f"session-created-{session.id}",
                type="session_created",
                title=f"Remediation started: {session.vulnerability.package_name}",
                description=f"Agent: {session.agent_type}, Status: {session.status.value}",
                timestamp=session.started_at or session.created_at,
                metadata={
                    "package_name": session.vulnerability.package_name,
                    "repository": session.repository.full_name,
                    "agent_type": session.agent_type,
                    "status": session.status.value,
                }
            ))
    
    # Sort all activities by timestamp (most recent first) and limit
    all_activities = sorted(activities, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    return all_activities


async def _generate_trend_data(
    org_id: str, 
    since_date: datetime, 
    days: int, 
    db: AsyncSession
) -> Dict[str, List[Dict[str, Any]]]:
    """Generate trend data for vulnerabilities and sessions."""
    # Create daily buckets
    buckets = []
    for i in range(days):
        bucket_date = since_date + timedelta(days=i)
        buckets.append(bucket_date.date())
    
    # Get daily vulnerability counts
    vuln_trend = []
    session_trend = []
    
    for bucket_date in buckets:
        start_of_day = datetime.combine(bucket_date, datetime.min.time())
        end_of_day = datetime.combine(bucket_date, datetime.max.time())
        
        # Count vulnerabilities detected on this day
        vuln_count_query = (
            select(func.count(Vulnerability.id))
            .join(Repository)
            .where(
                and_(
                    Repository.org_id == org_id,
                    Vulnerability.first_detected_at >= start_of_day,
                    Vulnerability.first_detected_at <= end_of_day
                )
            )
        )
        
        result = await db.execute(vuln_count_query)
        vuln_count = result.scalar() or 0
        
        vuln_trend.append({
            "date": bucket_date.isoformat(),
            "count": vuln_count
        })
        
        # Count sessions created on this day
        session_count_query = (
            select(func.count(RemediationSession.id))
            .join(Repository)
            .where(
                and_(
                    Repository.org_id == org_id,
                    RemediationSession.created_at >= start_of_day,
                    RemediationSession.created_at <= end_of_day
                )
            )
        )
        
        result = await db.execute(session_count_query)
        session_count = result.scalar() or 0
        
        session_trend.append({
            "date": bucket_date.isoformat(),
            "count": session_count
        })
    
    return {
        "vulnerabilities": vuln_trend,
        "sessions": session_trend
    }