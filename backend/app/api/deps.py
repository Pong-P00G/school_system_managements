from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRoleAssignment
from uuid import UUID

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
        
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
        
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise credentials_exception
        
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.personal_info),
            selectinload(User.role_assignments).selectinload(UserRoleAssignment.role)
        )
        .where(User.user_id == user_uuid)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require the current user to have an admin or super-admin role."""
    if not any(
        ra.role.role_name in ("admin", "super-admin")
        for ra in current_user.role_assignments
        if ra.is_active
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def get_current_teacher_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require the current user to have a teacher/faculty or admin role."""
    allowed = {"admin", "teacher", "faculty", "super-admin"}
    if not any(
        ra.role.role_name in allowed
        for ra in current_user.role_assignments
        if ra.is_active
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher or admin privileges required",
        )
    return current_user


async def get_current_super_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require the current user to have the super-admin role."""
    if not any(
        ra.role.role_name == "super-admin"
        for ra in current_user.role_assignments
        if ra.is_active
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super-admin privileges required",
        )
    return current_user
