"""Organization management API endpoints."""

from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from ..db.database import get_db_session
from ..db.models import Organization, Repository
from ..shared.org_metrics import (
    vulns_by_severity as _vulns_by_severity,
    compute_fix_rate,
    count_active_sessions,
    compute_mttr_hours,
)
from .auth import AuthContext, require_viewer_auth, require_admin_auth

router = APIRouter(prefix="/api/orgs", tags=["organizations"])


class OrgSettings(BaseModel):
    default_scan_schedule: str = "daily"
    auto_merge_enabled: bool = True
    notification_settings: Dict[str, Any] = {}


class UpdateOrgSettings(BaseModel):
    settings: OrgSettings


class OrgOverview(BaseModel):
    id: str
    name: str
    slug: str
    avatar_url: str
    plan: str
    repo_count: int
    total_vulns: int
    vulns_by_severity: Dict[str, int]
    fix_rate: float  # Percentage of vulns fixed/resolved
    mttr_hours: float  # Mean time to resolution
    active_sessions: int
    settings: Dict[str, Any]
    created_at: datetime


@router.get("/current", response_model=OrgOverview)
async def get_current_organization(
    auth: AuthContext = Depends(require_viewer_auth),
    db: AsyncSession = Depends(get_db_session)
):
    """Get current organization overview with metrics."""
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
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Calculate metrics
    all_vulns = []
    all_sessions = []
    active_repos = 0
    
    for repo in org.repositories:
        if repo.is_active:
            active_repos += 1
            all_vulns.extend(repo.vulnerabilities)
            all_sessions.extend(repo.remediation_sessions)
    
    total_vulns = len(all_vulns)
    severity_counts = _vulns_by_severity(all_vulns)
    fix_rate = compute_fix_rate(all_vulns)
    mttr_hours = compute_mttr_hours(all_sessions)
    active_sessions = count_active_sessions(all_sessions)
    
    return OrgOverview(
        id=str(org.id),
        name=org.name,
        slug=org.slug,
        avatar_url=org.avatar_url or "",
        plan=org.plan.value,
        repo_count=active_repos,
        total_vulns=total_vulns,
        vulns_by_severity=severity_counts,
        fix_rate=round(fix_rate, 1),
        mttr_hours=round(mttr_hours, 1),
        active_sessions=active_sessions,
        settings=org.settings,
        created_at=org.created_at,
    )


@router.patch("/current/settings")
async def update_organization_settings(
    settings_update: UpdateOrgSettings,
    auth: AuthContext = Depends(require_admin_auth),
    db: AsyncSession = Depends(get_db_session)
):
    """Update organization settings."""
    query = select(Organization).where(Organization.id == auth.org_id)
    result = await db.execute(query)
    org = result.scalars().first()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Update settings
    org.settings.update(settings_update.settings.dict())
    org.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"status": "updated", "organization": org.name}