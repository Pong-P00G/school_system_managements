from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRoleAssignment
from uuid import UUID
from typing import Optional

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    access_token: Optional[str] = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    # Cookie takes priority; fall back to Bearer header
    raw_token = access_token or (credentials.credentials if credentials else None)

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(raw_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    result = await db.execute(
        select(User)
        .options(
            selectinload(User.personal_info),
            selectinload(User.role_assignments).selectinload(UserRoleAssignment.role),
        )
        .where(User.user_id == user_uuid)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if not any(ra.role.role_name in ("admin", "super-admin") for ra in current_user.role_assignments if ra.is_active):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user


async def get_current_teacher_or_admin(current_user: User = Depends(get_current_user)) -> User:
    allowed = {"admin", "teacher", "faculty", "professor", "super-admin"}
    if not any(ra.role.role_name in allowed for ra in current_user.role_assignments if ra.is_active):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher or admin privileges required")
    return current_user


async def get_current_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if not any(ra.role.role_name == "super-admin" for ra in current_user.role_assignments if ra.is_active):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super-admin privileges required")
    return current_user
