"""GitHub App authentication utilities."""

import os
import time
from typing import Dict, Optional
import jwt
import httpx
import logging

logger = logging.getLogger(__name__)


class GitHubAppAuth:
    """Handles GitHub App authentication and installation tokens."""

    def __init__(self, app_id: str, private_key: str):
        self.app_id = app_id
        self.private_key = private_key
        self._installation_tokens: Dict[int, Dict] = {}

    def generate_jwt(self) -> str:
        """Generate a JWT token for GitHub App authentication."""
        now = int(time.time())
        payload = {
            "iat": now - 10,  # Issued 10 seconds ago to avoid clock skew
            "exp": now + 600,  # Expires in 10 minutes
            "iss": self.app_id,
        }
        return jwt.encode(payload, self.private_key, algorithm="RS256")

    async def get_installation_token(self, installation_id: int, force_refresh: bool = False) -> str:
        """Get access token for a specific installation, with caching."""
        # Check cache
        if not force_refresh and installation_id in self._installation_tokens:
            token_data = self._installation_tokens[installation_id]
            expires_at = token_data.get("expires_at", 0)
            # Refresh if token expires in less than 5 minutes
            if time.time() < expires_at - 300:
                return token_data["token"]

        # Fetch new token
        jwt_token = self.generate_jwt()
        url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ShieldOps/1.0",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            token = data["token"]
            expires_at = data["expires_at"]
            
            # Parse expires_at and convert to timestamp
            import datetime
            expires_dt = datetime.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            expires_timestamp = expires_dt.timestamp()
            
            # Cache the token
            self._installation_tokens[installation_id] = {
                "token": token,
                "expires_at": expires_timestamp,
            }
            
            logger.info(f"Generated new installation token for installation {installation_id}")
            return token

    async def get_app_installations(self) -> list:
        """Get all installations for this GitHub App."""
        jwt_token = self.generate_jwt()
        url = "https://api.github.com/app/installations"
        
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ShieldOps/1.0",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    async def make_installation_request(
        self, 
        installation_id: int, 
        method: str, 
        path: str, 
        **kwargs
    ) -> httpx.Response:
        """Make an authenticated request using an installation token."""
        token = await self.get_installation_token(installation_id)
        headers = kwargs.get("headers", {})
        headers.update({
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ShieldOps/1.0",
        })
        kwargs["headers"] = headers

        url = f"https://api.github.com{path}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, **kwargs)
            return response


def get_github_app_auth() -> Optional[GitHubAppAuth]:
    """Get GitHub App auth instance from environment variables."""
    app_id = os.getenv("GITHUB_APP_ID")
    private_key = os.getenv("GITHUB_APP_PRIVATE_KEY")
    
    if not app_id or not private_key:
        logger.warning("GitHub App credentials not configured")
        return None
    
    # Handle private key format (replace \\n with actual newlines)
    private_key = private_key.replace("\\n", "\n")
    
    return GitHubAppAuth(app_id, private_key)