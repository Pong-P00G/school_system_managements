"""Comprehensive API tests for the notification endpoints."""

from __future__ import annotations

import uuid

import pytest

from .helpers import (
    login_user,
    register_user,
)

BASE_SUFFIX = uuid.uuid4().hex[:6]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _headers(user: dict) -> dict[str, str]:
    """Return authorization headers for the given user dict (must contain 'token')."""
    return {"Authorization": f"Bearer {user['token']}"}


async def _logged_in(client, suffix: str) -> dict:
    """Register + login a user and return user data + token."""
    user = await register_user(client, suffix)
    token = await login_user(client, user["username"])
    user["token"] = token["access_token"]
    return user


async def _create_notification(client, user_id: str, headers: dict, **overrides) -> dict:
    """Helper to create a notification via the API."""
    payload = {
        "user_id": user_id,
        "title": f"Test Notification {uuid.uuid4().hex[:4]}",
        "message": "This is a test notification.",
        "notification_type": overrides.get("notification_type", "info"),
    }
    payload.update(overrides)
    resp = await client.post("/api/v1/notifications/", json=payload, headers=headers)
    assert resp.status_code == 201, f"Create notification failed: {resp.text}"
    return resp.json()


# ---------------------------------------------------------------------------
# LIST
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_notifications_empty(client):
    """Listing notifications when none exist returns empty list."""
    user = await _logged_in(client, f"lem_{BASE_SUFFIX}")
    resp = await client.get("/api/v1/notifications/", headers=_headers(user))
    assert resp.status_code == 200
    data = resp.json()
    assert data["notifications"] == []
    assert data["total"] == 0
    assert data["unread_count"] == 0


@pytest.mark.asyncio
async def test_list_notifications_pagination(client):
    """List notifications respects pagination parameters."""
    # Create a user and a second user to send notifications to
    creator = await _logged_in(client, f"lp1_{BASE_SUFFIX}")
    recipient = await _logged_in(client, f"lp2_{BASE_SUFFIX}")

    # Create a few notifications
    for i in range(3):
        await _create_notification(client, recipient["user_id"], _headers(creator),
                                   title=f"Notif {i} {uuid.uuid4().hex[:4]}")

    # Test with limit
    resp = await client.get(
        "/api/v1/notifications/?limit=2",
        headers=_headers(recipient),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["notifications"]) == 2
    assert data["total"] == 3

    # Test with skip
    resp = await client.get(
        "/api/v1/notifications/?skip=2&limit=10",
        headers=_headers(recipient),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["notifications"]) == 1


@pytest.mark.asyncio
async def test_list_notifications_order(client):
    """Notifications are returned in reverse chronological order."""
    creator = await _logged_in(client, f"lo1_{BASE_SUFFIX}")
    recipient = await _logged_in(client, f"lo2_{BASE_SUFFIX}")

    n1 = await _create_notification(client, recipient["user_id"], _headers(creator),
                                    title=f"First {uuid.uuid4().hex[:4]}")
    n2 = await _create_notification(client, recipient["user_id"], _headers(creator),
                                    title=f"Second {uuid.uuid4().hex[:4]}")

    resp = await client.get("/api/v1/notifications/", headers=_headers(recipient))
    data = resp.json()
    # Most recent first
    assert data["notifications"][0]["notification_id"] == n2["notification_id"]
    assert data["notifications"][1]["notification_id"] == n1["notification_id"]


