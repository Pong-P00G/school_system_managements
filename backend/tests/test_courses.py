"""Comprehensive API tests for the courses endpoint (CRUD + filters + sections)."""

from __future__ import annotations

import uuid

import pytest

from .helpers import (
    create_course,
    create_department,
    create_section,
    create_term,
    _short,
)

BASE_SUFFIX = uuid.uuid4().hex[:6]


@pytest.mark.asyncio
async def test_create_course(client):
    """Create a course successfully."""
    dept = await create_department(client, f"c_{BASE_SUFFIX}")
    payload = {
        "course_code": f"cc{_short()}",
        "course_name": f"Test Course {BASE_SUFFIX}",
        "department_id": dept["department_id"],
        "credits": 3,
    }
    resp = await client.post("/api/v1/courses/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["course_code"] == payload["course_code"]
    assert data["course_name"] == payload["course_name"]
    assert data["credits"] == 3
    assert data["is_active"] is True
    assert data["course_level"] == "undergraduate"  # default


@pytest.mark.asyncio
async def test_list_courses(client):
    """List courses returns paginated results."""
    dept = await create_department(client, f"cl_{BASE_SUFFIX}")
    await create_course(client, f"cl_{BASE_SUFFIX}", dept["department_id"])

    resp = await client.get("/api/v1/courses/")
    assert resp.status_code == 200
    data = resp.json()
    assert "courses" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_course(client):
    """Get a course by ID."""
    dept = await create_department(client, f"cg_{BASE_SUFFIX}")
    course = await create_course(client, f"cg_{BASE_SUFFIX}", dept["department_id"])

    resp = await client.get(f"/api/v1/courses/{course['course_id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["course_id"] == course["course_id"]
    assert data["course_name"] == course["course_name"]


@pytest.mark.asyncio
async def test_get_course_not_found(client):
    """Get a non-existent course returns 404."""
    resp = await client.get("/api/v1/courses/99999999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_course(client):
    """Update a course."""
    dept = await create_department(client, f"cu_{BASE_SUFFIX}")
    course = await create_course(client, f"cu_{BASE_SUFFIX}", dept["department_id"])

    resp = await client.put(
        f"/api/v1/courses/{course['course_id']}",
        json={"course_name": "Updated Name", "credits": 4},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["course_name"] == "Updated Name"
    assert data["credits"] == 4


@pytest.mark.asyncio
async def test_delete_course_soft(client):
    """Delete a course (hard delete)."""
    dept = await create_department(client, f"cd_{BASE_SUFFIX}")
    course = await create_course(client, f"cd_{BASE_SUFFIX}", dept["department_id"])

    resp = await client.delete(f"/api/v1/courses/{course['course_id']}")
    assert resp.status_code == 204

    # Verify it's actually deleted
    get_resp = await client.get(f"/api/v1/courses/{course['course_id']}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_course_duplicate_code(client):
    """Creating a course with a duplicate code returns 409."""
    dept = await create_department(client, f"cx_{BASE_SUFFIX}")
    code = f"cx{_short()}"
    await create_course(client, f"cx_{BASE_SUFFIX}", dept["department_id"],
                        course_code=code)

    resp = await client.post("/api/v1/courses/", json={
        "course_code": code,
        "course_name": "Duplicate",
        "department_id": dept["department_id"],
        "credits": 3,
    })
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_course_invalid_department(client):
    """Creating a course with a non-existent department returns 400."""
    resp = await client.post("/api/v1/courses/", json={
        "course_code": f"cx{_short()}",
        "course_name": "Bad Dept",
        "department_id": 99999999,
        "credits": 3,
    })
    assert resp.status_code == 400 or resp.status_code == 404


@pytest.mark.asyncio
async def test_list_courses_filters(client):
    """List courses supports filters: department_id, is_active, search."""
    dept = await create_department(client, f"cf_{BASE_SUFFIX}")
    await create_course(client, f"cf_{BASE_SUFFIX}", dept["department_id"])

    # Filter by department_id
    resp = await client.get(f"/api/v1/courses/?department_id={dept['department_id']}")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1

    # Filter by is_active
    resp = await client.get("/api/v1/courses/?is_active=true")
    assert resp.status_code == 200

    # Search by name
    resp = await client.get("/api/v1/courses/?search=Course")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_course_sections(client):
    """Get sections for a course."""
    dept = await create_department(client, f"cs_{BASE_SUFFIX}")
    course = await create_course(client, f"cs_{BASE_SUFFIX}", dept["department_id"])
    term = await create_term(client, f"cs_{BASE_SUFFIX}")
    await create_section(client, f"cs_{BASE_SUFFIX}", course["course_id"], term["term_id"])

    resp = await client.get(f"/api/v1/courses/{course['course_id']}/sections")
    assert resp.status_code == 200
    data = resp.json()
    assert "sections" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_courses_pagination(client):
    """List courses respects skip/limit pagination."""
    resp = await client.get("/api/v1/courses/?skip=0&limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["courses"]) <= 5


@pytest.mark.asyncio
async def test_delete_course_with_sections_returns_409(client):
    """Deleting a course that still has sections returns 409."""
    dept = await create_department(client, f"cs409_{BASE_SUFFIX}")
    course = await create_course(client, f"cs409_{BASE_SUFFIX}", dept["department_id"])
    term = await create_term(client, f"cs409_{BASE_SUFFIX}")
    await create_section(client, f"cs409_{BASE_SUFFIX}", course["course_id"], term["term_id"])

    resp = await client.delete(f"/api/v1/courses/{course['course_id']}")
    assert resp.status_code == 409
    assert "section(s)" in resp.json()["detail"].lower()
