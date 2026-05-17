"""Tests for the Reviews CRUD API endpoints."""

from __future__ import annotations

import uuid

import pytest

from .helpers import (
    _short,
    create_enrollment,
    register_user,
    login_user,
    setup_academic_graph,
    create_student,
    create_section,
    create_term,
)

BASE_SUFFIX = uuid.uuid4().hex[:6]


async def _setup_student_with_enrollment(client, suffix: str, term_overrides=None):
    """Create a student enrolled in a section (with a past term for reviewability)."""
    term_opts = term_overrides or {
        "start_date": "2024-01-15",
        "end_date": "2024-05-15",
        "status": "completed",
    }
    acad = await setup_academic_graph(client, suffix, term_overrides=term_opts)
    user = await register_user(client, f"{suffix}_rv")
    student = await create_student(client, f"{suffix}_rv", user["user_id"], acad["prog_id"])
    enrollment = await create_enrollment(client, student["student_id"], acad["section_id"])
    token_data = await login_user(client, user["username"])
    return {
        "user": user,
        "student": student,
        "enrollment": enrollment,
        "academic": acad,
        "token": token_data["access_token"],
    }


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_review(client):
    """Create a review for a completed enrollment."""
    data = await _setup_student_with_enrollment(client, f"cr_{BASE_SUFFIX}")
    resp = await client.post("/api/v1/reviews/", json={
        "enrollment_id": data["enrollment"]["enrollment_id"],
        "overall_rating": 4,
        "teaching_rating": 5,
        "content_rating": 4,
        "workload_rating": 3,
        "title": "Great course",
        "comment": "Learned a lot!",
        "is_anonymous": False,
    }, headers=_auth(data["token"]))
    assert resp.status_code == 201
    body = resp.json()
    assert body["overall_rating"] == 4
    assert body["teaching_rating"] == 5
    assert body["title"] == "Great course"
    assert body["enrollment_id"] == data["enrollment"]["enrollment_id"]
    assert "review_id" in body


@pytest.mark.asyncio
async def test_create_review_duplicate(client):
    """Cannot create two reviews for the same enrollment."""
    data = await _setup_student_with_enrollment(client, f"dup_{BASE_SUFFIX}")
    payload = {
        "enrollment_id": data["enrollment"]["enrollment_id"],
        "overall_rating": 5,
    }
    resp1 = await client.post("/api/v1/reviews/", json=payload, headers=_auth(data["token"]))
    assert resp1.status_code == 201

    resp2 = await client.post("/api/v1/reviews/", json=payload, headers=_auth(data["token"]))
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_create_review_invalid_rating(client):
    """Rating out of range should fail validation."""
    data = await _setup_student_with_enrollment(client, f"inv_{BASE_SUFFIX}")
    resp = await client.post("/api/v1/reviews/", json={
        "enrollment_id": data["enrollment"]["enrollment_id"],
        "overall_rating": 6,
    }, headers=_auth(data["token"]))
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_reviews(client):
    """List reviews returns paginated results."""
    data = await _setup_student_with_enrollment(client, f"lr_{BASE_SUFFIX}")
    await client.post("/api/v1/reviews/", json={
        "enrollment_id": data["enrollment"]["enrollment_id"],
        "overall_rating": 4,
    }, headers=_auth(data["token"]))

    resp = await client.get("/api/v1/reviews/", headers=_auth(data["token"]))
    assert resp.status_code == 200
    body = resp.json()
    assert "reviews" in body
    assert "total" in body
    assert body["total"] >= 1


@pytest.mark.asyncio
async def test_get_review_by_id(client):
    """Get a single review by ID."""
    data = await _setup_student_with_enrollment(client, f"gr_{BASE_SUFFIX}")
    create_resp = await client.post("/api/v1/reviews/", json={
        "enrollment_id": data["enrollment"]["enrollment_id"],
        "overall_rating": 3,
        "title": "OK course",
    }, headers=_auth(data["token"]))
    review_id = create_resp.json()["review_id"]

    resp = await client.get(f"/api/v1/reviews/{review_id}", headers=_auth(data["token"]))
    assert resp.status_code == 200
    assert resp.json()["review_id"] == review_id
    assert resp.json()["title"] == "OK course"