# ---------------------------------------------------------------------------
# FILTERS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_notifications_unread_only(client):
    """Filter only unread notifications."""
    creator = await _logged_in(client, f"lu1_{BASE_SUFFIX}")
    recipient = await _logged_in(client, f"lu2_{BASE_SUFFIX}")

    n1 = await _create_notification(client, recipient["user_id"], _headers(creator),
                                    title=f"Unread1 {uuid.uuid4().hex[:4]}")
    n2 = await _create_notification(client, recipient["user_id"], _headers(creator),
                                    title=f"Unread2 {uuid.uuid4().hex[:4]}")

    # Mark n1 as read
    await client.put(
        f"/api/v1/notifications/{n1['notification_id']}/read",
        headers=_headers(recipient),
    )

    resp = await client.get(
        "/api/v1/notifications/?unread_only=true",
        headers=_headers(recipient),
    )
    assert resp.status_code == 200
    data = resp.json()
    # Only n2 should be unread now
    assert data["total"] == 1
    assert data["unread_count"] == 1
    assert len(data["notifications"]) == 1
    assert data["notifications"][0]["notification_id"] == n2["notification_id"]
    assert data["notifications"][0]["is_read"] is False


@pytest.mark.asyncio
async def test_list_notifications_type_filter(client):
    """Filter notifications by type."""
    creator = await _logged_in(client, f"lt1_{BASE_SUFFIX}")
    recipient = await _logged_in(client, f"lt2_{BASE_SUFFIX}")

    await _create_notification(client, recipient["user_id"], _headers(creator),
                               notification_type="info", title=f"Info {uuid.uuid4().hex[:4]}")
    await _create_notification(client, recipient["user_id"], _headers(creator),
                               notification_type="warning", title=f"Warn {uuid.uuid4().hex[:4]}")

    resp = await client.get(
        "/api/v1/notifications/?notification_type=warning",
        headers=_headers(recipient),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["notifications"][0]["notification_type"] == "warning"


# ---------------------------------------------------------------------------
# UNREAD COUNT
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_unread_count(client):
    """Getting unread count returns correct tally."""
    creator = await _logged_in(client, f"uc1_{BASE_SUFFIX}")
    recipient = await _logged_in(client, f"uc2_{BASE_SUFFIX}")

    resp = await client.get("/api/v1/notifications/unread-count", headers=_headers(recipient))
    assert resp.status_code == 200
    assert resp.json()["unread_count"] == 0

    await _create_notification(client, recipient["user_id"], _headers(creator),
                               title=f"N1 {uuid.uuid4().hex[:4]}")
    await _create_notification(client, recipient["user_id"], _headers(creator),
                               title=f"N2 {uuid.uuid4().hex[:4]}")

    resp = await client.get("/api/v1/notifications/unread-count", headers=_headers(recipient))
    assert resp.status_code == 200
    assert resp.json()["unread_count"] == 2


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_notification(client):
    """Create a notification successfully."""
    creator = await _logged_in(client, f"cn1_{BASE_SUFFIX}")
    recipient = await _logged_in(client, f"cn2_{BASE_SUFFIX}")

    payload = {
        "user_id": recipient["user_id"],
        "title": "Welcome!",
        "message": "You have been enrolled in a course.",
        "notification_type": "success",
    }
    resp = await client.post("/api/v1/notifications/", json=payload, headers=_headers(creator))
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == payload["title"]
    assert data["message"] == payload["message"]
    assert data["notification_type"] == payload["notification_type"]
    assert data["user_id"] == payload["user_id"]
    assert data["is_read"] is False
    assert "notification_id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_notification_minimal(client):
    """Create a notification with only required fields."""
    creator = await _logged_in(client, f"cnm1_{BASE_SUFFIX}")
    recipient = await _logged_in(client, f"cnm2_{BASE_SUFFIX}")

    payload = {
        "user_id": recipient["user_id"],
        "title": "Minimal",
    }
    resp = await client.post("/api/v1/notifications/", json=payload, headers=_headers(creator))
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Minimal"
    assert data["message"] is None
    assert data["notification_type"] == "info"  # default


@pytest.mark.asyncio
async def test_create_notification_user_not_found(client):
    """Creating a notification for a non-existent user returns 404."""
    creator = await _logged_in(client, f"cnf_{BASE_SUFFIX}")
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    payload = {
        "user_id": fake_uuid,
        "title": "To nowhere",
    }
    resp = await client.post("/api/v1/notifications/", json=payload, headers=_headers(creator))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_notification_unauthenticated(client):
    """Creating a notification without auth returns 401 (Unauthorized)."""
    recipient = await register_user(client, f"cnu_{BASE_SUFFIX}")
    payload = {
        "user_id": recipient["user_id"],
        "title": "No auth",
    }
    resp = await client.post("/api/v1/notifications/", json=payload)
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET BY ID
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_notification(client):
    """Get a specific notification by ID."""
    creator = await _logged_in(client, f"gn1_{BASE_SUFFIX}")
    recipient = await _logged_in(client, f"gn2_{BASE_SUFFIX}")

    created = await _create_notification(client, recipient["user_id"], _headers(creator),
                                         title=f"GetMe {uuid.uuid4().hex[:4]}")

    resp = await client.get(
        f"/api/v1/notifications/{created['notification_id']}",
        headers=_headers(recipient),
    )
    assert resp.status_code == 200
    assert resp.json()["notification_id"] == created["notification_id"]


@pytest.mark.asyncio
async def test_get_notification_not_found(client):
    """Get a non-existent notification returns 404."""
    user = await _logged_in(client, f"gnf_{BASE_SUFFIX}")
    resp = await client.get("/api/v1/notifications/999999", headers=_headers(user))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_notification_wrong_user(client):
    """A user cannot fetch another user's notification."""
    creator = await _logged_in(client, f"gwu1_{BASE_SUFFIX}")
    recipient = await _logged_in(client, f"gwu2_{BASE_SUFFIX}")
    outsider = await _logged_in(client, f"gwu3_{BASE_SUFFIX}")

    created = await _create_notification(client, recipient["user_id"], _headers(creator),
                                         title=f"Mine {uuid.uuid4().hex[:4]}")

    resp = await client.get(
        f"/api/v1/notifications/{created['notification_id']}",
        headers=_headers(outsider),
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# MARK READ
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mark_notification_read(client):
    """Mark a single notification as read."""
    creator = await _logged_in(client, f"mr1_{BASE_SUFFIX}")
    recipient = await _logged_in(client, f"mr2_{BASE_SUFFIX}")

    created = await _create_notification(client, recipient["user_id"], _headers(creator),
                                         title=f"MarkRead {uuid.uuid4().hex[:4]}")
    assert created["is_read"] is False

    resp = await client.put(
        f"/api/v1/notifications/{created['notification_id']}/read",
        headers=_headers(recipient),
    )
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True

    # Verify persisted
    get_resp = await client.get(
        f"/api/v1/notifications/{created['notification_id']}",
        headers=_headers(recipient),
    )
    assert get_resp.json()["is_read"] is True


@pytest.mark.asyncio
async def test_mark_notification_read_not_found(client):
    """Mark a non-existent notification as read returns 404."""
    user = await _logged_in(client, f"mrnf_{BASE_SUFFIX}")
    resp = await client.put("/api/v1/notifications/999999/read", headers=_headers(user))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_mark_notification_read_wrong_user(client):
    """A user cannot mark another user's notification as read."""
    creator = await _logged_in(client, f"mwu1_{BASE_SUFFIX}")
    recipient = await _logged_in(client, f"mwu2_{BASE_SUFFIX}")
    outsider = await _logged_in(client, f"mwu3_{BASE_SUFFIX}")

    created = await _create_notification(client, recipient["user_id"], _headers(creator),
                                         title=f"NotYours {uuid.uuid4().hex[:4]}")

    resp = await client.put(
        f"/api/v1/notifications/{created['notification_id']}/read",
        headers=_headers(outsider),
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# MARK ALL READ
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mark_all_read(client):
    """Mark all notifications as read for the current user."""
    creator = await _logged_in(client, f"mar1_{BASE_SUFFIX}")
    recipient = await _logged_in(client, f"mar2_{BASE_SUFFIX}")

    n1 = await _create_notification(client, recipient["user_id"], _headers(creator),
                                    title=f"MAR-A {uuid.uuid4().hex[:4]}")
    n2 = await _create_notification(client, recipient["user_id"], _headers(creator),
                                    title=f"MAR-B {uuid.uuid4().hex[:4]}")

    resp = await client.put("/api/v1/notifications/read-all", headers=_headers(recipient))
    assert resp.status_code == 200
    assert resp.json()["message"] == "All notifications marked as read"

    # Verify both are read
    for n_id in [n1["notification_id"], n2["notification_id"]]:
        get_resp = await client.get(
            f"/api/v1/notifications/{n_id}",
            headers=_headers(recipient),
        )
        assert get_resp.json()["is_read"] is True

    # Unread count should be 0
    uc_resp = await client.get("/api/v1/notifications/unread-count", headers=_headers(recipient))
    assert uc_resp.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_mark_all_read_only_affects_own(client):
    """Mark-all-read only marks the current user's notifications."""
    creator = await _logged_in(client, f"mao1_{BASE_SUFFIX}")
    user_a = await _logged_in(client, f"mao2_{BASE_SUFFIX}")
    user_b = await _logged_in(client, f"mao3_{BASE_SUFFIX}")

    notif_a = await _create_notification(client, user_a["user_id"], _headers(creator),
                                         title=f"A {uuid.uuid4().hex[:4]}")
    notif_b = await _create_notification(client, user_b["user_id"], _headers(creator),
                                         title=f"B {uuid.uuid4().hex[:4]}")

    # User A marks all as read
    await client.put("/api/v1/notifications/read-all", headers=_headers(user_a))

    # User A's notification should be read
    a_resp = await client.get(
        f"/api/v1/notifications/{notif_a['notification_id']}",
        headers=_headers(user_a),
    )
    assert a_resp.json()["is_read"] is True

    # User B's notification should still be unread
    b_resp = await client.get(
        f"/api/v1/notifications/{notif_b['notification_id']}",
        headers=_headers(user_b),
    )
    assert b_resp.json()["is_read"] is False


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_notification(client):
    """Delete a notification."""
    creator = await _logged_in(client, f"dn1_{BASE_SUFFIX}")
    recipient = await _logged_in(client, f"dn2_{BASE_SUFFIX}")

    created = await _create_notification(client, recipient["user_id"], _headers(creator),
                                         title=f"DeleteMe {uuid.uuid4().hex[:4]}")

    resp = await client.delete(
        f"/api/v1/notifications/{created['notification_id']}",
        headers=_headers(recipient),
    )
    assert resp.status_code == 204

    # Verify it's gone
    get_resp = await client.get(
        f"/api/v1/notifications/{created['notification_id']}",
        headers=_headers(recipient),
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_notification_not_found(client):
    """Delete a non-existent notification returns 404."""
    user = await _logged_in(client, f"dnf_{BASE_SUFFIX}")
    resp = await client.delete("/api/v1/notifications/999999", headers=_headers(user))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_notification_wrong_user(client):
    """A user cannot delete another user's notification."""
    creator = await _logged_in(client, f"dwu1_{BASE_SUFFIX}")
    recipient = await _logged_in(client, f"dwu2_{BASE_SUFFIX}")
    outsider = await _logged_in(client, f"dwu3_{BASE_SUFFIX}")

    created = await _create_notification(client, recipient["user_id"], _headers(creator),
                                         title=f"NotYoursDel {uuid.uuid4().hex[:4]}")

    resp = await client.delete(
        f"/api/v1/notifications/{created['notification_id']}",
        headers=_headers(outsider),
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_notifications_unauthenticated(client):
    """Listing notifications without auth returns 401 (Unauthorized)."""
    resp = await client.get("/api/v1/notifications/")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_unread_count_unauthenticated(client):
    """Getting unread count without auth returns 401 (Unauthorized)."""
    resp = await client.get("/api/v1/notifications/unread-count")
    assert resp.status_code == 401
