"""User management endpoints with full CRUD operations."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.user import User, UserPersonalInfo, UserRoleAssignment, UserRole
from app.api.deps import get_current_user
from app.schemas.user import (
    UserOut, UserListOut, UserCreate, UserUpdate, UserPersonalInfoOut, UserRoleOut, UserWithRolesOut
)

router = APIRouter()


@router.get("/me", response_model=UserWithRolesOut)
async def get_my_details(current_user: User = Depends(get_current_user)):
    """Get details of the currently logged-in user."""
    return current_user


@router.get("/", response_model=UserListOut)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    search: str | None = Query(None),
    is_active: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List users with pagination and optional search filter."""
    query = select(User).options(
        selectinload(User.personal_info),
        selectinload(User.role_assignments).selectinload(UserRoleAssignment.role)
    )
    count_query = select(func.count(User.user_id))

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                User.username.ilike(search_term),
                User.email.ilike(search_term),
            )
        )
        count_query = count_query.where(
            or_(
                User.username.ilike(search_term),
                User.email.ilike(search_term),
            )
        )

    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(
        query.offset(skip).limit(limit).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return UserListOut(users=users, total=total)


@router.get("/roles", response_model=list[UserRoleOut])
async def list_roles(db: AsyncSession = Depends(get_db)):
    """List all available user roles."""
    result = await db.execute(select(UserRole).order_by(UserRole.role_name))
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single user by ID."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.personal_info), selectinload(User.role_assignments))
        .where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user."""
    # Check existing username or email
    existing = await db.execute(
        select(User).where(
            (User.username == data.username) | (User.email == data.email)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered",
        )

    user = User(
        username=data.username,
        email=data.email,
        password_hash=get_password_hash(data.password),
        is_active=data.is_active if hasattr(data, 'is_active') else True,
        is_verified=data.is_verified if hasattr(data, 'is_verified') else False,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: UUID, data: UserUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing user."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = data.model_dump(exclude_unset=True)
    
    # Handle password update separately
    if "password" in update_data:
        password = update_data.pop("password")
        if password:  # If password is not None and not empty string
            if len(password) < 8:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password must be at least 8 characters"
                )
            user.password_hash = get_password_hash(password)
    
    for key, value in update_data.items():
        setattr(user, key, value)

    await db.flush()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a user (soft delete by setting is_active to False)."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = False
    await db.flush()
    return None


@router.post("/{user_id}/personal-info", response_model=UserPersonalInfoOut, status_code=status.HTTP_201_CREATED)
async def create_user_personal_info(
    user_id: UUID, 
    data: UserPersonalInfoOut, 
    db: AsyncSession = Depends(get_db)
):
    """Create personal info for a user."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.personal_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has personal info"
        )

    personal_info = UserPersonalInfo(
        user_id=user_id,
        **data.model_dump()
    )
    db.add(personal_info)
    await db.flush()
    await db.refresh(personal_info)
    return personal_info


@router.put("/{user_id}/personal-info", response_model=UserPersonalInfoOut)
async def update_user_personal_info(
    user_id: UUID, 
    data: UserPersonalInfoOut, 
    db: AsyncSession = Depends(get_db)
):
    """Update personal info for a user."""
    result = await db.execute(
        select(UserPersonalInfo).where(UserPersonalInfo.user_id == user_id)
    )
    personal_info = result.scalar_one_or_none()
    if not personal_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personal info not found"
        )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(personal_info, key, value)

    await db.flush()
    await db.refresh(personal_info)
    return personal_info


@router.post("/{user_id}/roles/{role_id}", status_code=status.HTTP_201_CREATED)
async def assign_role_to_user(
    user_id: UUID, 
    role_id: int, 
    assigned_by: UUID | None = None,
    db: AsyncSession = Depends(get_db)
):
    """Assign a role to a user."""
    # Check user exists
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check role exists
    role_result = await db.execute(select(UserRole).where(UserRole.role_id == role_id))
    if not role_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    # Check if already assigned
    existing = await db.execute(
        select(UserRoleAssignment).where(
            UserRoleAssignment.user_id == user_id,
            UserRoleAssignment.role_id == role_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role already assigned to user"
        )

    assignment = UserRoleAssignment(
        user_id=user_id,
        role_id=role_id,
        assigned_by=assigned_by,
    )
    db.add(assignment)
    await db.flush()
    return {"message": "Role assigned successfully"}


@router.delete("/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role_from_user(user_id: UUID, role_id: int, db: AsyncSession = Depends(get_db)):
    """Remove a role from a user."""
    result = await db.execute(
        select(UserRoleAssignment).where(
            UserRoleAssignment.user_id == user_id,
            UserRoleAssignment.role_id == role_id,
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role assignment not found"
        )

    await db.delete(assignment)
    await db.flush()
    return None
