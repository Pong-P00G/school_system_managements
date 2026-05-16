import uuid
from datetime import datetime
from app.core.database import utcnow
from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Text, Date, ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    role_assignments = relationship("UserRoleAssignment", back_populates="user", lazy="selectin", foreign_keys="UserRoleAssignment.user_id", passive_deletes="all")
    personal_info = relationship("UserPersonalInfo", back_populates="user", uselist=False, lazy="selectin", passive_deletes="all")
    notifications = relationship("Notification", back_populates="user", lazy="selectin", passive_deletes="all")
    attendance_records = relationship("Attendance", back_populates="recorder", lazy="selectin", passive_deletes="all")


class UserRole(Base):
    __tablename__ = "user_roles"

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_system_role = Column(Boolean, default=False)
    role_level = Column(Integer, default=99)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    assignments = relationship("UserRoleAssignment", back_populates="role", passive_deletes="all")


class UserRoleAssignment(Base):
    __tablename__ = "user_role_assignments"

    assignment_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("user_roles.role_id", ondelete="CASCADE"), nullable=False)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    assigned_date = Column(DateTime, default=utcnow)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    # Relationships
    user = relationship("User", back_populates="role_assignments", foreign_keys=[user_id])
    role = relationship("UserRole", back_populates="assignments")


class UserPersonalInfo(Base):
    __tablename__ = "user_personal_info"

    info_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    preferred_name = Column(String(100), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    nationality = Column(String(100), nullable=True)
    profile_picture_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    user = relationship("User", back_populates="personal_info")


class Permission(Base):
    __tablename__ = "permissions"

    permission_id = Column(Integer, primary_key=True, autoincrement=True)
    permission_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("user_roles.role_id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.permission_id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),)


class PagePermission(Base):
    __tablename__ = "page_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    page_path = Column(String(200), nullable=False)
    page_name = Column(String(100), nullable=False)
    min_role_level = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (UniqueConstraint("page_path", name="uq_page_path"),)
