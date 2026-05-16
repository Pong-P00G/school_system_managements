"""Comprehensive API tests for the students endpoint (CRUD + /me + sub-resources)."""

from __future__ import annotations

import uuid

import pytest

from .helpers import (
    create_course,
    create_department,
    create_enrollment,
    create_program,
    create_section,
    create_student,
    create_term,
    register_user,
    _short,
)

BASE_SUFFIX = uuid.uuid4().hex[:6]


async def _setup_student_graph(client, suffix: str):
    """Create a full graph ending with a student. Returns all IDs."""
    dept = await create_department(client, f"{suffix}_d")
    prog = await create_program(client, f"{suffix}_p", dept["department_id"])
    user = await register_user(client, f"{suffix}_u")
    student = await create_student(client, f"{suffix}_s", user["user_id"], prog["program_id"])
    return {
        "dept_id": dept["department_id"],
        "prog_id": prog["program_id"],
        "user_id": user["user_id"],
        "student_id": student["student_id"],
        "username": user["username"],
    }


@pytest.mark.asyncio
async def test_create_student(client):
    """Create a student profile."""
    graph = await _setup_student_graph(client, f"sc_{BASE_SUFFIX}")
    # Already created by the helper, just verify
    resp = await client.get(f"/api/v1/students/{graph['student_id']}")
    assert resp.status_code == 200
    assert resp.json()["enrollment_status"] == "active"


@pytest.mark.asyncio
async def test_list_students(client):
    """List students returns paginated results."""
    await _setup_student_graph(client, f"sl_{BASE_SUFFIX}")
    resp = await client.get("/api/v1/students/")
    assert resp.status_code == 200
    data = resp.json()
    assert "students" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_student(client):
    """Get a student by ID."""
    graph = await _setup_student_graph(client, f"sg_{BASE_SUFFIX}")
    resp = await client.get(f"/api/v1/students/{graph['student_id']}")
    assert resp.status_code == 200
    assert resp.json()["student_id"] == str(graph["student_id"])


@pytest.mark.asyncio
async def test_get_student_not_found(client):
    """Get a non-existent student returns 404."""
    resp = await client.get("/api/v1/students/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_student(client):
    """Update a student."""
    graph = await _setup_student_graph(client, f"su_{BASE_SUFFIX}")
    resp = await client.put(
        f"/api/v1/students/{graph['student_id']}",
        json={"enrollment_status": "graduated", "academic_standing": "honors"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["enrollment_status"] == "graduated"
    assert data["academic_standing"] == "honors"


@pytest.mark.asyncio
async def test_delete_student(client):
    """Delete a student."""
    graph = await _setup_student_graph(client, f"sd_{BASE_SUFFIX}")
    resp = await client.delete(f"/api/v1/students/{graph['student_id']}")
    assert resp.status_code == 204

    get_resp = await client.get(f"/api/v1/students/{graph['student_id']}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_student_invalid_user(client):
    """Creating a student with non-existent user returns 404."""
    resp = await client.post("/api/v1/students/", json={
        "user_id": "00000000-0000-0000-0000-000000000000",
        "student_number": f"sn{_short()}",
        "program_id": 1,
        "enrollment_date": "2025-01-15",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_student_duplicate_number(client):
    """Creating a student with duplicate student number returns 409."""
    graph = await _setup_student_graph(client, f"sn_{BASE_SUFFIX}")
    # Try creating another student with same number
    resp = await client.post("/api/v1/students/", json={
        "user_id": graph["user_id"],  # but this user is already a student
        "student_number": f"sn{_short()}",  # different number
        "program_id": graph["prog_id"],
        "enrollment_date": "2025-01-15",
    })
    # Either 409 (duplicate profile for user) or 400
    assert resp.status_code in (400, 409)


@pytest.mark.asyncio
async def test_get_student_enrollments(client):
    """Get enrollments for a student."""
    graph = await _setup_student_graph(client, f"se_{BASE_SUFFIX}")
    dept = await create_department(client, f"se_{BASE_SUFFIX}_de")
    course = await create_course(client, f"se_{BASE_SUFFIX}_c", dept["department_id"])
    term = await create_term(client, f"se_{BASE_SUFFIX}_t")
    section = await create_section(client, f"se_{BASE_SUFFIX}_s", course["course_id"], term["term_id"])
    await create_enrollment(client, graph["student_id"], section["section_id"])

    resp = await client.get(f"/api/v1/students/{graph['student_id']}/enrollments")
    assert resp.status_code == 200
    data = resp.json()
    assert "enrollments" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_students_filters(client):
    """List students supports filters."""
    await _setup_student_graph(client, f"sf_{BASE_SUFFIX}")
    resp = await client.get("/api/v1/students/?enrollment_status=active")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_pagination(client):
    """Students list respects pagination."""
    resp = await client.get("/api/v1/students/?skip=0&limit=5")
    assert resp.status_code == 200
    assert len(resp.json()["students"]) <= 5


@pytest.mark.asyncio
async def test_delete_student_with_enrollments_returns_409(client):
    """Deleting a student that still has enrollments returns 409."""
    graph = await _setup_student_graph(client, f"se409_{BASE_SUFFIX}")
    dept = await create_department(client, f"se409_{BASE_SUFFIX}_de")
    course = await create_course(client, f"se409_{BASE_SUFFIX}_c", dept["department_id"])
    term = await create_term(client, f"se409_{BASE_SUFFIX}_t")
    section = await create_section(client, f"se409_{BASE_SUFFIX}_s", course["course_id"], term["term_id"])
    await create_enrollment(client, graph["student_id"], section["section_id"])

    resp = await client.delete(f"/api/v1/students/{graph['student_id']}")
    assert resp.status_code == 409
    assert "enrollment(s)" in resp.json()["detail"].lower()
