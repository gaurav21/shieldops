"""Tests for authentication middleware."""

import pytest
import pytest_asyncio
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

from src.api.auth import AuthContext, require_auth, get_auth_token, get_current_user
from src.github_app.oauth import GitHubOAuth
from src.db.models import UserRole
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_auth_context_role_hierarchy(test_user):
    """Test AuthContext role hierarchy checking."""
    auth = AuthContext(test_user)
    
    # Admin should have all permissions
    test_user.role = UserRole.ADMIN
    assert auth.has_role(UserRole.VIEWER)
    assert auth.has_role(UserRole.REVIEWER) 
    assert auth.has_role(UserRole.ADMIN)
    
    # Reviewer should have viewer permissions
    test_user.role = UserRole.REVIEWER
    assert auth.has_role(UserRole.VIEWER)
    assert auth.has_role(UserRole.REVIEWER)
    assert not auth.has_role(UserRole.ADMIN)
    
    # Viewer should only have viewer permissions
    test_user.role = UserRole.VIEWER
    assert auth.has_role(UserRole.VIEWER)
    assert not auth.has_role(UserRole.REVIEWER)
    assert not auth.has_role(UserRole.ADMIN)


@pytest.mark.asyncio
async def test_auth_context_require_role(test_user):
    """Test AuthContext role requirement."""
    auth = AuthContext(test_user)
    test_user.role = UserRole.VIEWER
    
    # Should pass for viewer role
    auth.require_role(UserRole.VIEWER)
    
    # Should fail for higher roles
    with pytest.raises(HTTPException) as exc_info:
        auth.require_role(UserRole.ADMIN)
    
    assert exc_info.value.status_code == 403
    assert "admin role" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_github_oauth_jwt_token(test_user):
    """Test JWT token generation and verification."""
    oauth = GitHubOAuth()
    
    # Generate token
    token = oauth.generate_jwt_token(test_user)
    assert token is not None
    
    # Verify token
    payload = oauth.verify_jwt_token(token)
    assert payload is not None
    assert payload["user_id"] == str(test_user.id)
    assert payload["login"] == test_user.login
    assert payload["role"] == test_user.role.value
    
    # Test expired token
    expired_payload = {
        "user_id": str(test_user.id),
        "exp": datetime.utcnow() - timedelta(hours=1),
    }
    expired_token = jwt.encode(expired_payload, oauth.jwt_secret, algorithm="HS256")
    
    invalid_payload = oauth.verify_jwt_token(expired_token)
    assert invalid_payload is None


@pytest.mark.asyncio
async def test_get_auth_token_from_header():
    """Test token extraction from Authorization header."""
    from fastapi import Request
    
    # Mock request with Authorization header
    request = AsyncMock()
    request.headers = {"Authorization": "Bearer test-token-123"}
    
    token = await get_auth_token(request, authorization="Bearer test-token-123")
    assert token == "test-token-123"


@pytest.mark.asyncio
async def test_get_auth_token_from_cookie():
    """Test token extraction from cookie."""
    from fastapi import Request
    
    # Mock request without Authorization header but with cookie
    request = AsyncMock()
    request.headers = {}
    
    token = await get_auth_token(request, authorization=None, session_token="cookie-token-456")
    assert token == "cookie-token-456"


@pytest.mark.asyncio
async def test_get_current_user_valid_token(test_session, test_user):
    """Test getting current user with valid token."""
    oauth = GitHubOAuth()
    token = oauth.generate_jwt_token(test_user)
    
    with patch("src.api.auth.get_github_oauth", return_value=oauth):
        user = await get_current_user(token, test_session)
        
    assert user is not None
    assert user.id == test_user.id


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(test_session):
    """Test getting current user with invalid token."""
    oauth = GitHubOAuth()
    
    with patch("src.api.auth.get_github_oauth", return_value=oauth):
        user = await get_current_user("invalid-token", test_session)
        
    assert user is None


@pytest.mark.asyncio
async def test_require_auth_success(test_session, test_user):
    """Test successful authentication requirement."""
    oauth = GitHubOAuth()
    token = oauth.generate_jwt_token(test_user)
    
    with patch("src.api.auth.get_github_oauth", return_value=oauth):
        auth_context = await require_auth(token, test_session)
        
    assert isinstance(auth_context, AuthContext)
    assert auth_context.user.id == test_user.id
    assert auth_context.org_id == test_user.org_id


@pytest.mark.asyncio
async def test_require_auth_no_token(test_session):
    """Test authentication requirement without token."""
    with pytest.raises(HTTPException) as exc_info:
        await require_auth(None, test_session)
    
    assert exc_info.value.status_code == 401
    assert "Authentication required" in exc_info.value.detail


@pytest.mark.asyncio
async def test_require_auth_invalid_token(test_session):
    """Test authentication requirement with invalid token."""
    oauth = GitHubOAuth()
    
    with patch("src.api.auth.get_github_oauth", return_value=oauth):
        with pytest.raises(HTTPException) as exc_info:
            await require_auth("invalid-token", test_session)
    
    assert exc_info.value.status_code == 401
    assert "Invalid or expired token" in exc_info.value.detail