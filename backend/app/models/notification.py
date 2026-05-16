"""Notification model for in-app notifications."""

from datetime import datetime
from app.core.database import utcnow

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Notification(Base):
    """In-app notification for users."""

    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    notification_type = Column(
        String(20), nullable=False, default="info"
    )  # info, success, warning, error
    reference_type = Column(String(50), nullable=True)  # e.g., "assignment", "enrollment", "grade"
    reference_id = Column(String(50), nullable=True)  # ID of the referenced entity
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("ix_notifications_user_unread", "user_id", "is_read"),
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.notification_id}, user={self.user_id}, type={self.notification_type}, read={self.is_read})>"