@pytest.mark.asyncio
async def test_get_review_not_found(client):
    """Get a non-existent review returns 404."""
    data = await _setup_student_with_enrollment(client, f"nf_{BASE_SUFFIX}")
    resp = await client.get("/api/v1/reviews/999999", headers=_auth(data["token"]))
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_review(client):
    """Update own review."""
    data = await _setup_student_with_enrollment(client, f"ur_{BASE_SUFFIX}")
    create_resp = await client.post("/api/v1/reviews/", json={
        "enrollment_id": data["enrollment"]["enrollment_id"],
        "overall_rating": 3,
        "title": "Initial title",
    }, headers=_auth(data["token"]))
    review_id = create_resp.json()["review_id"]

    resp = await client.patch(f"/api/v1/reviews/{review_id}", json={
        "overall_rating": 5,
        "title": "Updated title",
        "comment": "Changed my mind, it was great!",
    }, headers=_auth(data["token"]))
    assert resp.status_code == 200
    body = resp.json()
    assert body["overall_rating"] == 5
    assert body["title"] == "Updated title"
    assert body["comment"] == "Changed my mind, it was great!"


@pytest.mark.asyncio
async def test_update_review_not_owner(client):
    """Cannot update another student's review."""
    data = await _setup_student_with_enrollment(client, f"uo_{BASE_SUFFIX}")
    create_resp = await client.post("/api/v1/reviews/", json={
        "enrollment_id": data["enrollment"]["enrollment_id"],
        "overall_rating": 4,
    }, headers=_auth(data["token"]))
    review_id = create_resp.json()["review_id"]

    # Another user tries to update
    other_user = await register_user(client, f"uo2_{BASE_SUFFIX}")
    await create_student(client, f"uo2_{BASE_SUFFIX}", other_user["user_id"], data["academic"]["prog_id"])
    other_token = (await login_user(client, other_user["username"]))["access_token"]

    resp = await client.patch(f"/api/v1/reviews/{review_id}", json={
        "overall_rating": 1,
    }, headers=_auth(other_token))
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_review(client):
    """Delete own review."""
    data = await _setup_student_with_enrollment(client, f"dr_{BASE_SUFFIX}")
    create_resp = await client.post("/api/v1/reviews/", json={
        "enrollment_id": data["enrollment"]["enrollment_id"],
        "overall_rating": 2,
    }, headers=_auth(data["token"]))
    review_id = create_resp.json()["review_id"]

    resp = await client.delete(f"/api/v1/reviews/{review_id}", headers=_auth(data["token"]))
    assert resp.status_code == 204

    # Verify it's gone
    get_resp = await client.get(f"/api/v1/reviews/{review_id}", headers=_auth(data["token"]))
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_review_not_owner(client):
    """Cannot delete another student's review."""
    data = await _setup_student_with_enrollment(client, f"dno_{BASE_SUFFIX}")
    create_resp = await client.post("/api/v1/reviews/", json={
        "enrollment_id": data["enrollment"]["enrollment_id"],
        "overall_rating": 3,
    }, headers=_auth(data["token"]))
    review_id = create_resp.json()["review_id"]

    other_user = await register_user(client, f"dno2_{BASE_SUFFIX}")
    await create_student(client, f"dno2_{BASE_SUFFIX}", other_user["user_id"], data["academic"]["prog_id"])
    other_token = (await login_user(client, other_user["username"]))["access_token"]

    resp = await client.delete(f"/api/v1/reviews/{review_id}", headers=_auth(other_token))
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_course_review_summary(client):
    """Get review summary for a course."""
    data = await _setup_student_with_enrollment(client, f"cs_{BASE_SUFFIX}")
    await client.post("/api/v1/reviews/", json={
        "enrollment_id": data["enrollment"]["enrollment_id"],
        "overall_rating": 4,
        "teaching_rating": 5,
    }, headers=_auth(data["token"]))

    course_id = data["academic"]["course_id"]
    resp = await client.get(f"/api/v1/reviews/summary/course/{course_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_reviews"] >= 1
    assert body["average_overall"] is not None
    assert "distribution" in body
