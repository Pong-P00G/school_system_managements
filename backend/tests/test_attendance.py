"""Tests for the Attendance API endpoints.

Covers CRUD operations as well as permission checks.
Most endpoints require teacher_or_admin role; delete requires admin.
"""

from __future__ import annotations

import uuid

import pytest

from .helpers import (
    create_department,
    create_enrollment,
    create_faculty,
    login_user,
    register_user,
    setup_academic_graph,
    create_student,
)


def _headers(user: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {user['token']}"}


def _short() -> str:
    return uuid.uuid4().hex[:4]


# ---------------------------------------------------------------------------
# Helper — assign an existing role to a user via the public API
# ---------------------------------------------------------------------------


async def _assign_role(client, user_id: str, role_name: str) -> None:
    """Assign `role_name` to the user identified by `user_id`."""
    resp = await client.get("/api/v1/users/roles")
    assert resp.status_code == 200, resp.text
    roles = resp.json()
    role = next(r for r in roles if r["role_name"] == role_name)
    assign = await client.post(f"/api/v1/users/{user_id}/roles/{role['role_id']}")
    assert assign.status_code == 201, assign.text


# ---------------------------------------------------------------------------
# Composite setup — academic graph + registered users with roles
# ---------------------------------------------------------------------------


async def _setup_attendance_graph(client, suffix: str) -> dict:
    """Build the full dependency tree for attendance tests.

    Returns a dict with keys:
        faculty_user, faculty_headers, admin_user, admin_headers,
        student_user, student_headers, acad
    """
    suffix = f"{suffix}_{_short()}"
    acad = await setup_academic_graph(client, suffix)

    # --- Faculty user with "faculty" role ---
    fac_user = await register_user(client, f"{suffix}_fac")
    await _assign_role(client, fac_user["user_id"], "faculty")
    dept = await create_department(client, f"{suffix}_d2")
    faculty = await create_faculty(client, f"{suffix}_fac", fac_user["user_id"], dept["department_id"])
    fac_token = await login_user(client, fac_user["username"])
    faculty_user = {**fac_user, "faculty_id": faculty["faculty_id"], "token": fac_token["access_token"]}

    # --- Admin user with "admin" role ---
    adm_user = await register_user(client, f"{suffix}_adm")
    await _assign_role(client, adm_user["user_id"], "admin")
    adm_token = await login_user(client, adm_user["username"])
    admin_user = {**adm_user, "token": adm_token["access_token"]}

    # --- Student user (no special role needed) ---
    stu_user = await register_user(client, f"{suffix}_stu")
    student = await create_student(client, f"{suffix}_stu", stu_user["user_id"], acad["prog_id"])
    stu_token = await login_user(client, stu_user["username"])
    student_user = {**stu_user, "student_id": student["student_id"], "token": stu_token["access_token"]}

    # Enroll the student in the section so attendance can be recorded
    enrollment = await create_enrollment(client, student["student_id"], acad["section_id"])

    return {
        "faculty_user": faculty_user,
        "faculty_headers": _headers(faculty_user),
        "admin_user": admin_user,
        "admin_headers": _headers(admin_user),
        "student_user": student_user,
        "student_headers": _headers(student_user),
        "acad": acad,
        "enrollment_id": enrollment["enrollment_id"],
    }


# ===================================================================
# Tests
# ===================================================================


class TestRecordAttendance:
    @pytest.mark.asyncio
    async def test_record_present(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        payload = {
            "student_id": g["student_user"]["student_id"],
            "section_id": g["acad"]["section_id"],
            "class_date": "2025-03-15",
            "attendance_status": "present",
            "recorded_by": g["faculty_user"]["user_id"],
        }
        resp = await client.post("/api/v1/attendance/", json=payload, headers=g["faculty_headers"])
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["attendance_status"] == "present"
        assert data["student_id"] == g["student_user"]["student_id"]

    @pytest.mark.asyncio
    async def test_record_absent(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        payload = {
            "student_id": g["student_user"]["student_id"],
            "section_id": g["acad"]["section_id"],
            "class_date": "2025-03-16",
            "attendance_status": "absent",
            "recorded_by": g["faculty_user"]["user_id"],
        }
        resp = await client.post("/api/v1/attendance/", json=payload, headers=g["faculty_headers"])
        assert resp.status_code == 201, resp.text
        assert resp.json()["attendance_status"] == "absent"

    @pytest.mark.asyncio
    async def test_record_duplicate_returns_409(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        payload = {
            "student_id": g["student_user"]["student_id"],
            "section_id": g["acad"]["section_id"],
            "class_date": "2025-03-17",
            "attendance_status": "present",
            "recorded_by": g["faculty_user"]["user_id"],
        }
        resp1 = await client.post("/api/v1/attendance/", json=payload, headers=g["faculty_headers"])
        assert resp1.status_code == 201
        resp2 = await client.post("/api/v1/attendance/", json=payload, headers=g["faculty_headers"])
        assert resp2.status_code == 409

    @pytest.mark.asyncio
    async def test_record_as_student_returns_403(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        payload = {
            "student_id": g["student_user"]["student_id"],
            "section_id": g["acad"]["section_id"],
            "class_date": "2025-03-18",
            "attendance_status": "present",
            "recorded_by": g["faculty_user"]["user_id"],
        }
        resp = await client.post("/api/v1/attendance/", json=payload, headers=g["student_headers"])
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_record_nonexistent_section_returns_404(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        payload = {
            "student_id": g["student_user"]["student_id"],
            "section_id": 999999,
            "class_date": "2025-03-19",
            "attendance_status": "present",
            "recorded_by": g["faculty_user"]["user_id"],
        }
        resp = await client.post("/api/v1/attendance/", json=payload, headers=g["faculty_headers"])
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_record_unauthenticated_returns_401(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        payload = {
            "student_id": g["student_user"]["student_id"],
            "section_id": g["acad"]["section_id"],
            "class_date": "2025-03-20",
            "attendance_status": "present",
            "recorded_by": g["faculty_user"]["user_id"],
        }
        resp = await client.post("/api/v1/attendance/", json=payload)
        assert resp.status_code == 401


class TestBulkAttendance:
    @pytest.mark.asyncio
    async def test_record_bulk(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        payload = [
            {
                "section_id": g["acad"]["section_id"],
                "student_id": g["student_user"]["student_id"],
                "class_date": "2025-03-21",
                "attendance_status": "present",
                "recorded_by": g["faculty_user"]["user_id"],
            },
        ]
        resp = await client.post("/api/v1/attendance/bulk", json=payload, headers=g["faculty_headers"])
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_record_bulk_empty_returns_400(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        payload = []
        resp = await client.post("/api/v1/attendance/bulk", json=payload, headers=g["faculty_headers"])
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_record_bulk_as_student_returns_403(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        payload = [
            {
                "section_id": g["acad"]["section_id"],
                "student_id": g["student_user"]["student_id"],
                "class_date": "2025-03-23",
                "attendance_status": "present",
                "recorded_by": g["faculty_user"]["user_id"],
            },
        ]
        resp = await client.post("/api/v1/attendance/bulk", json=payload, headers=g["student_headers"])
        assert resp.status_code == 403


class TestListSectionAttendance:
    @pytest.mark.asyncio
    async def test_list_section_attendance(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        # First record some attendance
        payload = {
            "student_id": g["student_user"]["student_id"],
            "section_id": g["acad"]["section_id"],
            "class_date": "2025-04-01",
            "attendance_status": "present",
            "recorded_by": g["faculty_user"]["user_id"],
        }
        await client.post("/api/v1/attendance/", json=payload, headers=g["faculty_headers"])

        resp = await client.get(
            f"/api/v1/attendance/section/{g['acad']['section_id']}",
            headers=g["faculty_headers"],
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_section_pagination(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        resp = await client.get(
            f"/api/v1/attendance/section/{g['acad']['section_id']}?skip=0&limit=10",
            headers=g["faculty_headers"],
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list_section_as_student_returns_403(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        resp = await client.get(
            f"/api/v1/attendance/section/{g['acad']['section_id']}",
            headers=g["student_headers"],
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_list_section_nonexistent_returns_404(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        resp = await client.get(
            "/api/v1/attendance/section/999999",
            headers=g["faculty_headers"],
        )
        assert resp.status_code == 404


class TestGetMyAttendance:
    @pytest.mark.asyncio
    async def test_get_my_attendance(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        # Record some attendance for the student first
        payload = {
            "student_id": g["student_user"]["student_id"],
            "section_id": g["acad"]["section_id"],
            "class_date": "2025-04-05",
            "attendance_status": "present",
            "recorded_by": g["faculty_user"]["user_id"],
        }
        await client.post("/api/v1/attendance/", json=payload, headers=g["faculty_headers"])

        resp = await client.get("/api/v1/attendance/my", headers=g["student_headers"])
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_my_attendance_empty(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        resp = await client.get("/api/v1/attendance/my", headers=g["student_headers"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_my_attendance_unauthenticated_returns_401(self, client):
        resp = await client.get("/api/v1/attendance/my")
        assert resp.status_code == 401


class TestGetAttendanceRecord:
    @pytest.mark.asyncio
    async def test_get_attendance_record(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        payload = {
            "student_id": g["student_user"]["student_id"],
            "section_id": g["acad"]["section_id"],
            "class_date": "2025-04-10",
            "attendance_status": "present",
            "recorded_by": g["faculty_user"]["user_id"],
        }
        create = await client.post("/api/v1/attendance/", json=payload, headers=g["faculty_headers"])
        assert create.status_code == 201
        attendance_id = create.json()["attendance_id"]

        resp = await client.get(
            f"/api/v1/attendance/{attendance_id}", headers=g["faculty_headers"]
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["attendance_id"] == attendance_id

    @pytest.mark.asyncio
    async def test_get_attendance_record_not_found_returns_404(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        resp = await client.get("/api/v1/attendance/999999", headers=g["faculty_headers"])
        assert resp.status_code == 404


class TestUpdateAttendance:
    @pytest.mark.asyncio
    async def test_update_attendance(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        payload = {
            "student_id": g["student_user"]["student_id"],
            "section_id": g["acad"]["section_id"],
            "class_date": "2025-04-15",
            "attendance_status": "present",
            "recorded_by": g["faculty_user"]["user_id"],
        }
        create = await client.post("/api/v1/attendance/", json=payload, headers=g["faculty_headers"])
        attendance_id = create.json()["attendance_id"]

        resp = await client.put(
            f"/api/v1/attendance/{attendance_id}",
            json={"attendance_status": "absent"},
            headers=g["faculty_headers"],
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["attendance_status"] == "absent"

    @pytest.mark.asyncio
    async def test_update_attendance_not_found_returns_404(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        resp = await client.put(
            "/api/v1/attendance/999999",
            json={"attendance_status": "present"},
            headers=g["faculty_headers"],
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_attendance_as_student_returns_403(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        # Create with faculty
        payload = {
            "student_id": g["student_user"]["student_id"],
            "section_id": g["acad"]["section_id"],
            "class_date": "2025-04-20",
            "attendance_status": "present",
            "recorded_by": g["faculty_user"]["user_id"],
        }
        create = await client.post("/api/v1/attendance/", json=payload, headers=g["faculty_headers"])
        attendance_id = create.json()["attendance_id"]

        resp = await client.put(
            f"/api/v1/attendance/{attendance_id}",
            json={"attendance_status": "absent"},
            headers=g["student_headers"],
        )
        assert resp.status_code == 403


class TestDeleteAttendance:
    @pytest.mark.asyncio
    async def test_delete_attendance(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        payload = {
            "student_id": g["student_user"]["student_id"],
            "section_id": g["acad"]["section_id"],
            "class_date": "2025-04-25",
            "attendance_status": "present",
            "recorded_by": g["faculty_user"]["user_id"],
        }
        create = await client.post("/api/v1/attendance/", json=payload, headers=g["faculty_headers"])
        attendance_id = create.json()["attendance_id"]

        resp = await client.delete(
            f"/api/v1/attendance/{attendance_id}", headers=g["admin_headers"]
        )
        assert resp.status_code == 204, resp.text

    @pytest.mark.asyncio
    async def test_delete_attendance_as_faculty_returns_403(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        payload = {
            "student_id": g["student_user"]["student_id"],
            "section_id": g["acad"]["section_id"],
            "class_date": "2025-04-30",
            "attendance_status": "present",
            "recorded_by": g["faculty_user"]["user_id"],
        }
        create = await client.post("/api/v1/attendance/", json=payload, headers=g["faculty_headers"])
        attendance_id = create.json()["attendance_id"]

        resp = await client.delete(
            f"/api/v1/attendance/{attendance_id}", headers=g["faculty_headers"]
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_attendance_not_found_returns_404(self, client, suffix):
        g = await _setup_attendance_graph(client, suffix)
        resp = await client.delete("/api/v1/attendance/999999", headers=g["admin_headers"])
        assert resp.status_code == 404
