"""Permission management endpoints (super-admin only)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import Permission, RolePermission, PagePermission
from app.models.audit import AuditLog, log_audit
from app.api.deps import get_current_super_admin, get_current_user
from pydantic import BaseModel

router = APIRouter()


# --- Schemas ---
class PermissionOut(BaseModel):
    permission_id: int
    permission_name: str
    description: str | None = None
    model_config = {"from_attributes": True}


class PagePermissionOut(BaseModel):
    id: int
    page_path: str
    page_name: str
    min_role_level: int
    model_config = {"from_attributes": True}


class PagePermissionUpdate(BaseModel):
    min_role_level: int


class RolePermissionAssign(BaseModel):
    role_id: int
    permission_id: int


# --- Role Permissions ---
@router.get("/", response_model=list[PermissionOut])
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_super_admin),
):
    result = await db.execute(select(Permission).order_by(Permission.permission_name))
    return result.scalars().all()


@router.get("/role/{role_id}", response_model=list[PermissionOut])
async def get_role_permissions(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_super_admin),
):
    result = await db.execute(
        select(Permission)
        .join(RolePermission, RolePermission.permission_id == Permission.permission_id)
        .where(RolePermission.role_id == role_id)
    )
    return result.scalars().all()


@router.post("/role", status_code=status.HTTP_201_CREATED)
async def assign_permission_to_role(
    data: RolePermissionAssign,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_super_admin),
):
    rp = RolePermission(role_id=data.role_id, permission_id=data.permission_id)
    db.add(rp)
    await db.flush()
    return {"detail": "Permission assigned"}


@router.delete("/role/{role_id}/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_super_admin),
):
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
    )
    rp = result.scalar_one_or_none()
    if not rp:
        raise HTTPException(status_code=404, detail="Role permission not found")
    await db.delete(rp)
    await db.flush()


# --- Page Permissions ---
@router.get("/pages", response_model=list[PagePermissionOut])
async def list_page_permissions(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_super_admin),
):
    """List all page permissions. Super-admin only."""
    result = await db.execute(select(PagePermission).order_by(PagePermission.min_role_level, PagePermission.page_name))
    return result.scalars().all()


@router.put("/pages/{page_id}", response_model=PagePermissionOut)
async def update_page_permission(
    page_id: int,
    data: PagePermissionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_super_admin),
):
    """Update min_role_level for a page. Super-admin only."""
    result = await db.execute(select(PagePermission).where(PagePermission.id == page_id))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page permission not found")
    old_level = page.min_role_level
    page.min_role_level = data.min_role_level
    db.add(AuditLog(action="update", entity_type="page_permission", entity_id=str(page_id), user_id=current_user.user_id, old_values={"min_role_level": old_level}, new_values={"min_role_level": data.min_role_level}))
    await db.flush()
    await db.refresh(page)
    log_audit("update", "page_permission", page_id, page.page_name, current_user)
    return page


@router.get("/my-pages", response_model=list[PagePermissionOut])
async def get_my_page_permissions(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get pages accessible to the current user based on their role level."""
    # Get user's best (lowest) role level
    levels = [
        ra.role.role_level for ra in current_user.role_assignments
        if ra.is_active and ra.role.role_level is not None
    ]
    user_level = min(levels) if levels else 99

    result = await db.execute(
        select(PagePermission)
        .where(PagePermission.min_role_level >= user_level)
        .order_by(PagePermission.page_name)
    )
    return result.scalars().all()
