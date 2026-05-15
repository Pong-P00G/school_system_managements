"""Comprehensive API tests for the staff endpoint (CRUD + filters)."""

from __future__ import annotations

import uuid

import pytest

from .helpers import (
    create_department,
    create_staff,
    register_user,
    _short,
)

BASE_SUFFIX = uuid.uuid4().hex[:6]


async def _setup_staff_graph(client, suffix: str):
    """Create a user + staff profile."""
    user = await register_user(client, f"{suffix}_u")
    staff = await create_staff(client, f"{suffix}_s", user["user_id"])
    return {
        "user_id": user["user_id"],
        "staff_id": staff["staff_id"],
        "username": user["username"],
    }


@pytest.mark.asyncio
async def test_create_staff(client):
    """Create a staff profile."""
    graph = await _setup_staff_graph(client, f"sc_{BASE_SUFFIX}")
    resp = await client.get(f"/api/v1/staff/{graph['staff_id']}")
    assert resp.status_code == 200
    assert resp.json()["employment_status"] == "active"


@pytest.mark.asyncio
async def test_list_staff(client):
    """List staff returns paginated results."""
    await _setup_staff_graph(client, f"sl_{BASE_SUFFIX}")
    resp = await client.get("/api/v1/staff/")
    assert resp.status_code == 200
    data = resp.json()
    assert "staff" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_staff(client):
    """Get a staff member by ID."""
    graph = await _setup_staff_graph(client, f"sg_{BASE_SUFFIX}")
    resp = await client.get(f"/api/v1/staff/{graph['staff_id']}")
    assert resp.status_code == 200
    assert resp.json()["staff_id"] == str(graph["staff_id"])


@pytest.mark.asyncio
async def test_get_staff_not_found(client):
    """Get a non-existent staff returns 404."""
    resp = await client.get("/api/v1/staff/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_staff(client):
    """Update a staff member."""
    graph = await _setup_staff_graph(client, f"su_{BASE_SUFFIX}")
    resp = await client.put(
        f"/api/v1/staff/{graph['staff_id']}",
        json={"job_title": "Senior Administrator", "employment_status": "on_leave"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_title"] == "Senior Administrator"
    assert data["employment_status"] == "on_leave"


@pytest.mark.asyncio
async def test_delete_staff(client):
    """Delete a staff member."""
    graph = await _setup_staff_graph(client, f"sd_{BASE_SUFFIX}")
    resp = await client.delete(f"/api/v1/staff/{graph['staff_id']}")
    assert resp.status_code == 204

    get_resp = await client.get(f"/api/v1/staff/{graph['staff_id']}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_staff_invalid_user(client):
    """Creating staff with non-existent user returns 404."""
    resp = await client.post("/api/v1/staff/", json={
        "user_id": "00000000-0000-0000-0000-000000000000",
        "employee_number": f"en{_short()}",
        "hire_date": "2025-01-15",
        "job_title": "Admin",
        "job_category": "Administrative",
        "employment_type": "full_time",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_staff_duplicate_employee_number(client):
    """Creating staff with duplicate employee number returns 409."""
    graph = await _setup_staff_graph(client, f"sn_{BASE_SUFFIX}")
    resp = await client.get(f"/api/v1/staff/{graph['staff_id']}")
    emp_num = resp.json()["employee_number"]

    user2 = await register_user(client, f"sn_{BASE_SUFFIX}_2")
    resp = await client.post("/api/v1/staff/", json={
        "user_id": str(user2["user_id"]),
        "employee_number": emp_num,
        "hire_date": "2025-01-15",
        "job_title": "Admin",
        "job_category": "Administrative",
        "employment_type": "full_time",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_staff_with_department(client):
    """Create a staff member with a department."""
    dept = await create_department(client, f"swd_{BASE_SUFFIX}")
    user = await register_user(client, f"swd_{BASE_SUFFIX}")
    resp = await client.post("/api/v1/staff/", json={
        "user_id": str(user["user_id"]),
        "employee_number": f"en{_short()}",
        "department_id": dept["department_id"],
        "hire_date": "2025-01-15",
        "job_title": "Department Assistant",
        "job_category": "Administrative",
        "employment_type": "full_time",
    })
    assert resp.status_code == 201
    assert resp.json()["department_id"] == dept["department_id"]


@pytest.mark.asyncio
async def test_list_staff_filters(client):
    """List staff supports filters."""
    await _setup_staff_graph(client, f"sf_{BASE_SUFFIX}")

    resp = await client.get("/api/v1/staff/?employment_status=active")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1

    resp = await client.get("/api/v1/staff/?job_category=Administrative")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_pagination(client):
    """Staff list respects pagination."""
    resp = await client.get("/api/v1/staff/?skip=0&limit=5")
    assert resp.status_code == 200
    assert len(resp.json()["staff"]) <= 5
