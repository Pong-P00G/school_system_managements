"""Shared helper/factory functions for creating test data in API tests.

All functions in this module follow the same pattern: they use the async HTTP
client to call real API endpoints and return the JSON response data. Unique
suffixes (short hex strings) are used to avoid collisions since tests share a
single database.
"""

from __future__ import annotations

import uuid
from typing import Any


def _short() -> str:
    """Return a short hex string for use in unique identifiers."""
    return uuid.uuid4().hex[:8]


# ---------------------------------------------------------------------------
# Auth / User helpers
# ---------------------------------------------------------------------------

async def register_user(client, suffix: str) -> dict[str, Any]:
    """Register a user and return the full JSON response."""
    resp = await client.post("/api/v1/auth/register", json={
        "username": f"u_{suffix}",
        "email": f"u_{suffix}@test.com",
        "password": "Password123",
    })
    assert resp.status_code == 201, f"Register failed: {resp.text}"
    return resp.json()


async def login_user(client, username: str, password: str = "Password123") -> dict[str, Any]:
    """Log in and return the token response."""
    resp = await client.post("/api/v1/auth/login", json={
        "username": username,
        "password": password,
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()


# ---------------------------------------------------------------------------
# Domain entity helpers
# ---------------------------------------------------------------------------

async def create_department(client, suffix: str, **overrides: Any) -> dict[str, Any]:
    """Create a department and return the JSON response."""
    payload = {
        "department_code": f"d{_short()}",
        "department_name": f"Dept {suffix}",
        "is_active": True,
    }
    payload.update(overrides)
    resp = await client.post("/api/v1/departments/", json=payload)
    assert resp.status_code == 201, f"Create department failed: {resp.text}"
    return resp.json()


async def create_program(client, suffix: str, department_id: int, **overrides: Any) -> dict[str, Any]:
    """Create a program and return the JSON response."""
    payload = {
        "program_code": f"p_{_short()}",
        "program_name": f"Prog {suffix}",
        "department_id": department_id,
        "degree_level": "Bachelor",
        "total_credits_required": 120,
    }
    payload.update(overrides)
    resp = await client.post("/api/v1/programs/", json=payload)
    assert resp.status_code == 201, f"Create program failed: {resp.text}"
    return resp.json()


async def create_course(client, suffix: str, department_id: int, **overrides: Any) -> dict[str, Any]:
    """Create a course and return the JSON response."""
    payload = {
        "course_code": f"c{_short()}",
        "course_name": f"Course {suffix}",
        "department_id": department_id,
        "credits": 3,
    }
    payload.update(overrides)
    resp = await client.post("/api/v1/courses/", json=payload)
    assert resp.status_code == 201, f"Create course failed: {resp.text}"
    return resp.json()


async def create_term(client, suffix: str, **overrides: Any) -> dict[str, Any]:
    """Create an academic term and return the JSON response."""
    payload = {
        "term_name": f"Term {suffix}",
        "term_code": f"t{_short()}",
        "academic_year": "2025-2026",
        "term_type": "spring",
        "start_date": "2025-01-15",
        "end_date": "2025-05-15",
        "status": "active",
    }
    payload.update(overrides)
    resp = await client.post("/api/v1/terms/", json=payload)
    assert resp.status_code == 201, f"Create term failed: {resp.text}"
    return resp.json()


async def create_section(client, suffix: str, course_id: int, term_id: int, **overrides: Any) -> dict[str, Any]:
    """Create a course section and return the JSON response."""
    payload = {
        "course_id": course_id,
        "term_id": term_id,
        "section_number": f"s{_short()}",
        "max_capacity": 30,
        "delivery_mode": "in-person",
        "status": "open",
    }
    payload.update(overrides)
    resp = await client.post("/api/v1/sections/", json=payload)
    assert resp.status_code == 201, f"Create section failed: {resp.text}"
    return resp.json()


async def create_student(
    client, suffix: str, user_id: str, program_id: int, **overrides: Any
) -> dict[str, Any]:
    """Create a student profile and return the JSON response."""
    payload = {
        "user_id": str(user_id),
        "student_number": f"sn{_short()}",
        "program_id": program_id,
        "enrollment_date": "2025-01-15",
        "enrollment_status": "active",
    }
    payload.update(overrides)
    resp = await client.post("/api/v1/students/", json=payload)
    assert resp.status_code == 201, f"Create student failed: {resp.text}"
    return resp.json()


async def create_faculty(
    client, suffix: str, user_id: str, department_id: int, **overrides: Any
) -> dict[str, Any]:
    """Create a faculty profile and return the JSON response."""
    payload = {
        "user_id": str(user_id),
        "employee_number": f"en{_short()}",
        "department_id": department_id,
        "hire_date": "2025-01-15",
        "faculty_rank": "Assistant Professor",
        "tenure_status": "tenure-track",
        "employment_type": "full-time",
        "employment_status": "active",
    }
    payload.update(overrides)
    resp = await client.post("/api/v1/faculty/", json=payload)
    assert resp.status_code == 201, f"Create faculty failed: {resp.text}"
    return resp.json()


async def create_staff(
    client, suffix: str, user_id: str, **overrides: Any
) -> dict[str, Any]:
    """Create a staff profile and return the JSON response."""
    payload = {
        "user_id": str(user_id),
        "employee_number": f"en{_short()}",
        "hire_date": "2025-01-15",
        "job_title": "Administrative Assistant",
        "job_category": "administrative",
        "employment_type": "full-time",
        "employment_status": "active",
    }
    payload.update(overrides)
    resp = await client.post("/api/v1/staff/", json=payload)
    assert resp.status_code == 201, f"Create staff failed: {resp.text}"
    return resp.json()


async def create_enrollment(client, student_id: str, section_id: int) -> dict[str, Any]:
    """Create an enrollment and return the JSON response."""
    resp = await client.post("/api/v1/enrollments/", json={
        "student_id": str(student_id),
        "section_id": section_id,
    })
    assert resp.status_code == 201, f"Create enrollment failed: {resp.text}"
    return resp.json()


# ---------------------------------------------------------------------------
# Composite fixture helpers
# ---------------------------------------------------------------------------

async def setup_academic_graph(
    client,
    base_suffix: str,
    *,
    course_overrides: dict | None = None,
    term_overrides: dict | None = None,
    section_overrides: dict | None = None,
) -> dict[str, Any]:
    """Create a full academic dependency graph.

    Returns a dict with keys:
      dept_id, prog_id, course_id, term_id, section_id
    """
    dept = await create_department(client, f"{base_suffix}_d")
    prog = await create_program(client, f"{base_suffix}_p", dept["department_id"])
    course = await create_course(
        client, f"{base_suffix}_c", dept["department_id"],
        **(course_overrides or {}),
    )
    term = await create_term(
        client, f"{base_suffix}_t",
        **(term_overrides or {}),
    )
    section = await create_section(
        client, f"{base_suffix}_s", course["course_id"], term["term_id"],
        **(section_overrides or {}),
    )
    return {
        "dept_id": dept["department_id"],
        "prog_id": prog["program_id"],
        "course_id": course["course_id"],
        "term_id": term["term_id"],
        "section_id": section["section_id"],
    }


async def setup_user_and_student(
    client, base_suffix: str, program_id: int
) -> dict[str, Any]:
    """Create a user + student profile. Returns dict with user_id, student_id."""
    user = await register_user(client, f"{base_suffix}_st")
    student = await create_student(
        client, f"{base_suffix}_s", user["user_id"], program_id,
    )
    return {
        "user_id": user["user_id"],
        "student_id": student["student_id"],
        "username": user["username"],
    }


async def setup_user_and_faculty(
    client, base_suffix: str, department_id: int
) -> dict[str, Any]:
    """Create a user + faculty profile. Returns dict with user_id, faculty_id."""
    user = await register_user(client, f"{base_suffix}_fa")
    faculty = await create_faculty(
        client, f"{base_suffix}_f", user["user_id"], department_id,
    )
    return {
        "user_id": user["user_id"],
        "faculty_id": faculty["faculty_id"],
        "username": user["username"],
    }


async def setup_user_and_staff(
    client, base_suffix: str
) -> dict[str, Any]:
    """Create a user + staff profile. Returns dict with user_id, staff_id."""
    user = await register_user(client, f"{base_suffix}_stf")
    staff = await create_staff(
        client, f"{base_suffix}_stf", user["user_id"],
    )
    return {
        "user_id": user["user_id"],
        "staff_id": staff["staff_id"],
        "username": user["username"],
    }
