"""Pydantic schemas for user-related endpoints."""

from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


# --- Auth schemas ---
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- User schemas ---
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    is_active: bool = True
    is_verified: bool = False


class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str | None = None
    is_active: bool | None = None
    is_verified: bool | None = None


class UserPersonalInfoBase(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    middle_name: str | None = None
    preferred_name: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    nationality: str | None = None


class UserPersonalInfoCreate(UserPersonalInfoBase):
    pass


class UserPersonalInfoOut(UserPersonalInfoBase):
    first_name: str
    last_name: str
    middle_name: str | None = None
    preferred_name: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    nationality: str | None = None

    model_config = {"from_attributes": True}


class UserRoleOut(BaseModel):
    role_id: int
    role_name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class UserRoleAssignmentOut(BaseModel):
    role: UserRoleOut
    is_active: bool

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    user_id: UUID
    username: str
    email: str
    is_active: bool
    is_verified: bool
    last_login: datetime | None = None
    created_at: datetime | None = None
    personal_info: UserPersonalInfoOut | None = None

    model_config = {"from_attributes": True}


class UserWithRolesOut(BaseModel):
    user_id: UUID
    username: str
    email: str
    is_active: bool
    is_verified: bool
    last_login: datetime | None = None
    created_at: datetime | None = None
    personal_info: UserPersonalInfoOut | None = None
    roles: list[UserRoleAssignmentOut] = Field(default_factory=list, validation_alias="role_assignments")

    model_config = {"from_attributes": True}


class UserListOut(BaseModel):
    users: list[UserWithRolesOut]
    total: int
