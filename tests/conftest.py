"""Test fixtures and configuration."""

import asyncio
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.db.database import Base
from src.db.models import Organization, Repository, User, UserRole, PlanType
from trigger import app

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_shieldops.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine):
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def test_client():
    """Create test HTTP client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def test_org(test_session):
    """Create test organization."""
    org = Organization(
        github_org_id=12345,
        name="Test Organization",
        slug="test-org",
        avatar_url="https://example.com/avatar.png",
        installation_id=67890,
        plan=PlanType.PRO,
    )
    test_session.add(org)
    await test_session.commit()
    await test_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def test_repo(test_session, test_org):
    """Create test repository."""
    repo = Repository(
        org_id=test_org.id,
        github_repo_id=11111,
        full_name="test-org/test-repo",
        default_branch="main",
        is_active=True,
    )
    test_session.add(repo)
    await test_session.commit()
    await test_session.refresh(repo)
    return repo


@pytest_asyncio.fixture
async def test_user(test_session, test_org):
    """Create test user."""
    user = User(
        github_user_id=22222,
        login="testuser",
        email="test@example.com",
        avatar_url="https://example.com/user.png",
        role=UserRole.ADMIN,
        org_id=test_org.id,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
def mock_github_api(monkeypatch):
    """Mock GitHub API responses."""
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code
        
        def json(self):
            return self.json_data
        
        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")
    
    async def mock_request(*args, **kwargs):
        # Return mock responses based on URL
        url = args[1] if len(args) > 1 else kwargs.get("url", "")
        
        if "installations" in url:
            return MockResponse([{
                "id": 67890,
                "account": {"id": 12345, "login": "test-org"},
            }])
        elif "access_tokens" in url:
            return MockResponse({
                "token": "test-token",
                "expires_at": "2024-12-31T23:59:59Z",
            })
        elif "user" in url:
            return MockResponse({
                "id": 22222,
                "login": "testuser",
                "email": "test@example.com",
                "avatar_url": "https://example.com/user.png",
            })
        elif "orgs" in url:
            return MockResponse([{
                "id": 12345,
                "login": "test-org",
            }])
        else:
            return MockResponse({})
    
    import httpx
    monkeypatch.setattr(httpx.AsyncClient, "request", mock_request)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock_request)
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_request)


def pytest_configure():
    """Configure pytest."""
    # Set test environment variables
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["JWT_SECRET"] = "test-secret"
    os.environ["GITHUB_OAUTH_CLIENT_ID"] = "test-client-id"
    os.environ["GITHUB_OAUTH_CLIENT_SECRET"] = "test-client-secret"