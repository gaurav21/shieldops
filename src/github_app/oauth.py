"""GitHub OAuth flow for user authentication."""

import os
import logging
from typing import Dict, Any, Optional
import httpx
import jwt
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..db.models import User, Organization

logger = logging.getLogger(__name__)


class GitHubOAuth:
    """Handles GitHub OAuth flow for user authentication."""

    def __init__(self):
        self.client_id = os.getenv("GITHUB_OAUTH_CLIENT_ID", "")
        self.client_secret = os.getenv("GITHUB_OAUTH_CLIENT_SECRET", "")
        self.jwt_secret = os.getenv("JWT_SECRET", "development-secret-key")
        
        if not self.client_id or not self.client_secret:
            logger.warning("GitHub OAuth credentials not configured")

    def get_authorization_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Generate GitHub OAuth authorization URL."""
        base_url = "https://github.com/login/oauth/authorize"
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": "user:email read:org",
        }
        
        if state:
            params["state"] = state
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base_url}?{query_string}"

    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        url = "https://github.com/login/oauth/access_token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        }
        
        headers = {
            "Accept": "application/json",
            "User-Agent": "ShieldOps/1.0",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, headers=headers)
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from GitHub API."""
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/json",
            "User-Agent": "ShieldOps/1.0",
        }

        async with httpx.AsyncClient() as client:
            # Get user info
            user_response = await client.get("https://api.github.com/user", headers=headers)
            user_response.raise_for_status()
            user_data = user_response.json()
            
            # Get user email if not public
            if not user_data.get("email"):
                emails_response = await client.get(
                    "https://api.github.com/user/emails", headers=headers
                )
                emails_response.raise_for_status()
                emails = emails_response.json()
                
                # Find primary email
                for email_data in emails:
                    if email_data.get("primary"):
                        user_data["email"] = email_data["email"]
                        break
            
            return user_data

    async def get_user_organizations(self, access_token: str) -> list:
        """Get user's organizations from GitHub API."""
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/json",
            "User-Agent": "ShieldOps/1.0",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.github.com/user/orgs", headers=headers)
            response.raise_for_status()
            return response.json()

    async def create_or_update_user(
        self, 
        user_data: Dict[str, Any], 
        access_token: str,
        db: AsyncSession
    ) -> User:
        """Create or update user in database."""
        github_user_id = user_data["id"]
        login = user_data["login"]
        email = user_data.get("email")
        avatar_url = user_data.get("avatar_url")
        
        # Get user's organizations
        user_orgs = await self.get_user_organizations(access_token)
        user_org_ids = {org["id"] for org in user_orgs}
        
        # Find which of our tracked organizations the user belongs to
        result = await db.execute(
            select(Organization).where(Organization.github_org_id.in_(user_org_ids))
        )
        matching_orgs = result.scalars().all()
        
        if not matching_orgs:
            raise ValueError("User is not a member of any ShieldOps-enabled organization")
        
        # Use the first matching organization (in practice, most users belong to one org)
        org = matching_orgs[0]
        
        # Check if user already exists
        result = await db.execute(
            select(User).where(User.github_user_id == github_user_id)
        )
        user = result.scalars().first()
        
        if user:
            # Update existing user
            user.login = login
            user.email = email
            user.avatar_url = avatar_url
            user.last_login_at = datetime.utcnow()
            # Update organization if it changed
            user.org_id = org.id
            logger.info(f"Updated user {login} (ID: {github_user_id})")
        else:
            # Create new user (default role is VIEWER)
            user = User(
                github_user_id=github_user_id,
                login=login,
                email=email,
                avatar_url=avatar_url,
                org_id=org.id,
                last_login_at=datetime.utcnow(),
            )
            db.add(user)
            logger.info(f"Created user {login} (ID: {github_user_id})")
        
        await db.commit()
        return user

    def generate_jwt_token(self, user: User) -> str:
        """Generate JWT session token for user."""
        payload = {
            "user_id": str(user.id),
            "github_user_id": user.github_user_id,
            "login": user.login,
            "org_id": str(user.org_id),
            "role": user.role.value,
            "exp": datetime.utcnow() + timedelta(days=7),  # Token expires in 7 days
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None

    async def get_current_user(self, token: str, db: AsyncSession) -> Optional[User]:
        """Get current user from JWT token."""
        payload = self.verify_jwt_token(token)
        if not payload:
            return None
        
        user_id = payload.get("user_id")
        if not user_id:
            return None
        
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalars().first()


def get_github_oauth() -> GitHubOAuth:
    """Get GitHub OAuth instance."""
    return GitHubOAuth()