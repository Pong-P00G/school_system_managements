"""Role management endpoints with level-based access control."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sa_delete
from app.core.database import get_db
from app.models.user import UserRole, UserRoleAssignment
from app.schemas.user import UserRoleOut, RoleCreate, RoleUpdate
from app.api.deps import get_current_admin

router = APIRouter()


def get_user_level(current_user) -> int:
    """Get the lowest (highest privilege) role_level of the current user."""
    levels = [
        ra.role.role_level for ra in current_user.role_assignments
        if ra.is_active and ra.role.role_level is not None
    ]
    return min(levels) if levels else 99


@router.get("/", response_model=list[UserRoleOut])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    result = await db.execute(select(UserRole).order_by(UserRole.role_level))
    return result.scalars().all()


@router.post("/", response_model=UserRoleOut, status_code=status.HTTP_201_CREATED)
async def create_role(
    data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    user_level = get_user_level(current_user)
    # Can only create roles with higher level number (lower privilege)
    if data.role_level <= user_level:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create a role with equal or higher privilege than your own")

    existing = await db.execute(select(UserRole).where(UserRole.role_name == data.role_name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role name already exists")

    role = UserRole(role_name=data.role_name, description=data.description, role_level=data.role_level)
    db.add(role)
    await db.flush()
    await db.refresh(role)
    return role


@router.get("/{role_id}", response_model=UserRoleOut)
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
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
    current_user=Depends(get_current_admin),
):
    result = await db.execute(select(UserRole).where(UserRole.role_id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    user_level = get_user_level(current_user)
    # Can only modify roles with higher level number (lower privilege)
    if role.role_level <= user_level:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify a role with equal or higher privilege")

    update_data = data.model_dump(exclude_unset=True)

    # Cannot set level to equal or higher privilege than own
    if "role_level" in update_data and update_data["role_level"] <= user_level:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot set role level to equal or higher privilege than your own")

    if "role_name" in update_data:
        existing = await db.execute(
            select(UserRole).where(UserRole.role_id != role_id, UserRole.role_name == update_data["role_name"])
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role name already exists")

    for key, value in update_data.items():
        setattr(role, key, value)

    await db.flush()
    await db.refresh(role)
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    result = await db.execute(select(UserRole).where(UserRole.role_id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    user_level = get_user_level(current_user)
    if role.role_level <= user_level:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete a role with equal or higher privilege")

    await db.execute(sa_delete(UserRoleAssignment).where(UserRoleAssignment.role_id == role_id))
    await db.delete(role)
    await db.flush()
    return None
