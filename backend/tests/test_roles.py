"""Tests for the Roles management API endpoints (/api/v1/roles/).

All endpoints require admin privileges.
Note: The database enforces a CHECK constraint (chk_role_name) limiting
role_name to a fixed set: student, faculty, staff, admin, librarian,
registrar, finance_officer, researcher. All 8 are seeded as system roles,
so create/delete of arbitrary roles is not possible through the API.
"""

from __future__ import annotations

import uuid

import pytest

from .helpers import login_user, register_user


def _headers(user: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {user['token']}"}


def _short() -> str:
    return uuid.uuid4().hex[:4]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _admin_user(client, suffix: str) -> dict:
    """Register a user and assign the admin role, returning user + token."""
    suffix = f"{suffix}_{_short()}"
    user = await register_user(client, f"{suffix}_admin")
    # Fetch roles via public endpoint and assign admin role
    resp = await client.get("/api/v1/users/roles")
    assert resp.status_code == 200, resp.text
    roles = resp.json()
    admin_role = next(r for r in roles if r["role_name"] == "admin")
    assign = await client.post(f"/api/v1/users/{user['user_id']}/roles/{admin_role['role_id']}")
    assert assign.status_code == 201, assign.text
    token_data = await login_user(client, user["username"])
    return {**user, "token": token_data["access_token"]}


async def _non_admin_user(client, suffix: str) -> dict:
    """Register a user with no role assignments."""
    suffix = f"{suffix}_{_short()}"
    user = await register_user(client, f"{suffix}_user")
    token_data = await login_user(client, user["username"])
    return {**user, "token": token_data["access_token"]}


# ===================================================================
# Tests
# ===================================================================


class TestListRoles:
    @pytest.mark.asyncio
    async def test_list_roles(self, client, suffix):
        admin = await _admin_user(client, suffix)
        resp = await client.get("/api/v1/roles/", headers=_headers(admin))
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert isinstance(data, list)
        role_names = {r["role_name"] for r in data}
        assert "admin" in role_names
        assert "student" in role_names

    @pytest.mark.asyncio
    async def test_list_roles_non_admin_returns_403(self, client, suffix):
        user = await _non_admin_user(client, suffix)
        resp = await client.get("/api/v1/roles/", headers=_headers(user))
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_list_roles_unauthenticated_returns_401(self, client):
        resp = await client.get("/api/v1/roles/")
        assert resp.status_code == 401


class TestCreateRole:
    @pytest.mark.asyncio
    async def test_create_role_invalid_name_returns_409(self, client, suffix):
        """Creating a role with a name outside the allowed set fails (check constraint)."""
        admin = await _admin_user(client, suffix)
        payload = {"role_name": f"invalid_role_{_short()}", "description": "Not allowed"}
        resp = await client.post("/api/v1/roles/", json=payload, headers=_headers(admin))
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_create_duplicate_role_returns_409(self, client, suffix):
        """Creating a role with an existing name fails (unique constraint)."""
        admin = await _admin_user(client, suffix)
        payload = {"role_name": "researcher", "description": "Already exists"}
        resp = await client.post("/api/v1/roles/", json=payload, headers=_headers(admin))
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_create_role_non_admin_returns_403(self, client, suffix):
        user = await _non_admin_user(client, suffix)
        payload = {"role_name": "student", "description": "test"}
        resp = await client.post("/api/v1/roles/", json=payload, headers=_headers(user))
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_create_role_unauthenticated_returns_401(self, client):
        payload = {"role_name": "student", "description": "test"}
        resp = await client.post("/api/v1/roles/", json=payload)
        assert resp.status_code == 401


class TestGetRole:
    @pytest.mark.asyncio
    async def test_get_role(self, client, suffix):
        admin = await _admin_user(client, suffix)
        # Get list first to find an ID
        list_resp = await client.get("/api/v1/roles/", headers=_headers(admin))
        roles = list_resp.json()
        role_id = roles[0]["role_id"]

        resp = await client.get(f"/api/v1/roles/{role_id}", headers=_headers(admin))
        assert resp.status_code == 200, resp.text
        assert resp.json()["role_id"] == role_id

    @pytest.mark.asyncio
    async def test_get_role_not_found_returns_404(self, client, suffix):
        admin = await _admin_user(client, suffix)
        resp = await client.get("/api/v1/roles/999999", headers=_headers(admin))
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_role_non_admin_returns_403(self, client, suffix):
        user = await _non_admin_user(client, suffix)
        resp = await client.get("/api/v1/roles/1", headers=_headers(user))
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_get_role_unauthenticated_returns_401(self, client):
        resp = await client.get("/api/v1/roles/1")
        assert resp.status_code == 401


class TestUpdateRole:
    @pytest.mark.asyncio
    async def test_update_role_description(self, client, suffix):
        admin = await _admin_user(client, suffix)
        # Get list first to find an ID
        list_resp = await client.get("/api/v1/roles/", headers=_headers(admin))
        roles = list_resp.json()
        role_id = roles[0]["role_id"]

        resp = await client.put(
            f"/api/v1/roles/{role_id}",
            json={"description": "Updated description"},
            headers=_headers(admin),
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_role_not_found_returns_404(self, client, suffix):
        admin = await _admin_user(client, suffix)
        resp = await client.put(
            "/api/v1/roles/999999",
            json={"description": "nope"},
            headers=_headers(admin),
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_role_non_admin_returns_403(self, client, suffix):
        user = await _non_admin_user(client, suffix)
        resp = await client.put(
            "/api/v1/roles/1",
            json={"description": "nope"},
            headers=_headers(user),
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_update_role_unauthenticated_returns_401(self, client):
        resp = await client.put("/api/v1/roles/1", json={"description": "nope"})
        assert resp.status_code == 401


class TestDeleteRole:
    @pytest.mark.asyncio
    async def test_delete_system_role_returns_400(self, client, suffix):
        """All seeded roles are system roles, so delete should return 400."""
        admin = await _admin_user(client, suffix)
        # Get list to find a role ID
        list_resp = await client.get("/api/v1/roles/", headers=_headers(admin))
        roles = list_resp.json()
        role_id = roles[0]["role_id"]
        resp = await client.delete(f"/api/v1/roles/{role_id}", headers=_headers(admin))
        assert resp.status_code == 400, resp.text
        assert "system" in resp.text.lower()

    @pytest.mark.asyncio
    async def test_delete_role_not_found_returns_404(self, client, suffix):
        admin = await _admin_user(client, suffix)
        resp = await client.delete("/api/v1/roles/999999", headers=_headers(admin))
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_role_non_admin_returns_403(self, client, suffix):
        user = await _non_admin_user(client, suffix)
        resp = await client.delete("/api/v1/roles/1", headers=_headers(user))
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_role_unauthenticated_returns_401(self, client):
        resp = await client.delete("/api/v1/roles/1")
        assert resp.status_code == 401
