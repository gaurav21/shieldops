"""GitHub App installation handling."""

import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..db.models import Organization, Repository
from .app_auth import GitHubAppAuth

logger = logging.getLogger(__name__)


class InstallationHandler:
    """Handles GitHub App installation events."""

    def __init__(self, github_app_auth: GitHubAppAuth):
        self.github_app = github_app_auth

    async def handle_installation_created(
        self, payload: Dict[str, Any], db: AsyncSession
    ) -> Dict[str, Any]:
        """Handle app installation event."""
        installation = payload["installation"]
        account = installation["account"]
        
        installation_id = installation["id"]
        github_org_id = account["id"]
        name = account["login"]
        avatar_url = account.get("avatar_url")
        
        # Create or update organization
        result = await db.execute(
            select(Organization).where(Organization.github_org_id == github_org_id)
        )
        org = result.scalars().first()
        
        if org:
            # Update existing organization
            org.installation_id = installation_id
            org.avatar_url = avatar_url
            logger.info(f"Updated organization {name} (ID: {github_org_id})")
        else:
            # Create new organization
            org = Organization(
                github_org_id=github_org_id,
                name=name,
                slug=name.lower().replace(" ", "-"),
                avatar_url=avatar_url,
                installation_id=installation_id,
            )
            db.add(org)
            logger.info(f"Created organization {name} (ID: {github_org_id})")
        
        await db.commit()
        
        # Fetch and sync repositories
        await self._sync_repositories(org, installation_id, db)
        
        return {"status": "success", "organization": name}

    async def handle_installation_deleted(
        self, payload: Dict[str, Any], db: AsyncSession
    ) -> Dict[str, Any]:
        """Handle app uninstallation event."""
        installation = payload["installation"]
        account = installation["account"]
        github_org_id = account["id"]
        
        # Find and deactivate organization
        result = await db.execute(
            select(Organization).where(Organization.github_org_id == github_org_id)
        )
        org = result.scalars().first()
        
        if org:
            # Deactivate all repositories
            repos_result = await db.execute(
                select(Repository).where(Repository.org_id == org.id)
            )
            repos = repos_result.scalars().all()
            
            for repo in repos:
                repo.is_active = False
            
            logger.info(f"Deactivated {len(repos)} repositories for org {org.name}")
            await db.commit()
            
            return {"status": "success", "organization": org.name, "deactivated_repos": len(repos)}
        
        logger.warning(f"Organization not found for GitHub org ID {github_org_id}")
        return {"status": "not_found", "github_org_id": github_org_id}

    async def handle_installation_repositories(
        self, payload: Dict[str, Any], db: AsyncSession
    ) -> Dict[str, Any]:
        """Handle repositories added/removed from installation."""
        installation = payload["installation"]
        action = payload["action"]  # "added" or "removed"
        repositories_added = payload.get("repositories_added", [])
        repositories_removed = payload.get("repositories_removed", [])
        
        installation_id = installation["id"]
        
        # Find organization
        result = await db.execute(
            select(Organization).where(Organization.installation_id == installation_id)
        )
        org = result.scalars().first()
        
        if not org:
            logger.error(f"Organization not found for installation {installation_id}")
            return {"status": "error", "message": "Organization not found"}
        
        added_count = 0
        removed_count = 0
        
        # Handle added repositories
        for repo_data in repositories_added:
            await self._add_repository(org, repo_data, db)
            added_count += 1
        
        # Handle removed repositories
        for repo_data in repositories_removed:
            await self._remove_repository(repo_data["id"], db)
            removed_count += 1
        
        await db.commit()
        
        logger.info(f"Repositories updated for {org.name}: +{added_count}, -{removed_count}")
        return {
            "status": "success",
            "organization": org.name,
            "added": added_count,
            "removed": removed_count
        }

    async def _sync_repositories(
        self, org: Organization, installation_id: int, db: AsyncSession
    ) -> None:
        """Sync all repositories for an installation."""
        try:
            # Fetch repositories from GitHub API
            response = await self.github_app.make_installation_request(
                installation_id, "GET", "/installation/repositories"
            )
            response.raise_for_status()
            
            data = response.json()
            repositories = data.get("repositories", [])
            
            logger.info(f"Syncing {len(repositories)} repositories for {org.name}")
            
            # Sync each repository
            for repo_data in repositories:
                await self._add_repository(org, repo_data, db)
                
        except Exception as e:
            logger.error(f"Failed to sync repositories for {org.name}: {e}")

    async def _add_repository(
        self, org: Organization, repo_data: Dict[str, Any], db: AsyncSession
    ) -> Repository:
        """Add or update a repository."""
        github_repo_id = repo_data["id"]
        full_name = repo_data["full_name"]
        default_branch = repo_data.get("default_branch", "main")
        
        # Check if repository already exists
        result = await db.execute(
            select(Repository).where(Repository.github_repo_id == github_repo_id)
        )
        repo = result.scalars().first()
        
        if repo:
            # Update existing repository
            repo.full_name = full_name
            repo.default_branch = default_branch
            repo.is_active = True
            logger.debug(f"Updated repository {full_name}")
        else:
            # Create new repository
            repo = Repository(
                org_id=org.id,
                github_repo_id=github_repo_id,
                full_name=full_name,
                default_branch=default_branch,
                is_active=True,
            )
            db.add(repo)
            logger.debug(f"Added repository {full_name}")
        
        return repo

    async def _remove_repository(self, github_repo_id: int, db: AsyncSession) -> None:
        """Deactivate a repository."""
        result = await db.execute(
            select(Repository).where(Repository.github_repo_id == github_repo_id)
        )
        repo = result.scalars().first()
        
        if repo:
            repo.is_active = False
            logger.debug(f"Deactivated repository {repo.full_name}")


async def handle_github_app_webhook(
    payload: Dict[str, Any], 
    github_app_auth: GitHubAppAuth,
    db: AsyncSession
) -> Dict[str, Any]:
    """Main webhook handler for GitHub App events."""
    action = payload.get("action")
    
    if "installation" not in payload:
        return {"status": "ignored", "reason": "Not an installation event"}
    
    handler = InstallationHandler(github_app_auth)
    
    if action == "created":
        return await handler.handle_installation_created(payload, db)
    elif action == "deleted":
        return await handler.handle_installation_deleted(payload, db)
    elif action in ("added", "removed"):
        return await handler.handle_installation_repositories(payload, db)
    else:
        logger.info(f"Ignoring installation action: {action}")
        return {"status": "ignored", "action": action}