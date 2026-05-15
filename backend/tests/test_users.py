"""Comprehensive API tests for the users endpoint (CRUD + roles + personal info)."""

from __future__ import annotations

import uuid

import pytest

from .helpers import (
    login_user,
    register_user,
    _short,
)

BASE_SUFFIX = uuid.uuid4().hex[:6]


@pytest.mark.asyncio
async def test_create_user(client):
    """Create a user successfully."""
    payload = {
        "username": f"uc_{BASE_SUFFIX}",
        "email": f"uc_{BASE_SUFFIX}@test.com",
        "password": "Password123",
    }
    resp = await client.post("/api/v1/users/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert data["is_active"] is True
    assert "password" not in data  # password should never be returned


@pytest.mark.asyncio
async def test_list_users(client):
    """List users returns paginated results."""
    await register_user(client, f"ul_{BASE_SUFFIX}")
    resp = await client.get("/api/v1/users/")
    assert resp.status_code == 200
    data = resp.json()
    assert "users" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_user(client):
    """Get a user by ID."""
    user = await register_user(client, f"ug_{BASE_SUFFIX}")
    resp = await client.get(f"/api/v1/users/{user['user_id']}")
    assert resp.status_code == 200
    assert resp.json()["user_id"] == str(user["user_id"])


@pytest.mark.asyncio
async def test_get_user_not_found(client):
    """Get a non-existent user returns 404."""
    resp = await client.get("/api/v1/users/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_me(client):
    """Get the currently logged-in user's details."""
    user = await register_user(client, f"gm_{BASE_SUFFIX}")
    token = await login_user(client, user["username"])
    headers = {"Authorization": f"Bearer {token['access_token']}"}

    resp = await client.get("/api/v1/users/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["user_id"] == str(user["user_id"])


@pytest.mark.asyncio
async def test_update_user(client):
    """Update a user."""
    user = await register_user(client, f"uu_{BASE_SUFFIX}")
    resp = await client.put(
        f"/api/v1/users/{user['user_id']}",
        json={"email": f"updated_{BASE_SUFFIX}@test.com"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == f"updated_{BASE_SUFFIX}@test.com"


@pytest.mark.asyncio
async def test_delete_user_soft(client):
    """Delete (soft delete) a user."""
    user = await register_user(client, f"ud_{BASE_SUFFIX}")
    resp = await client.delete(f"/api/v1/users/{user['user_id']}")
    assert resp.status_code == 204

    get_resp = await client.get(f"/api/v1/users/{user['user_id']}")
    assert get_resp.json()["is_active"] is False


@pytest.mark.asyncio
async def test_create_user_duplicate_username(client):
    """Creating a user with duplicate username returns 409."""
    user = await register_user(client, f"ux_{BASE_SUFFIX}")
    resp = await client.post("/api/v1/users/", json={
        "username": user["username"],
        "email": f"other_{BASE_SUFFIX}@test.com",
        "password": "Password123",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client):
    """Creating a user with duplicate email returns 409."""
    user = await register_user(client, f"ue_{BASE_SUFFIX}")
    resp = await client.post("/api/v1/users/", json={
        "username": f"other_{BASE_SUFFIX}",
        "email": user["email"],
        "password": "Password123",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_users_filters(client):
    """List users supports filters."""
    await register_user(client, f"uf_{BASE_SUFFIX}")
    resp = await client.get("/api/v1/users/?is_active=true")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_create_user_personal_info(client):
    """Create personal info for a user."""
    user = await register_user(client, f"pi_{BASE_SUFFIX}")
    resp = await client.post(
        f"/api/v1/users/{user['user_id']}/personal-info",
        json={
            "first_name": "John",
            "last_name": "Doe",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"


@pytest.mark.asyncio
async def test_update_user_personal_info(client):
    """Update personal info for a user."""
    user = await register_user(client, f"pu_{BASE_SUFFIX}")
    resp = await client.put(
        f"/api/v1/users/{user['user_id']}/personal-info",
        json={
            "first_name": "Jane",
            "last_name": "Smith",
        },
    )
    assert resp.status_code == 200 or resp.status_code == 201
    data = resp.json()
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Smith"


@pytest.mark.asyncio
async def test_list_roles(client):
    """List available user roles."""
    resp = await client.get("/api/v1/users/roles")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_assign_role_to_user(client):
    """Assign a role to a user."""
    user = await register_user(client, f"ar_{BASE_SUFFIX}")
    roles_resp = await client.get("/api/v1/users/roles")
    roles = roles_resp.json()
    if roles:
        role_id = roles[0]["role_id"]
        resp = await client.post(
            f"/api/v1/users/{user['user_id']}/roles/{role_id}",
        )
        assert resp.status_code == 201


@pytest.mark.asyncio
async def test_pagination(client):
    """Users list respects pagination."""
    resp = await client.get("/api/v1/users/?skip=0&limit=5")
    assert resp.status_code == 200
    assert len(resp.json()["users"]) <= 5
