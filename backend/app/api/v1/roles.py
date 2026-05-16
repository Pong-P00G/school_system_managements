"""Role management endpoints (admin only)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.user import UserRole, UserRoleAssignment
from app.schemas.user import (
    UserRoleOut, RoleCreate, RoleUpdate
)
from app.api.deps import get_current_admin

router = APIRouter()


@router.get("/", response_model=list[UserRoleOut])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """List all available user roles. Admin only."""
    result = await db.execute(select(UserRole).order_by(UserRole.role_name))
    return result.scalars().all()


@router.post("/", response_model=UserRoleOut, status_code=status.HTTP_201_CREATED)
async def create_role(
    data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """Create a new user role. Admin only."""
    # Check for existing role name
    existing = await db.execute(
        select(UserRole).where(UserRole.role_name == data.role_name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role name already exists",
        )

    role = UserRole(
        role_name=data.role_name,
        description=data.description,
    )
    db.add(role)
    await db.flush()
    await db.refresh(role)
    return role


@router.get("/{role_id}", response_model=UserRoleOut)
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """Get a single role by ID. Admin only."""
    result = await db.execute(select(UserRole).where(UserRole.role_id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


@router.put("/{role_id}", response_model=UserRoleOut)
async def update_role(
    role_id: int,
    data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """Update an existing role. Admin only."""
    result = await db.execute(select(UserRole).where(UserRole.role_id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    update_data = data.model_dump(exclude_unset=True)

    # Check for conflicts if updating role name
    if "role_name" in update_data:
        existing = await db.execute(
            select(UserRole).where(
                UserRole.role_id != role_id,
                UserRole.role_name == update_data["role_name"],
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Role name already exists",
            )

    for key, value in update_data.items():
        setattr(role, key, value)

    await db.flush()
    await db.refresh(role)
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """Delete a role. Admin only. Cannot delete system roles."""
    result = await db.execute(select(UserRole).where(UserRole.role_id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    if role.is_system_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system roles",
        )

    # Check if role is assigned to any users
    assignment_count = await db.scalar(
        select(func.count(UserRoleAssignment.assignment_id)).where(
            UserRoleAssignment.role_id == role_id
        )
    )
    if assignment_count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete role: {assignment_count} user(s) are assigned this role. Remove the assignments first.",
        )

    await db.delete(role)
    await db.flush()
    return None
