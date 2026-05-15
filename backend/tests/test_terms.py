"""Comprehensive API tests for the academic terms endpoint (CRUD + current)."""

from __future__ import annotations

import uuid

import pytest

from .helpers import (
    create_term,
    _short,
)

BASE_SUFFIX = uuid.uuid4().hex[:6]


@pytest.mark.asyncio
async def test_create_term(client):
    """Create an academic term successfully."""
    resp = await client.post("/api/v1/terms/", json={
        "term_name": f"Test Term {BASE_SUFFIX}",
        "term_code": f"t{_short()}",
        "academic_year": "2025-2026",
        "term_type": "spring",
        "start_date": "2025-01-15",
        "end_date": "2025-05-15",
        "status": "active",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["term_name"] == f"Test Term {BASE_SUFFIX}"
    assert data["term_type"] == "spring"
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_list_terms(client):
    """List terms returns paginated results."""
    await create_term(client, f"tl_{BASE_SUFFIX}")
    resp = await client.get("/api/v1/terms/")
    assert resp.status_code == 200
    data = resp.json()
    assert "terms" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_term(client):
    """Get a term by ID."""
    term = await create_term(client, f"tg_{BASE_SUFFIX}")
    resp = await client.get(f"/api/v1/terms/{term['term_id']}")
    assert resp.status_code == 200
    assert resp.json()["term_id"] == term["term_id"]


@pytest.mark.asyncio
async def test_get_term_not_found(client):
    """Get a non-existent term returns 404."""
    resp = await client.get("/api/v1/terms/99999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_term(client):
    """Update a term."""
    term = await create_term(client, f"tu_{BASE_SUFFIX}")
    resp = await client.put(
        f"/api/v1/terms/{term['term_id']}",
        json={"term_name": "Updated Term", "status": "completed"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["term_name"] == "Updated Term"
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_delete_term(client):
    """Delete a term."""
    term = await create_term(client, f"td_{BASE_SUFFIX}")
    resp = await client.delete(f"/api/v1/terms/{term['term_id']}")
    assert resp.status_code == 204

    get_resp = await client.get(f"/api/v1/terms/{term['term_id']}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_term_duplicate_code(client):
    """Creating a term with duplicate code returns 409."""
    code = f"tx{_short()}"
    await create_term(client, f"tx_{BASE_SUFFIX}", term_code=code)

    resp = await client.post("/api/v1/terms/", json={
        "term_name": "Duplicate Term",
        "term_code": code,
        "academic_year": "2025-2026",
        "term_type": "spring",
        "start_date": "2025-01-15",
        "end_date": "2025-05-15",
        "status": "active",
    })
    assert resp.status_code == 409
    assert "already exists" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_terms_filters(client):
    """List terms supports filters."""
    await create_term(client, f"tf_{BASE_SUFFIX}")

    # Filter by academic_year
    resp = await client.get("/api/v1/terms/?academic_year=2025-2026")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1

    # Filter by term_type
    resp = await client.get("/api/v1/terms/?term_type=spring")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1

    # Filter by status
    resp = await client.get("/api/v1/terms/?status=active")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_current_active_term(client):
    """Get the currently active term."""
    await create_term(client, f"tca_{BASE_SUFFIX}", status="active")

    resp = await client.get("/api/v1/terms/current/active")
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


@pytest.mark.asyncio
async def test_get_upcoming_terms(client):
    """Get upcoming terms."""
    await create_term(client, f"tcu_{BASE_SUFFIX}", status="upcoming",
                      start_date="2026-01-15", end_date="2026-05-15")

    resp = await client.get("/api/v1/terms/current/upcoming")
    assert resp.status_code == 200
    data = resp.json()
    assert "terms" in data


@pytest.mark.asyncio
async def test_pagination(client):
    """Terms list respects pagination."""
    resp = await client.get("/api/v1/terms/?skip=0&limit=5")
    assert resp.status_code == 200
    assert len(resp.json()["terms"]) <= 5
