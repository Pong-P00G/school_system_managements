"""Comprehensive API tests for the programs endpoint (CRUD + filters + students)."""

from __future__ import annotations

import uuid

import pytest

from .helpers import (
    create_course,
    create_department,
    create_program,
    create_student,
    create_term,
    register_user,
    _short,
)

BASE_SUFFIX = uuid.uuid4().hex[:6]


@pytest.mark.asyncio
async def test_create_program(client):
    """Create a program successfully."""
    dept = await create_department(client, f"pc_{BASE_SUFFIX}")
    code = f"p_{_short()}"
    resp = await client.post("/api/v1/programs/", json={
        "program_code": code,
        "program_name": f"Test Program {BASE_SUFFIX}",
        "department_id": dept["department_id"],
        "degree_level": "Bachelor",
        "total_credits_required": 120,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["program_code"] == code
    assert data["degree_level"] == "Bachelor"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_programs(client):
    """List programs returns paginated results."""
    dept = await create_department(client, f"pl_{BASE_SUFFIX}")
    await create_program(client, f"pl_{BASE_SUFFIX}", dept["department_id"])
    resp = await client.get("/api/v1/programs/")
    assert resp.status_code == 200
    data = resp.json()
    assert "programs" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_program(client):
    """Get a program by ID."""
    dept = await create_department(client, f"pg_{BASE_SUFFIX}")
    prog = await create_program(client, f"pg_{BASE_SUFFIX}", dept["department_id"])
    resp = await client.get(f"/api/v1/programs/{prog['program_id']}")
    assert resp.status_code == 200
    assert resp.json()["program_id"] == prog["program_id"]


@pytest.mark.asyncio
async def test_get_program_not_found(client):
    """Get a non-existent program returns 404."""
    resp = await client.get("/api/v1/programs/99999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_program(client):
    """Update a program."""
    dept = await create_department(client, f"pu_{BASE_SUFFIX}")
    prog = await create_program(client, f"pu_{BASE_SUFFIX}", dept["department_id"])
    new_name = f"Updated Program {BASE_SUFFIX}"
    resp = await client.put(
        f"/api/v1/programs/{prog['program_id']}",
        json={"program_name": new_name},
    )
    assert resp.status_code == 200
    assert resp.json()["program_name"] == new_name


@pytest.mark.asyncio
async def test_delete_program_soft(client):
    """Delete a program."""
    dept = await create_department(client, f"pd_{BASE_SUFFIX}")
    prog = await create_program(client, f"pd_{BASE_SUFFIX}", dept["department_id"])
    resp = await client.delete(f"/api/v1/programs/{prog['program_id']}")
    assert resp.status_code == 204

    get_resp = await client.get(f"/api/v1/programs/{prog['program_id']}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_program_duplicate(client):
    """Creating a program with duplicate code/name returns 409."""
    dept = await create_department(client, f"px_{BASE_SUFFIX}")
    code = f"px{_short()}"
    await create_program(client, f"px_{BASE_SUFFIX}", dept["department_id"],
                         program_code=code)
    resp = await client.post("/api/v1/programs/", json={
        "program_code": code,
        "program_name": "Duplicate",
        "department_id": dept["department_id"],
        "degree_level": "Bachelor",
        "total_credits_required": 120,
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_program_invalid_department(client):
    """Creating a program with non-existent department returns 400."""
    resp = await client.post("/api/v1/programs/", json={
        "program_code": f"px{_short()}",
        "program_name": "Bad Dept",
        "department_id": 99999999,
        "degree_level": "Bachelor",
        "total_credits_required": 120,
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_list_programs_filters(client):
    """List programs supports filters."""
    dept = await create_department(client, f"pf_{BASE_SUFFIX}")
    await create_program(client, f"pf_{BASE_SUFFIX}", dept["department_id"])

    # Filter by department
    resp = await client.get(f"/api/v1/programs/?department_id={dept['department_id']}")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1

    # Filter by degree_level
    resp = await client.get("/api/v1/programs/?degree_level=Bachelor")
    assert resp.status_code == 200

    # Search
    resp = await client.get("/api/v1/programs/?search=Prog")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_program_students(client):
    """Get students enrolled in a program."""
    dept = await create_department(client, f"ps_{BASE_SUFFIX}")
    prog = await create_program(client, f"ps_{BASE_SUFFIX}", dept["department_id"])
    user = await register_user(client, f"ps_{BASE_SUFFIX}")
    await create_student(client, f"ps_{BASE_SUFFIX}", user["user_id"], prog["program_id"])

    resp = await client.get(f"/api/v1/programs/{prog['program_id']}/students")
    assert resp.status_code == 200
    data = resp.json()
    assert "students" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_pagination(client):
    """Programs list respects pagination."""
    resp = await client.get("/api/v1/programs/?skip=0&limit=5")
    assert resp.status_code == 200
    assert len(resp.json()["programs"]) <= 5


@pytest.mark.asyncio
async def test_delete_program_with_students_cascades(client):
    """Deleting a program should cascade to its students."""
    dept = await create_department(client, f"ps409_{BASE_SUFFIX}")
    prog = await create_program(client, f"ps409_{BASE_SUFFIX}", dept["department_id"])
    user = await register_user(client, f"ps409_{BASE_SUFFIX}")
    student = await create_student(client, f"ps409_{BASE_SUFFIX}", user["user_id"], prog["program_id"])

    resp = await client.delete(f"/api/v1/programs/{prog['program_id']}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/v1/students/{student['student_id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_program_not_found(client):
    """Deleting a non-existent program returns 404."""
    resp = await client.delete("/api/v1/programs/99999999")
    assert resp.status_code == 404
