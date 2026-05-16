"""Tests verifying cascade deletion behavior across all entities.

When a parent record is deleted, all associated child records should also be
deleted. These tests verify that cascade deletion works correctly for the
full dependency graph: Department → Course → Section → Enrollment/Assignment,
Program → Student, Term → Section, User → PersonalInfo/Roles, etc.
"""

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient

from .helpers import (
    create_course,
    create_department,
    create_enrollment,
    create_faculty,
    create_program,
    create_section,
    create_student,
    create_term,
    login_user,
    register_user,
    setup_academic_graph,
    setup_user_and_faculty,
    setup_user_and_student,
)


# ────────────────────────────────────────────────────────────
# Department cascade
# ────────────────────────────────────────────────────────────


async def _create_dept_with_courses_programs_faculty(
    client: AsyncClient, suffix: str,
) -> dict[str, Any]:
    """Create a department with courses, programs, and faculty members."""
    dept = await create_department(client, f"{suffix}_dept")

    course1 = await create_course(client, f"{suffix}_c1", dept["department_id"])
    course2 = await create_course(client, f"{suffix}_c2", dept["department_id"])
    prog = await create_program(client, f"{suffix}_p", dept["department_id"])

    # Create a user + faculty for this department
    fac_info = await setup_user_and_faculty(client, f"{suffix}_f", dept["department_id"])

    return {
        "dept_id": dept["department_id"],
        "course_ids": [course1["course_id"], course2["course_id"]],
        "prog_id": prog["program_id"],
        "faculty_id": fac_info["faculty_id"],
    }


@pytest.mark.asyncio
async def test_delete_department_cascades_to_courses(client: AsyncClient, suffix: str):
    """Deleting a department should delete all its courses."""
    data = await _create_dept_with_courses_programs_faculty(client, suffix)

    # Verify courses exist
    for cid in data["course_ids"]:
        resp = await client.get(f"/api/v1/courses/{cid}")
        assert resp.status_code == 200, f"Course {cid} should exist before deletion"

    # Delete the department
    resp = await client.delete(f"/api/v1/departments/{data['dept_id']}")
    assert resp.status_code == 204, f"Delete department failed: {resp.text}"

    # Verify courses are gone
    for cid in data["course_ids"]:
        resp = await client.get(f"/api/v1/courses/{cid}")
        assert resp.status_code == 404, f"Course {cid} should be deleted"


