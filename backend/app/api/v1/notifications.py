"""Notification management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import (
    NotificationOut,
    NotificationListOut,
    NotificationCreate,
    NotificationUpdate,
)
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/", response_model=NotificationListOut)
async def list_notifications(
    unread_only: bool = Query(False),
    notification_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List notifications for the current user with optional filters and pagination."""
    query = select(Notification).where(Notification.user_id == current_user.user_id)
    count_query = select(func.count(Notification.notification_id)).where(
        Notification.user_id == current_user.user_id
    )
    unread_query = select(func.count(Notification.notification_id)).where(
        Notification.user_id == current_user.user_id,
        Notification.is_read == False,
    )

    if unread_only:
        query = query.where(Notification.is_read == False)
        count_query = count_query.where(Notification.is_read == False)

    if notification_type:
        query = query.where(Notification.notification_type == notification_type)
        count_query = count_query.where(
            Notification.notification_type == notification_type
        )

    # Get unread count
    unread_result = await db.execute(unread_query)
    unread_count = unread_result.scalar()

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(
        query.offset(skip)
        .limit(limit)
        .order_by(Notification.created_at.desc())
    )
    notifications = result.scalars().all()
    return NotificationListOut(
        notifications=notifications, total=total, unread_count=unread_count
    )


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the count of unread notifications for the current user."""
    result = await db.execute(
        select(func.count(Notification.notification_id)).where(
            Notification.user_id == current_user.user_id,
            Notification.is_read == False,
        )
    )
    count = result.scalar()
    return {"unread_count": count}


@router.get("/{notification_id}", response_model=NotificationOut)
async def get_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single notification by ID."""
    result = await db.execute(
        select(Notification).where(
            Notification.notification_id == notification_id,
            Notification.user_id == current_user.user_id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )
    return notification


@router.post("/", response_model=NotificationOut, status_code=status.HTTP_201_CREATED)
async def create_notification(
    data: NotificationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new notification (admin/system use)."""
    # Verify user exists
    user_result = await db.execute(
        select(User).where(User.user_id == data.user_id)
    )
    if not user_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    notification = Notification(**data.model_dump())
    db.add(notification)
    await db.flush()
    await db.refresh(notification)
    return notification


@router.put("/{notification_id}/read", response_model=NotificationOut)
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a single notification as read."""
    result = await db.execute(
        select(Notification).where(
            Notification.notification_id == notification_id,
            Notification.user_id == current_user.user_id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )

    notification.is_read = True
    await db.flush()
    await db.refresh(notification)
    return notification


@router.put("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read for the current user."""
    await db.execute(
        update(Notification)
        .where(
            Notification.user_id == current_user.user_id,
            Notification.is_read == False,
        )
        .values(is_read=True)
    )
    await db.flush()
    return {"message": "All notifications marked as read"}


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a notification."""
    result = await db.execute(
        select(Notification).where(
            Notification.notification_id == notification_id,
            Notification.user_id == current_user.user_id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )

    await db.delete(notification)
    await db.flush()
    return None
