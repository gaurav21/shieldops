"""Authentication middleware and utilities."""

import logging
from typing import Optional, Dict, Any
from functools import wraps
from fastapi import HTTPException, Request, Depends, Cookie, Header
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db_session
from ..db.models import User, UserRole
from ..github_app.oauth import get_github_oauth

logger = logging.getLogger(__name__)


class AuthContext:
    """Authentication context for the current request."""
    
    def __init__(self, user: User):
        self.user = user
        self.org_id = user.org_id
        self.role = user.role

    def has_role(self, required_role: UserRole) -> bool:
        """Check if user has required role or higher."""
        role_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.REVIEWER: 2,
            UserRole.ADMIN: 3,
        }
        return role_hierarchy.get(self.user.role, 0) >= role_hierarchy.get(required_role, 0)

    def require_role(self, required_role: UserRole) -> None:
        """Require user to have a specific role."""
        if not self.has_role(required_role):
            raise HTTPException(
                status_code=403,
                detail=f"Requires {required_role.value} role or higher"
            )


async def get_auth_token(
    request: Request,
    authorization: Optional[str] = Header(None),
    session_token: Optional[str] = Cookie(None),
) -> Optional[str]:
    """Extract auth token from Authorization header or cookie."""
    # Try Authorization header first
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    
    # Fall back to session cookie
    if session_token:
        return session_token
    
    return None


async def get_current_user(
    token: Optional[str] = Depends(get_auth_token),
    db: AsyncSession = Depends(get_db_session)
) -> Optional[User]:
    """Get current authenticated user (optional)."""
    if not token:
        return None
    
    oauth = get_github_oauth()
    return await oauth.get_current_user(token, db)


async def require_auth(
    token: Optional[str] = Depends(get_auth_token),
    db: AsyncSession = Depends(get_db_session)
) -> AuthContext:
    """Require authentication and return auth context."""
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    oauth = get_github_oauth()
    user = await oauth.get_current_user(token, db)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    return AuthContext(user)


def require_role(required_role: UserRole):
    """Decorator to require a specific role."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract auth context from function arguments
            auth_context = None
            for arg in args:
                if isinstance(arg, AuthContext):
                    auth_context = arg
                    break
            
            # Look in kwargs
            if not auth_context:
                auth_context = kwargs.get("auth")
            
            if not auth_context:
                raise HTTPException(
                    status_code=500,
                    detail="Auth context not found"
                )
            
            auth_context.require_role(required_role)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Convenience dependencies for different roles
async def require_viewer_auth(
    auth: AuthContext = Depends(require_auth)
) -> AuthContext:
    """Require viewer role or higher."""
    auth.require_role(UserRole.VIEWER)
    return auth


async def require_reviewer_auth(
    auth: AuthContext = Depends(require_auth)
) -> AuthContext:
    """Require reviewer role or higher."""
    auth.require_role(UserRole.REVIEWER)
    return auth


async def require_admin_auth(
    auth: AuthContext = Depends(require_auth)
) -> AuthContext:
    """Require admin role."""
    auth.require_role(UserRole.ADMIN)
    return auth