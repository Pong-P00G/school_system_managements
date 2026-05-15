"""Comprehensive API tests for the course sections endpoint (CRUD + enroll + join)."""

from __future__ import annotations

import uuid

import pytest

from .helpers import (
    create_course,
    create_department,
    create_enrollment,
    create_section,
    create_student,
    create_term,
    register_user,
    setup_academic_graph,
    _short,
)

BASE_SUFFIX = uuid.uuid4().hex[:6]


@pytest.mark.asyncio
async def test_create_section(client):
    """Create a course section successfully."""
    acad = await setup_academic_graph(client, f"sc_{BASE_SUFFIX}")
    resp = await client.post("/api/v1/sections/", json={
        "course_id": acad["course_id"],
        "term_id": acad["term_id"],
        "section_number": f"s{_short()}",
        "max_capacity": 30,
        "delivery_mode": "in-person",
        "status": "open",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["section_number"] is not None
    assert data["max_capacity"] == 30
    assert data["join_code"] is not None  # auto-generated


@pytest.mark.asyncio
async def test_list_sections(client):
    """List sections returns paginated results."""
    acad = await setup_academic_graph(client, f"sl_{BASE_SUFFIX}")
    await create_section(client, f"sl_{BASE_SUFFIX}", acad["course_id"], acad["term_id"])
    resp = await client.get("/api/v1/sections/")
    assert resp.status_code == 200
    data = resp.json()
    assert "sections" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_section(client):
    """Get a section by ID."""
    acad = await setup_academic_graph(client, f"sg_{BASE_SUFFIX}")
    section = await create_section(client, f"sg_{BASE_SUFFIX}", acad["course_id"], acad["term_id"])
    resp = await client.get(f"/api/v1/sections/{section['section_id']}")
    assert resp.status_code == 200
    assert resp.json()["section_id"] == section["section_id"]


@pytest.mark.asyncio
async def test_get_section_not_found(client):
    """Get a non-existent section returns 404."""
    resp = await client.get("/api/v1/sections/99999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_section(client):
    """Update a section."""
    acad = await setup_academic_graph(client, f"su_{BASE_SUFFIX}")
    section = await create_section(client, f"su_{BASE_SUFFIX}", acad["course_id"], acad["term_id"])
    resp = await client.put(
        f"/api/v1/sections/{section['section_id']}",
        json={"max_capacity": 50, "delivery_mode": "online"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["max_capacity"] == 50
    assert data["delivery_mode"] == "online"


@pytest.mark.asyncio
async def test_delete_section(client):
    """Delete a section."""
    acad = await setup_academic_graph(client, f"sd_{BASE_SUFFIX}")
    section = await create_section(client, f"sd_{BASE_SUFFIX}", acad["course_id"], acad["term_id"])
    resp = await client.delete(f"/api/v1/sections/{section['section_id']}")
    assert resp.status_code == 204

    get_resp = await client.get(f"/api/v1/sections/{section['section_id']}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_section_duplicate_number(client):
    """Creating a section with duplicate section number for same course/term returns 409."""
    acad = await setup_academic_graph(client, f"sx_{BASE_SUFFIX}")
    num = f"s{_short()}"
    await create_section(client, f"sx_{BASE_SUFFIX}", acad["course_id"], acad["term_id"],
                         section_number=num)
    resp = await client.post("/api/v1/sections/", json={
        "course_id": acad["course_id"],
        "term_id": acad["term_id"],
        "section_number": num,
        "max_capacity": 30,
        "delivery_mode": "in-person",
        "status": "open",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_section_invalid_course(client):
    """Creating a section with non-existent course returns 404."""
    term = await create_term(client, f"si_{BASE_SUFFIX}")
    resp = await client.post("/api/v1/sections/", json={
        "course_id": 99999999,
        "term_id": term["term_id"],
        "section_number": "s001",
        "max_capacity": 30,
        "delivery_mode": "in-person",
        "status": "open",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_sections_filters(client):
    """List sections supports filters."""
    acad = await setup_academic_graph(client, f"sf_{BASE_SUFFIX}")
    await create_section(client, f"sf_{BASE_SUFFIX}", acad["course_id"], acad["term_id"])

    # By course
    resp = await client.get(f"/api/v1/sections/?course_id={acad['course_id']}")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1

    # By term
    resp = await client.get(f"/api/v1/sections/?term_id={acad['term_id']}")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1

    # By status
    resp = await client.get("/api/v1/sections/?status=open")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_section_enrollments(client):
    """Get enrollments for a section."""
    acad = await setup_academic_graph(client, f"se_{BASE_SUFFIX}")
    section = await create_section(client, f"se_{BASE_SUFFIX}", acad["course_id"], acad["term_id"],
                                   max_capacity=2)
    user = await register_user(client, f"se_{BASE_SUFFIX}")
    student = await create_student(client, f"se_{BASE_SUFFIX}", user["user_id"], acad["prog_id"])
    await create_enrollment(client, student["student_id"], section["section_id"])

    resp = await client.get(f"/api/v1/sections/{section['section_id']}/enrollments")
    assert resp.status_code == 200
    data = resp.json()
    assert "enrollments" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_section_assignments(client):
    """Get assignments for a section."""
    acad = await setup_academic_graph(client, f"sa_{BASE_SUFFIX}")
    section = await create_section(client, f"sa_{BASE_SUFFIX}", acad["course_id"], acad["term_id"])
    resp = await client.get(f"/api/v1/sections/{section['section_id']}/assignments")
    assert resp.status_code == 200
    data = resp.json()
    assert "assignments" in data


@pytest.mark.asyncio
async def test_enroll_student_manually(client):
    """Enroll a student manually via the sections endpoint."""
    acad = await setup_academic_graph(client, f"sm_{BASE_SUFFIX}")
    section = await create_section(client, f"sm_{BASE_SUFFIX}", acad["course_id"], acad["term_id"],
                                   max_capacity=2)
    user = await register_user(client, f"sm_{BASE_SUFFIX}")
    student = await create_student(client, f"sm_{BASE_SUFFIX}", user["user_id"], acad["prog_id"])

    resp = await client.post(
        f"/api/v1/sections/{section['section_id']}/enroll",
        params={"student_id": str(student["student_id"])},
    )
    assert resp.status_code == 201
    assert "enrollment_id" in resp.json()


@pytest.mark.asyncio
async def test_join_section_by_code(client):
    """Join a section using the class join code."""
    acad = await setup_academic_graph(client, f"sj_{BASE_SUFFIX}")
    section = await create_section(client, f"sj_{BASE_SUFFIX}", acad["course_id"], acad["term_id"],
                                   max_capacity=2)
    user = await register_user(client, f"sj_{BASE_SUFFIX}")
    student = await create_student(client, f"sj_{BASE_SUFFIX}", user["user_id"], acad["prog_id"])

    # Get the section's join code
    sec_resp = await client.get(f"/api/v1/sections/{section['section_id']}")
    join_code = sec_resp.json()["join_code"]

    resp = await client.post(
        "/api/v1/sections/join",
        json={"join_code": join_code, "student_id": str(student["student_id"])},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "enrollment_id" in data
    assert data["course_name"] is not None


@pytest.mark.asyncio
async def test_join_section_invalid_code(client):
    """Join with an invalid code returns 404."""
    resp = await client.post(
        "/api/v1/sections/join",
        json={"join_code": "INVALID", "student_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_pagination(client):
    """Sections list respects pagination."""
    resp = await client.get("/api/v1/sections/?skip=0&limit=5")
    assert resp.status_code == 200
    assert len(resp.json()["sections"]) <= 5
