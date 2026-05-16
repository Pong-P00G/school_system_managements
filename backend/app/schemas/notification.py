"""Pydantic schemas for Notifications."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationBase(BaseModel):
    """Fields required when creating a notification."""

    title: str = Field(..., max_length=200)
    message: str | None = None
    notification_type: str = Field(default="info", max_length=20)
    reference_type: str | None = Field(None, max_length=50)
    reference_id: str | None = Field(None, max_length=50)


class NotificationCreate(NotificationBase):
    """Schema for creating a new notification."""

    user_id: UUID


class NotificationUpdate(BaseModel):
    """Schema for updating a notification (mark as read)."""

    is_read: bool | None = None


class NotificationOut(NotificationBase):
    """Schema for notification response."""

    notification_id: int
    user_id: UUID
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListOut(BaseModel):
    """Paginated list of notifications."""

    notifications: list[NotificationOut]
    total: int
    unread_count: int = 0
