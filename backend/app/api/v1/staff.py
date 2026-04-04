"""Staff management endpoints with full CRUD operations."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.people import Staff
from app.models.user import User
from app.models.academic import Department
from app.schemas.people import (
    StaffOut, StaffListOut, StaffCreate, StaffUpdate
)

router = APIRouter()


@router.get("/", response_model=StaffListOut)
async def list_staff(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    department_id: int | None = Query(None),
    employment_status: str | None = Query(None),
    job_category: str | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List staff with optional filters and pagination."""
    query = select(Staff).options(
        selectinload(Staff.user),
    )
    count_query = select(func.count(Staff.staff_id))

    if department_id is not None:
        query = query.where(Staff.department_id == department_id)
        count_query = count_query.where(Staff.department_id == department_id)

    if employment_status:
        query = query.where(Staff.employment_status == employment_status)
        count_query = count_query.where(Staff.employment_status == employment_status)

    if job_category:
        query = query.where(Staff.job_category == job_category)
        count_query = count_query.where(Staff.job_category == job_category)

    if search:
        search_term = f"%{search}%"
        query = query.join(User).where(
            User.username.ilike(search_term) |
            User.email.ilike(search_term) |
            Staff.employee_number.ilike(search_term)
        )
        count_query = count_query.join(User).where(
            User.username.ilike(search_term) |
            User.email.ilike(search_term) |
            Staff.employee_number.ilike(search_term)
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(
        query.offset(skip).limit(limit).order_by(Staff.created_at.desc())
    )
    staff = result.scalars().all()
    return StaffListOut(staff=staff, total=total)


@router.get("/{staff_id}", response_model=StaffOut)
async def get_staff(staff_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single staff member by ID."""
    result = await db.execute(
        select(Staff)
        .options(selectinload(Staff.user))
        .where(Staff.staff_id == staff_id)
    )
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    return staff


@router.post("/", response_model=StaffOut, status_code=status.HTTP_201_CREATED)
async def create_staff(data: StaffCreate, db: AsyncSession = Depends(get_db)):
    """Create a new staff profile for an existing user."""
    # Check if user exists
    user_result = await db.execute(select(User).where(User.user_id == data.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check if staff already exists for this user
    existing_staff = await db.execute(
        select(Staff).where(Staff.staff_id == data.user_id)
    )
    if existing_staff.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Staff profile already exists for this user"
        )

    # Check for duplicate employee number
    existing_number = await db.execute(
        select(Staff).where(Staff.employee_number == data.employee_number)
    )
    if existing_number.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee number already exists"
        )

    # Verify department exists if provided
    if data.department_id:
        dept_result = await db.execute(
            select(Department).where(Department.department_id == data.department_id)
        )
        if not dept_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found"
            )

    staff = Staff(
        staff_id=data.user_id,
        **data.model_dump(exclude={"user_id"})
    )
    db.add(staff)
    await db.flush()
    await db.refresh(staff)
    return staff


@router.put("/{staff_id}", response_model=StaffOut)
async def update_staff(staff_id: UUID, data: StaffUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing staff member."""
    result = await db.execute(select(Staff).where(Staff.staff_id == staff_id))
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")

    update_data = data.model_dump(exclude_unset=True)

    # Check for duplicate employee number if updating
    if "employee_number" in update_data:
        existing = await db.execute(
            select(Staff).where(
                Staff.staff_id != staff_id,
                Staff.employee_number == update_data["employee_number"]
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Employee number already exists"
            )

    # Verify department exists if updating
    if "department_id" in update_data and update_data["department_id"]:
        dept_result = await db.execute(
            select(Department).where(Department.department_id == update_data["department_id"])
        )
        if not dept_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found"
            )

    for key, value in update_data.items():
        setattr(staff, key, value)

    await db.flush()
    await db.refresh(staff)
    return staff


@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff(staff_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a staff profile."""
    result = await db.execute(select(Staff).where(Staff.staff_id == staff_id))
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")

    await db.delete(staff)
    await db.flush()
    return None