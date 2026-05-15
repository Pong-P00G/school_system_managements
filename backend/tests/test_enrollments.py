"""Integration tests for enrollment endpoints (capacity, grade, withdrawal)."""

import uuid

import pytest

# Module-level unique suffix to prevent collisions across test runs
BASE_SUFFIX = uuid.uuid4().hex[:6]


def _short() -> str:
    """Return a short 4-char hex string for use in DB field values."""
    return uuid.uuid4().hex[:4]


async def _setup_prerequisites(client, suffix: str) -> dict:
    """Create all entities needed for enrollment tests. Returns dict of IDs."""
    # 1. User
    resp = await client.post("/api/v1/auth/register", json={
        "username": f"u_{suffix}",
        "email": f"u_{suffix}@x.com",
        "password": "Password123",
    })
    assert resp.status_code == 201
    user_id = resp.json()["user_id"]

    # 2. Department (code max_length=10)
    sc = _short()
    resp = await client.post("/api/v1/departments/", json={
        "department_code": f"d{sc}",
        "department_name": f"Dept {suffix}",
        "is_active": True,
    })
    assert resp.status_code == 201
    dept_id = resp.json()["department_id"]

    # 3. Program (code max_length=20)
    resp = await client.post("/api/v1/programs/", json={
        "program_code": f"p_{_short()}",
        "program_name": f"Prog {suffix}",
        "department_id": dept_id,
        "degree_level": "Bachelor",
        "total_credits_required": 120,
    })
    assert resp.status_code == 201
    prog_id = resp.json()["program_id"]

    # 4. Course (code max_length=20)
    resp = await client.post("/api/v1/courses/", json={
        "course_code": f"c{_short()}",
        "course_name": f"Course {suffix}",
        "department_id": dept_id,
        "credits": 3,
    })
    assert resp.status_code == 201
    course_id = resp.json()["course_id"]

    # 5. Term (code max_length=20)
    resp = await client.post("/api/v1/terms/", json={
        "term_name": f"Term {suffix}",
        "term_code": f"t{_short()}",
        "academic_year": "2025-2026",
        "term_type": "spring",
        "start_date": "2025-01-15",
        "end_date": "2025-05-15",
        "status": "active",
    })
    assert resp.status_code == 201
    term_id = resp.json()["term_id"]

    # 6. Section (capacity=2 — for normal tests)
    sc2 = _short()
    resp = await client.post("/api/v1/sections/", json={
        "course_id": course_id,
        "term_id": term_id,
        "section_number": f"s{sc2}",
        "max_capacity": 2,
        "delivery_mode": "in-person",
        "status": "open",
    })
    assert resp.status_code == 201
    section_id = resp.json()["section_id"]

    # 7. Section (capacity=1 — for full-section tests)
    resp = await client.post("/api/v1/sections/", json={
        "course_id": course_id,
        "term_id": term_id,
        "section_number": f"sf{_short()}",
        "max_capacity": 1,
        "delivery_mode": "in-person",
        "status": "open",
    })
    assert resp.status_code == 201
    full_section_id = resp.json()["section_id"]

    # 8. Student (student_number max_length=20)
    resp = await client.post("/api/v1/students/", json={
        "user_id": str(user_id),
        "student_number": f"sn{_short()}",
        "program_id": prog_id,
        "enrollment_date": "2025-01-15",
        "enrollment_status": "active",
    })
    assert resp.status_code == 201
    student_id = resp.json()["student_id"]

    return {
        "user_id": user_id,
        "dept_id": dept_id,
        "prog_id": prog_id,
        "course_id": course_id,
        "term_id": term_id,
        "section_id": section_id,
        "full_section_id": full_section_id,
        "student_id": student_id,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enroll_student_success(client):
    """Create enrollment → verify by GET → verify section count → list includes it."""
    p = await _setup_prerequisites(client, f"es_{BASE_SUFFIX}")

    resp = await client.post("/api/v1/enrollments/", json={
        "student_id": str(p["student_id"]),
        "section_id": p["section_id"],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["enrollment_status"] == "enrolled"
    assert data["student_id"] == str(p["student_id"])
    assert data["section_id"] == p["section_id"]
    eid = data["enrollment_id"]

    # GET by ID
    resp = await client.get(f"/api/v1/enrollments/{eid}")
    assert resp.status_code == 200
    assert resp.json()["enrollment_id"] == eid

    # Section enrolled_count incremented
    resp = await client.get(f"/api/v1/sections/{p['section_id']}")
    assert resp.json()["enrolled_count"] == 1

    # List filters by section_id
    resp = await client.get(f"/api/v1/enrollments/?section_id={p['section_id']}")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_enroll_duplicate_rejected(client):
    """Enrolling same student in same section twice returns 400."""
    p = await _setup_prerequisites(client, f"dup_{BASE_SUFFIX}")

    resp = await client.post("/api/v1/enrollments/", json={
        "student_id": str(p["student_id"]),
        "section_id": p["section_id"],
    })
    assert resp.status_code == 201

    resp = await client.post("/api/v1/enrollments/", json={
        "student_id": str(p["student_id"]),
        "section_id": p["section_id"],
    })
    assert resp.status_code == 400
    assert "already enrolled" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_enroll_section_full(client):
    """Enrolling into a section at capacity returns 400."""
    p = await _setup_prerequisites(client, f"full_{BASE_SUFFIX}")

    # Second student to attempt enrollment into the full section
    resp = await client.post("/api/v1/auth/register", json={
        "username": f"uf_{BASE_SUFFIX}",
        "email": f"uf_{BASE_SUFFIX}@x.com",
        "password": "Password123",
    })
    user2_id = resp.json()["user_id"]
    resp = await client.post("/api/v1/students/", json={
        "user_id": str(user2_id),
        "student_number": f"sf{_short()}",
        "program_id": p["prog_id"],
        "enrollment_date": "2025-01-15",
    })
    student2_id = resp.json()["student_id"]

    # Fill the capacity-1 section
    resp = await client.post("/api/v1/enrollments/", json={
        "student_id": str(p["student_id"]),
        "section_id": p["full_section_id"],
    })
    assert resp.status_code == 201

    # Second student — should be rejected
    resp = await client.post("/api/v1/enrollments/", json={
        "student_id": str(student2_id),
        "section_id": p["full_section_id"],
    })
    assert resp.status_code == 400
    assert "full" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_enroll_nonexistent_student(client):
    """Enrolling a non-existent UUID student returns 404."""
    p = await _setup_prerequisites(client, f"ns_{BASE_SUFFIX}")

    resp = await client.post("/api/v1/enrollments/", json={
        "student_id": "00000000-0000-0000-0000-000000000000",
        "section_id": p["section_id"],
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_enroll_nonexistent_section(client):
    """Enrolling in a non-existent section returns 404."""
    p = await _setup_prerequisites(client, f"nx_{BASE_SUFFIX}")

    resp = await client.post("/api/v1/enrollments/", json={
        "student_id": str(p["student_id"]),
        "section_id": 99999999,
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_submit_grade(client):
    """Submit grade → status becomes 'completed', grade/final_grade set."""
    p = await _setup_prerequisites(client, f"gr_{BASE_SUFFIX}")

    resp = await client.post("/api/v1/enrollments/", json={
        "student_id": str(p["student_id"]),
        "section_id": p["section_id"],
    })
    eid = resp.json()["enrollment_id"]

    resp = await client.post(
        f"/api/v1/enrollments/{eid}/grade",
        params={"grade": "A", "grade_points": 4.0},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["grade"] == "A"
    assert data["final_grade"] == "A"
    assert data["grade_points"] == 4.0
    assert data["enrollment_status"] == "completed"
    assert data["grade_submitted_date"] is not None


@pytest.mark.asyncio
async def test_grade_nonexistent_enrollment(client):
    """Grading a non-existent enrollment returns 404."""
    resp = await client.post(
        "/api/v1/enrollments/99999999/grade",
        params={"grade": "A"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_withdraw_from_enrollment(client):
    """Withdraw → status='withdrawn', reason stored, count decremented."""
    p = await _setup_prerequisites(client, f"wd_{BASE_SUFFIX}")

    resp = await client.post("/api/v1/enrollments/", json={
        "student_id": str(p["student_id"]),
        "section_id": p["section_id"],
    })
    eid = resp.json()["enrollment_id"]

    # enrolled_count before withdrawal
    resp = await client.get(f"/api/v1/sections/{p['section_id']}")
    assert resp.json()["enrolled_count"] == 1

    # Withdraw
    resp = await client.post(
        f"/api/v1/enrollments/{eid}/withdraw",
        params={"reason": "Changed schedule"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["enrollment_status"] == "withdrawn"
    assert data["withdrawal_reason"] == "Changed schedule"
    assert data["withdrawal_date"] is not None

    # enrolled_count decremented
    resp = await client.get(f"/api/v1/sections/{p['section_id']}")
    assert resp.json()["enrolled_count"] == 0


@pytest.mark.asyncio
async def test_withdraw_completed_enrollment_fails(client):
    """Withdrawing from a completed enrollment returns 400."""
    p = await _setup_prerequisites(client, f"wn_{BASE_SUFFIX}")

    resp = await client.post("/api/v1/enrollments/", json={
        "student_id": str(p["student_id"]),
        "section_id": p["section_id"],
    })
    eid = resp.json()["enrollment_id"]

    # Complete it via grade submission
    await client.post(
        f"/api/v1/enrollments/{eid}/grade",
        params={"grade": "B", "grade_points": 3.0},
    )

    # Try withdrawing a completed enrollment → 400
    resp = await client.post(f"/api/v1/enrollments/{eid}/withdraw")
    assert resp.status_code == 400
    assert "Can only withdraw from active enrollments" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_get_enrollment_not_found(client):
    """GET a non-existent enrollment ID returns 404."""
    resp = await client.get("/api/v1/enrollments/99999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_enrollments_filters(client):
    """List supports filters: student_id, enrollment_status."""
    p = await _setup_prerequisites(client, f"li_{BASE_SUFFIX}")

    resp = await client.post("/api/v1/enrollments/", json={
        "student_id": str(p["student_id"]),
        "section_id": p["section_id"],
    })
    eid = resp.json()["enrollment_id"]

    # Filter by student_id
    resp = await client.get(f"/api/v1/enrollments/?student_id={p['student_id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert any(e["enrollment_id"] == eid for e in body["enrollments"])

    # Filter by enrollment_status
    resp = await client.get("/api/v1/enrollments/?enrollment_status=enrolled")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1
