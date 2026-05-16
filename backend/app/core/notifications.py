"""Helper functions to create notifications for system events."""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification
from app.api.v1.notifications import broadcast_notification


async def notify_role_change(db: AsyncSession, user_id: UUID, action: str, role_name: str):
    """Notify user about role changes."""
    messages = {
        "create": f"New role '{role_name}' has been created",
        "update": f"Role '{role_name}' has been updated",
        "delete": f"Role '{role_name}' has been deleted",
    }
    
    notification = Notification(
        user_id=user_id,
        title="Role Management Update",
        message=messages.get(action, f"Role '{role_name}' was modified"),
        notification_type="info",
    )
    db.add(notification)
    await db.flush()
    await db.refresh(notification)
    
    await broadcast_notification(user_id, {
        "notification_id": notification.notification_id,
        "title": notification.title,
        "message": notification.message,
        "notification_type": notification.notification_type,
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
    })


async def notify_permission_change(db: AsyncSession, user_id: UUID, page_name: str, new_level: int):
    """Notify user about page permission changes."""
    notification = Notification(
        user_id=user_id,
        title="Permission Update",
        message=f"Access level for '{page_name}' changed to level {new_level}",
        notification_type="info",
    )
    db.add(notification)
    await db.flush()
    await db.refresh(notification)
    
    await broadcast_notification(user_id, {
        "notification_id": notification.notification_id,
        "title": notification.title,
        "message": notification.message,
        "notification_type": notification.notification_type,
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
    })
