"""Comprehensive API tests for the departments endpoint (CRUD + filters + sub-resources)."""

from __future__ import annotations

import uuid

import pytest

from .helpers import (
    create_course,
    create_department,
    create_program,
    create_term,
    _short,
)

BASE_SUFFIX = uuid.uuid4().hex[:6]


@pytest.mark.asyncio
async def test_create_department(client):
    """Create a department successfully."""
    code = f"d{_short()}"
    resp = await client.post("/api/v1/departments/", json={
        "department_code": code,
        "department_name": f"Test Dept {BASE_SUFFIX}",
        "is_active": True,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["department_code"] == code
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_departments(client):
    """List departments returns paginated results."""
    await create_department(client, f"dl_{BASE_SUFFIX}")
    resp = await client.get("/api/v1/departments/")
    assert resp.status_code == 200
    data = resp.json()
    assert "departments" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_department(client):
    """Get a department by ID."""
    dept = await create_department(client, f"dg_{BASE_SUFFIX}")
    resp = await client.get(f"/api/v1/departments/{dept['department_id']}")
    assert resp.status_code == 200
    assert resp.json()["department_id"] == dept["department_id"]


@pytest.mark.asyncio
async def test_get_department_not_found(client):
    """Get a non-existent department returns 404."""
    resp = await client.get("/api/v1/departments/99999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_department(client):
    """Update a department."""
    dept = await create_department(client, f"du_{BASE_SUFFIX}")
    new_name = f"Updated Dept {_short()}"
    resp = await client.put(
        f"/api/v1/departments/{dept['department_id']}",
        json={"department_name": new_name},
    )
    assert resp.status_code == 200
    assert resp.json()["department_name"] == new_name


@pytest.mark.asyncio
async def test_delete_department_soft(client):
    """Delete a department (hard delete)."""
    dept = await create_department(client, f"dd_{BASE_SUFFIX}")
    resp = await client.delete(f"/api/v1/departments/{dept['department_id']}")
    assert resp.status_code == 204

    # Verify it's actually deleted
    get_resp = await client.get(f"/api/v1/departments/{dept['department_id']}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_department_duplicate_code(client):
    """Creating a department with duplicate code returns 409."""
    code = f"dx{_short()}"
    await create_department(client, f"dx_{BASE_SUFFIX}", department_code=code)
    resp = await client.post("/api/v1/departments/", json={
        "department_code": code,
        "department_name": "Duplicate Dept",
        "is_active": True,
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_departments_filters(client):
    """List departments supports search and is_active filters."""
    await create_department(client, f"df_{BASE_SUFFIX}")
    resp = await client.get(f"/api/v1/departments/?search=Dept&is_active=true")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_get_department_courses(client):
    """Get courses for a department."""
    dept = await create_department(client, f"dc_{BASE_SUFFIX}")
    await create_course(client, f"dc_{BASE_SUFFIX}", dept["department_id"])
    resp = await client.get(f"/api/v1/departments/{dept['department_id']}/courses")
    assert resp.status_code == 200
    data = resp.json()
    assert "courses" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_department_programs(client):
    """Get programs for a department."""
    dept = await create_department(client, f"dp_{BASE_SUFFIX}")
    await create_program(client, f"dp_{BASE_SUFFIX}", dept["department_id"])
    resp = await client.get(f"/api/v1/departments/{dept['department_id']}/programs")
    assert resp.status_code == 200
    data = resp.json()
    assert "programs" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_department_courses_not_found(client):
    """Getting courses for non-existent department returns 404."""
    resp = await client.get("/api/v1/departments/99999999/courses")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_pagination(client):
    """Departments list respects skip/limit pagination."""
    resp = await client.get("/api/v1/departments/?skip=0&limit=5")
    assert resp.status_code == 200
    assert len(resp.json()["departments"]) <= 5


@pytest.mark.asyncio
async def test_delete_department_with_courses_returns_409(client):
    """Deleting a department that still has courses returns 409."""
    dept = await create_department(client, f"dc409_{BASE_SUFFIX}")
    await create_course(client, f"dc409_{BASE_SUFFIX}", dept["department_id"])

    resp = await client.delete(f"/api/v1/departments/{dept['department_id']}")
    assert resp.status_code == 409
    assert "course(s)" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_department_with_programs_returns_409(client):
    """Deleting a department that still has programs returns 409."""
    dept = await create_department(client, f"dp409_{BASE_SUFFIX}")
    await create_program(client, f"dp409_{BASE_SUFFIX}", dept["department_id"])

    resp = await client.delete(f"/api/v1/departments/{dept['department_id']}")
    assert resp.status_code == 409
    assert "program(s)" in resp.json()["detail"].lower()
