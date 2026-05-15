"""Comprehensive API tests for the faculty endpoint (CRUD + /me + sub-resources)."""

from __future__ import annotations

import uuid

import pytest

from .helpers import (
    create_course,
    create_department,
    create_faculty,
    create_section,
    create_term,
    login_user,
    register_user,
    _short,
)

BASE_SUFFIX = uuid.uuid4().hex[:6]


async def _setup_faculty_graph(client, suffix: str):
    """Create a department + user + faculty."""
    dept = await create_department(client, f"{suffix}_d")
    user = await register_user(client, f"{suffix}_u")
    faculty = await create_faculty(client, f"{suffix}_f", user["user_id"], dept["department_id"])
    return {
        "dept_id": dept["department_id"],
        "user_id": user["user_id"],
        "faculty_id": faculty["faculty_id"],
        "username": user["username"],
    }


@pytest.mark.asyncio
async def test_create_faculty(client):
    """Create a faculty profile."""
    graph = await _setup_faculty_graph(client, f"fc_{BASE_SUFFIX}")
    resp = await client.get(f"/api/v1/faculty/{graph['faculty_id']}")
    assert resp.status_code == 200
    assert resp.json()["employment_status"] == "active"


@pytest.mark.asyncio
async def test_list_faculty(client):
    """List faculty returns paginated results."""
    await _setup_faculty_graph(client, f"fl_{BASE_SUFFIX}")
    resp = await client.get("/api/v1/faculty/")
    assert resp.status_code == 200
    data = resp.json()
    assert "faculty" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_faculty(client):
    """Get a faculty member by ID."""
    graph = await _setup_faculty_graph(client, f"fg_{BASE_SUFFIX}")
    resp = await client.get(f"/api/v1/faculty/{graph['faculty_id']}")
    assert resp.status_code == 200
    assert resp.json()["faculty_id"] == str(graph["faculty_id"])


@pytest.mark.asyncio
async def test_get_faculty_not_found(client):
    """Get a non-existent faculty returns 404."""
    resp = await client.get("/api/v1/faculty/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_faculty(client):
    """Update a faculty member."""
    graph = await _setup_faculty_graph(client, f"fu_{BASE_SUFFIX}")
    resp = await client.put(
        f"/api/v1/faculty/{graph['faculty_id']}",
        json={"faculty_rank": "Professor", "employment_status": "on_leave"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["faculty_rank"] == "Professor"
    assert data["employment_status"] == "on_leave"


@pytest.mark.asyncio
async def test_delete_faculty(client):
    """Delete a faculty member."""
    graph = await _setup_faculty_graph(client, f"fd_{BASE_SUFFIX}")
    resp = await client.delete(f"/api/v1/faculty/{graph['faculty_id']}")
    assert resp.status_code == 204

    get_resp = await client.get(f"/api/v1/faculty/{graph['faculty_id']}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_faculty_invalid_user(client):
    """Creating faculty with non-existent user returns 404."""
    dept = await create_department(client, f"fi_{BASE_SUFFIX}")
    resp = await client.post("/api/v1/faculty/", json={
        "user_id": "00000000-0000-0000-0000-000000000000",
        "employee_number": f"en{_short()}",
        "department_id": dept["department_id"],
        "hire_date": "2025-01-15",
        "faculty_rank": "Assistant Professor",
        "tenure_status": "tenure_track",
        "employment_type": "full_time",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_faculty_duplicate_employee_number(client):
    """Creating faculty with duplicate employee number returns 409."""
    graph = await _setup_faculty_graph(client, f"fn_{BASE_SUFFIX}")
    # Get the employee number
    resp = await client.get(f"/api/v1/faculty/{graph['faculty_id']}")
    emp_num = resp.json()["employee_number"]

    user2 = await register_user(client, f"fn_{BASE_SUFFIX}_2")
    resp = await client.post("/api/v1/faculty/", json={
        "user_id": str(user2["user_id"]),
        "employee_number": emp_num,
        "department_id": graph["dept_id"],
        "hire_date": "2025-01-15",
        "faculty_rank": "Assistant Professor",
        "tenure_status": "tenure_track",
        "employment_type": "full_time",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_faculty_my_profile(client):
    """Get current user's faculty profile via /me."""
    graph = await _setup_faculty_graph(client, f"fm_{BASE_SUFFIX}")
    token_data = await login_user(client, graph["username"])
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}

    resp = await client.get("/api/v1/faculty/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["faculty_id"] == str(graph["faculty_id"])


@pytest.mark.asyncio
async def test_get_faculty_my_sections(client):
    """Get current user's sections via /me/sections."""
    graph = await _setup_faculty_graph(client, f"fs_{BASE_SUFFIX}")

    # Create a section assigned to this faculty
    course = await create_course(client, f"fs_{BASE_SUFFIX}_c", graph["dept_id"])
    term = await create_term(client, f"fs_{BASE_SUFFIX}_t")
    await create_section(
        client, f"fs_{BASE_SUFFIX}_s", course["course_id"], term["term_id"],
        instructor_id=graph["user_id"],
    )

    token_data = await login_user(client, graph["username"])
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}

    resp = await client.get("/api/v1/faculty/me/sections", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "sections" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_faculty_sections(client):
    """Get sections for a specific faculty member."""
    graph = await _setup_faculty_graph(client, f"fx_{BASE_SUFFIX}")
    course = await create_course(client, f"fx_{BASE_SUFFIX}_c", graph["dept_id"])
    term = await create_term(client, f"fx_{BASE_SUFFIX}_t")
    await create_section(
        client, f"fx_{BASE_SUFFIX}_s", course["course_id"], term["term_id"],
        instructor_id=graph["user_id"],
    )

    resp = await client.get(f"/api/v1/faculty/{graph['faculty_id']}/sections")
    assert resp.status_code == 200
    data = resp.json()
    assert "sections" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_faculty_assignments(client):
    """Get assignments for a faculty member."""
    graph = await _setup_faculty_graph(client, f"fa_{BASE_SUFFIX}")
    resp = await client.get(f"/api/v1/faculty/{graph['faculty_id']}/assignments")
    assert resp.status_code == 200
    data = resp.json()
    assert "assignments" in data


@pytest.mark.asyncio
async def test_list_faculty_filters(client):
    """List faculty supports filters."""
    await _setup_faculty_graph(client, f"ff_{BASE_SUFFIX}")
    resp = await client.get("/api/v1/faculty/?employment_status=active")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_pagination(client):
    """Faculty list respects pagination."""
    resp = await client.get("/api/v1/faculty/?skip=0&limit=5")
    assert resp.status_code == 200
    assert len(resp.json()["faculty"]) <= 5
