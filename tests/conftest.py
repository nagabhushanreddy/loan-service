"""Test configuration and fixtures"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from app.auth import AuthenticatedUser
from app.models.enums import UserRole


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_user() -> AuthenticatedUser:
    """Create test authenticated user"""
    return AuthenticatedUser(
        user_id="test-user-123",
        tenant_id="test-tenant-456",
        roles=["customer", "loan_officer"],
        email="test@example.com"
    )


@pytest.fixture
def admin_user() -> AuthenticatedUser:
    """Create test admin user"""
    return AuthenticatedUser(
        user_id="admin-user-999",
        tenant_id="test-tenant-456",
        roles=["admin", "checker"],
        email="admin@example.com"
    )
