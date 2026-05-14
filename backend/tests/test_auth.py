"""Regression tests for authentication endpoints."""

import uuid

import pytest
from sqlalchemy import select

from app.core.database import async_session
from app.models.user import User


@pytest.mark.asyncio
async def test_register_creates_user_and_rejects_duplicates(client):
    """Register should create a user and block duplicate username/email reuse."""
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "username": f"pytest_{suffix}",
        "email": f"pytest_{suffix}@example.com",
        "password": "Password123",
    }

    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert data["is_active"] is True
    assert data["is_verified"] is False

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.username == payload["username"])
        )
        created_user = result.scalar_one_or_none()
        assert created_user is not None

    duplicate_response = await client.post("/api/v1/auth/register", json=payload)
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"] == "Username or email already registered"