@pytest.mark.asyncio
async def test_delete_department_cascades_to_programs(client: AsyncClient, suffix: str):
    """Deleting a department should delete all its programs."""
    data = await _create_dept_with_courses_programs_faculty(client, suffix)

    # Verify program exists
    resp = await client.get(f"/api/v1/programs/{data['prog_id']}")
    assert resp.status_code == 200

    # Delete the department
    resp = await client.delete(f"/api/v1/departments/{data['dept_id']}")
    assert resp.status_code == 204

    # Verify program is gone
    resp = await client.get(f"/api/v1/programs/{data['prog_id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_department_cascades_to_faculty(client: AsyncClient, suffix: str):
    """Deleting a department should delete all its faculty members."""
    data = await _create_dept_with_courses_programs_faculty(client, suffix)

    # Verify faculty exists
    resp = await client.get(f"/api/v1/faculty/{data['faculty_id']}")
    assert resp.status_code == 200

    # Delete the department
    resp = await client.delete(f"/api/v1/departments/{data['dept_id']}")
    assert resp.status_code == 204

    # Verify faculty is gone
    resp = await client.get(f"/api/v1/faculty/{data['faculty_id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_department_deep_cascade(client: AsyncClient, suffix: str):
    """Deleting a department should cascade through course → section → enrollment."""
    acad = await setup_academic_graph(client, f"{suffix}_deep")

    # Enroll a student in the section
    student_info = await setup_user_and_student(
        client, f"{suffix}_st", acad["prog_id"],
    )
    enrollment = await create_enrollment(
        client, student_info["student_id"], acad["section_id"],
    )

    # Verify enrollment exists
    resp = await client.get(f"/api/v1/enrollments/{enrollment['enrollment_id']}")
    assert resp.status_code == 200

    # Delete the department (which should cascade through all children)
    resp = await client.delete(f"/api/v1/departments/{acad['dept_id']}")
    assert resp.status_code == 204

    # Verify the section is gone
    resp = await client.get(f"/api/v1/sections/{acad['section_id']}")
    assert resp.status_code == 404

    # Verify the enrollment is gone
    resp = await client.get(f"/api/v1/enrollments/{enrollment['enrollment_id']}")
    assert resp.status_code == 404

    # Verify the course is gone
    resp = await client.get(f"/api/v1/courses/{acad['course_id']}")
    assert resp.status_code == 404


# ────────────────────────────────────────────────────────────
# Program cascade
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_program_cascades_to_students(client: AsyncClient, suffix: str):
    """Deleting a program should delete all students in it."""
    acad = await setup_academic_graph(client, f"{suffix}_prg")

    # Create two students in the program
    stu1 = await setup_user_and_student(client, f"{suffix}_s1", acad["prog_id"])
    stu2 = await setup_user_and_student(client, f"{suffix}_s2", acad["prog_id"])

    # Verify students exist
    for sid in [stu1["student_id"], stu2["student_id"]]:
        resp = await client.get(f"/api/v1/students/{sid}")
        assert resp.status_code == 200

    # Delete the program
    resp = await client.delete(f"/api/v1/programs/{acad['prog_id']}")
    assert resp.status_code == 204

    # Verify students are gone
    for sid in [stu1["student_id"], stu2["student_id"]]:
        resp = await client.get(f"/api/v1/students/{sid}")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_program_cascades_to_student_enrollments(
    client: AsyncClient, suffix: str,
):
    """Deleting a program should cascade delete student enrollments."""
    acad = await setup_academic_graph(client, f"{suffix}_penr")

    # Create a student and enroll them
    stu = await setup_user_and_student(client, f"{suffix}_se", acad["prog_id"])
    enrollment = await create_enrollment(client, stu["student_id"], acad["section_id"])

    # Verify enrollment exists
    resp = await client.get(f"/api/v1/enrollments/{enrollment['enrollment_id']}")
    assert resp.status_code == 200

    # Delete the program
    resp = await client.delete(f"/api/v1/programs/{acad['prog_id']}")
    assert resp.status_code == 204

    # Verify enrollment is gone
    resp = await client.get(f"/api/v1/enrollments/{enrollment['enrollment_id']}")
    assert resp.status_code == 404


# ────────────────────────────────────────────────────────────
# Course cascade
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_course_cascades_to_sections(client: AsyncClient, suffix: str):
    """Deleting a course should delete all its sections."""
    acad = await setup_academic_graph(client, f"{suffix}_csc")

    # Verify section exists
    resp = await client.get(f"/api/v1/sections/{acad['section_id']}")
    assert resp.status_code == 200

    # Delete the course
    resp = await client.delete(f"/api/v1/courses/{acad['course_id']}")
    assert resp.status_code == 204

    # Verify section is gone
    resp = await client.get(f"/api/v1/sections/{acad['section_id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_course_cascades_to_section_enrollments(
    client: AsyncClient, suffix: str,
):
    """Deleting a course should cascade delete section enrollments."""
    acad = await setup_academic_graph(client, f"{suffix}_csenr")

    # Enroll a student
    stu = await setup_user_and_student(client, f"{suffix}_ce", acad["prog_id"])
    enrollment = await create_enrollment(client, stu["student_id"], acad["section_id"])

    resp = await client.get(f"/api/v1/enrollments/{enrollment['enrollment_id']}")
    assert resp.status_code == 200

    # Delete the course
    resp = await client.delete(f"/api/v1/courses/{acad['course_id']}")
    assert resp.status_code == 204

    # Verify enrollment is gone
    resp = await client.get(f"/api/v1/enrollments/{enrollment['enrollment_id']}")
    assert resp.status_code == 404


# ────────────────────────────────────────────────────────────
# Section cascade
# ────────────────────────────────────────────────────────────


async def _setup_section_with_enrollments(
    client: AsyncClient, suffix: str,
) -> dict[str, Any]:
    """Create an academic graph, a student, and enroll them in the section."""
    acad = await setup_academic_graph(client, f"{suffix}_sec")
    stu = await setup_user_and_student(client, f"{suffix}_se2", acad["prog_id"])
    enrollment = await create_enrollment(client, stu["student_id"], acad["section_id"])
    return {
        **acad,
        "student_id": stu["student_id"],
        "enrollment_id": enrollment["enrollment_id"],
    }


@pytest.mark.asyncio
async def test_delete_section_cascades_to_enrollments(client: AsyncClient, suffix: str):
    """Deleting a section should delete its enrollments."""
    data = await _setup_section_with_enrollments(client, suffix)

    resp = await client.get(f"/api/v1/enrollments/{data['enrollment_id']}")
    assert resp.status_code == 200

    resp = await client.delete(f"/api/v1/sections/{data['section_id']}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/v1/enrollments/{data['enrollment_id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_section_with_assignments(client: AsyncClient, suffix: str):
    """Deleting a section should delete its assignments."""
    acad = await setup_academic_graph(client, f"{suffix}_sas")

    # Register and login as a user to get auth token
    creator = await register_user(client, f"{suffix}_asn_creator")
    login_resp = await login_user(client, creator["username"])
    token = login_resp["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create an assignment (authenticated)
    resp = await client.post("/api/v1/assignments/", json={
        "section_id": acad["section_id"],
        "assignment_name": f"Test Assignment {suffix}",
        "assignment_type": "homework",
        "max_points": 100,
        "weight_percentage": 10,
        "is_published": True,
        "created_by": str(creator["user_id"]),
    }, headers=headers)
    assert resp.status_code == 201, f"Create assignment failed: {resp.text}"
    assignment_id = resp.json()["assignment_id"]

    # Verify assignment exists
    resp = await client.get(f"/api/v1/assignments/{assignment_id}")
    assert resp.status_code == 200

    # Delete the section
    resp = await client.delete(f"/api/v1/sections/{acad['section_id']}")
    assert resp.status_code == 204

    # Verify assignment is gone
    resp = await client.get(f"/api/v1/assignments/{assignment_id}")
    assert resp.status_code == 404


# ────────────────────────────────────────────────────────────
# Term cascade
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_term_cascades_to_sections(client: AsyncClient, suffix: str):
    """Deleting a term should delete its sections."""
    acad = await setup_academic_graph(client, f"{suffix}_tcs")

    # Verify section exists
    resp = await client.get(f"/api/v1/sections/{acad['section_id']}")
    assert resp.status_code == 200

    # Delete the term
    resp = await client.delete(f"/api/v1/terms/{acad['term_id']}")
    assert resp.status_code == 204

    # Verify section is gone
    resp = await client.get(f"/api/v1/sections/{acad['section_id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_term_cascades_to_enrollments(client: AsyncClient, suffix: str):
    """Deleting a term should cascade delete its sections' enrollments."""
    acad = await setup_academic_graph(client, f"{suffix}_tenr")

    # Enroll a student
    stu = await setup_user_and_student(client, f"{suffix}_te", acad["prog_id"])
    enrollment = await create_enrollment(client, stu["student_id"], acad["section_id"])

    resp = await client.get(f"/api/v1/enrollments/{enrollment['enrollment_id']}")
    assert resp.status_code == 200

    # Delete the term
    resp = await client.delete(f"/api/v1/terms/{acad['term_id']}")
    assert resp.status_code == 204

    # Verify enrollment is gone
    resp = await client.get(f"/api/v1/enrollments/{enrollment['enrollment_id']}")
    assert resp.status_code == 404


# ────────────────────────────────────────────────────────────
# Student cascade
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_student_cascades_to_enrollments(client: AsyncClient, suffix: str):
    """Deleting a student should delete their enrollments."""
    acad = await setup_academic_graph(client, f"{suffix}_stenr")
    stu = await setup_user_and_student(client, f"{suffix}_st1", acad["prog_id"])
    enrollment = await create_enrollment(client, stu["student_id"], acad["section_id"])

    resp = await client.get(f"/api/v1/enrollments/{enrollment['enrollment_id']}")
    assert resp.status_code == 200

    resp = await client.delete(f"/api/v1/students/{stu['student_id']}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/v1/enrollments/{enrollment['enrollment_id']}")
    assert resp.status_code == 404


# ────────────────────────────────────────────────────────────
# User cascade
# ────────────────────────────────────────────────────────────


async def _create_user_with_all_relations(
    client: AsyncClient, suffix: str,
) -> dict[str, Any]:
    """Create a user with personal info, role assignment, and notification."""
    user = await register_user(client, f"{suffix}_usr")

    # Add personal info via PUT (upsert)
    resp = await client.put(
        f"/api/v1/users/{user['user_id']}/personal-info",
        json={
            "first_name": f"Test{suffix}",
            "last_name": "User",
        },
    )
    assert resp.status_code == 200, f"Create personal info failed: {resp.text}"

    # Assign a role — first get the roles list
    roles_resp = await client.get("/api/v1/users/roles")
    assert roles_resp.status_code == 200
    roles = roles_resp.json()
    if roles:
        role_id = roles[0]["role_id"]
        resp = await client.post(f"/api/v1/users/{user['user_id']}/roles/{role_id}")
        assert resp.status_code == 201, f"Assign role failed: {resp.text}"

    return {
        "user_id": user["user_id"],
        "username": user["username"],
    }


@pytest.mark.asyncio
async def test_delete_user_cascades_to_personal_info(client: AsyncClient, suffix: str):
    """Deleting a user should remove their personal info."""
    data = await _create_user_with_all_relations(client, suffix)

    # Verify user exists
    resp = await client.get(f"/api/v1/users/{data['user_id']}")
    assert resp.status_code == 200

    # Delete the user
    resp = await client.delete(f"/api/v1/users/{data['user_id']}")
    assert resp.status_code == 204

    # Verify user is gone
    resp = await client.get(f"/api/v1/users/{data['user_id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_cascades_to_role_assignments(client: AsyncClient, suffix: str):
    """Deleting a user should remove their role assignments."""
    data = await _create_user_with_all_relations(client, suffix)

    # Verify the user exists
    resp = await client.get(f"/api/v1/users/{data['user_id']}")
    assert resp.status_code == 200

    # Delete the user
    resp = await client.delete(f"/api/v1/users/{data['user_id']}")
    assert resp.status_code == 204

    # Verify user is gone
    resp = await client.get(f"/api/v1/users/{data['user_id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_with_student_profile(client: AsyncClient, suffix: str):
    """Deleting a user should also work when they have a student profile."""
    acad = await setup_academic_graph(client, f"{suffix}_uws")
    stu = await setup_user_and_student(client, f"{suffix}_ustu", acad["prog_id"])

    resp = await client.get(f"/api/v1/students/{stu['student_id']}")
    assert resp.status_code == 200

    # Delete the user
    resp = await client.delete(f"/api/v1/users/{stu['user_id']}")
    assert resp.status_code == 204

    # Verify user is gone
    resp = await client.get(f"/api/v1/users/{stu['user_id']}")
    assert resp.status_code == 404

    # Student profile uses FK ondelete=CASCADE, so it should be gone too
    resp = await client.get(f"/api/v1/students/{stu['student_id']}")
    assert resp.status_code == 404


# ────────────────────────────────────────────────────────────
# Faculty cascade
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_faculty_cascades_to_reviews(client: AsyncClient, suffix: str):
    """Deleting a faculty member should delete their reviews."""
    dept = await create_department(client, f"{suffix}_freview")
    fac_info = await setup_user_and_faculty(client, f"{suffix}_frev", dept["department_id"])

    # Create a review for this faculty member
    # First, we need a reviewable enrollment
    acad = await setup_academic_graph(client, f"{suffix}_revg", section_overrides={"instructor_id": fac_info["faculty_id"]})
    stu = await setup_user_and_student(client, f"{suffix}_revst", acad["prog_id"])
    enrollment = await create_enrollment(client, stu["student_id"], acad["section_id"])

    # Login as the student to get auth token for grade submission and review
    login_resp = await login_user(client, stu["username"])
    token = login_resp["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Submit a grade to make it reviewable
    resp = await client.post(
        f"/api/v1/enrollments/{enrollment['enrollment_id']}/grade",
        params={
            "grade": "A",
            "grade_points": 4.0,
            "graded_by": str(fac_info["user_id"]),
        },
        headers=headers,
    )
    assert resp.status_code == 200, f"Submit grade failed: {resp.text}"

    # Create the review (authenticated as the student)
    # The endpoint auto-populates course_id, faculty_id, term_id from the section
    resp = await client.post("/api/v1/reviews/", json={
        "enrollment_id": enrollment["enrollment_id"],
        "overall_rating": 5,
        "comment": "Great course!",
    }, headers=headers)
    assert resp.status_code == 201, f"Create review failed: {resp.text}"
    review_id = resp.json()["review_id"]

    # Verify review exists
    resp = await client.get(f"/api/v1/reviews/{review_id}", headers=headers)
    assert resp.status_code == 200, f"Get review failed: {resp.text}"

    # Delete the faculty member
    resp = await client.delete(f"/api/v1/faculty/{fac_info['faculty_id']}")
    assert resp.status_code == 204

    # Verify review is gone
    resp = await client.get(f"/api/v1/reviews/{review_id}", headers=headers)
    assert resp.status_code == 404, f"Review still exists after faculty delete: {resp.text}"


# ────────────────────────────────────────────────────────────
# Negative cases — deleting without dependents
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_empty_department_succeeds(client: AsyncClient, suffix: str):
    """Deleting a department with no dependents should succeed."""
    dept = await create_department(client, f"{suffix}_empty")

    resp = await client.delete(f"/api/v1/departments/{dept['department_id']}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/v1/departments/{dept['department_id']}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_empty_term_succeeds(client: AsyncClient, suffix: str):
    """Deleting a term with no sections should succeed."""
    term = await create_term(client, f"{suffix}_empty")

    resp = await client.delete(f"/api/v1/terms/{term['term_id']}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/v1/terms/{term['term_id']}")
    assert resp.status_code == 404


# ────────────────────────────────────────────────────────────
# 404 errors on nonexistent records
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_nonexistent_department_returns_404(client: AsyncClient):
    resp = await client.delete("/api/v1/departments/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_course_returns_404(client: AsyncClient):
    resp = await client.delete("/api/v1/courses/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_section_returns_404(client: AsyncClient):
    resp = await client.delete("/api/v1/sections/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_program_returns_404(client: AsyncClient):
    resp = await client.delete("/api/v1/programs/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_term_returns_404(client: AsyncClient):
    resp = await client.delete("/api/v1/terms/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_enrollment_returns_404(client: AsyncClient):
    resp = await client.delete("/api/v1/enrollments/999999")
    assert resp.status_code == 404
