"""Audit logging for role and permission changes."""

import json
import logging
from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from app.core.database import Base, utcnow

logger = logging.getLogger("audit")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    action = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(50), nullable=False)
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utcnow)


def log_audit(action: str, entity_type: str, entity_id, entity_name: str, user, changes: str = None):
    """Log to Python logger."""
    logger.info(
        "AUDIT: %s %s [%s] '%s' by %s | %s",
        action, entity_type, entity_id, entity_name,
        user.username if user else "system",
        changes or ""
    )
