"""Department management endpoints with full CRUD operations."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.academic import Department, Course, Program
from app.models.people import Faculty
from app.schemas.academic import (
    DepartmentOut, DepartmentListOut, DepartmentCreate, DepartmentUpdate
)

router = APIRouter()


@router.get("/", response_model=DepartmentListOut)
async def list_departments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    is_active: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List departments with pagination and optional search filter."""
    query = select(Department)
    count_query = select(func.count(Department.department_id))

    if search:
        search_term = f"%{search}%"
        query = query.where(
            Department.department_name.ilike(search_term) |
            Department.department_code.ilike(search_term)
        )
        count_query = count_query.where(
            Department.department_name.ilike(search_term) |
            Department.department_code.ilike(search_term)
        )

    if is_active is not None:
        query = query.where(Department.is_active == is_active)
        count_query = count_query.where(Department.is_active == is_active)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(
        query.offset(skip).limit(limit).order_by(Department.department_name)
    )
    departments = result.scalars().all()
    return DepartmentListOut(departments=departments, total=total)


@router.get("/{department_id}", response_model=DepartmentOut)
async def get_department(department_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single department by ID."""
    result = await db.execute(
        select(Department).where(Department.department_id == department_id)
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return dept


@router.post("/", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
async def create_department(data: DepartmentCreate, db: AsyncSession = Depends(get_db)):
    """Create a new department."""
    # Check for existing code or name
    existing = await db.execute(
        select(Department).where(
            (Department.department_code == data.department_code) |
            (Department.department_name == data.department_name)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department code or name already exists",
        )

    dept = Department(**data.model_dump())
    db.add(dept)
    await db.flush()
    await db.refresh(dept)
    return dept


@router.put("/{department_id}", response_model=DepartmentOut)
async def update_department(
    department_id: int, 
    data: DepartmentUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Update an existing department."""
    result = await db.execute(
        select(Department).where(Department.department_id == department_id)
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    update_data = data.model_dump(exclude_unset=True)
    
    # Check for conflicts if updating code or name
    if "department_code" in update_data or "department_name" in update_data:
        conditions = []
        if "department_code" in update_data:
            conditions.append(Department.department_code == update_data["department_code"])
        if "department_name" in update_data:
            conditions.append(Department.department_name == update_data["department_name"])
        conflict_filter = conditions[0]
        for c in conditions[1:]:
            conflict_filter = conflict_filter | c
        existing = await db.execute(
            select(Department).where(
                Department.department_id != department_id,
                conflict_filter,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Department code or name already exists",
            )

    for key, value in update_data.items():
        setattr(dept, key, value)

    await db.flush()
    await db.refresh(dept)
    return dept


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: int,
    force: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """Delete a department (soft delete by setting is_active=False)."""
    result = await db.execute(
        select(Department)
        .options(selectinload(Department.courses), selectinload(Department.programs))
        .where(Department.department_id == department_id)
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    if not force:
        # Check for dependent records
        if dept.courses:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete department: {len(dept.courses)} course(s) are still associated with this department. Reassign or remove them first."
            )
        if dept.programs:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete department: {len(dept.programs)} program(s) are still associated with this department. Reassign or remove them first."
            )
        faculty_count = await db.scalar(
            select(func.count(Faculty.faculty_id)).where(Faculty.department_id == department_id)
        )
        if faculty_count:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete department: {faculty_count} faculty member(s) are assigned to this department. Reassign them first."
            )

    dept.is_active = False
    await db.flush()
    return None


@router.get("/{department_id}/courses")
async def get_department_courses(
    department_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get all courses for a department."""
    from app.models.academic import Course
    from app.schemas.academic import CourseListOut, CourseOut

    result = await db.execute(
        select(Department).where(Department.department_id == department_id)
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    count_query = select(func.count(Course.course_id)).where(Course.department_id == department_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = select(Course).where(Course.department_id == department_id).offset(skip).limit(limit)
    courses_result = await db.execute(query)
    courses = courses_result.scalars().all()

    return CourseListOut(courses=courses, total=total)


@router.get("/{department_id}/programs")
async def get_department_programs(
    department_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get all programs for a department."""
    from app.models.academic import Program
    from app.schemas.academic import ProgramListOut, ProgramOut

    result = await db.execute(
        select(Department).where(Department.department_id == department_id)
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    count_query = select(func.count(Program.program_id)).where(Program.department_id == department_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = select(Program).where(Program.department_id == department_id).offset(skip).limit(limit)
    programs_result = await db.execute(query)
    programs = programs_result.scalars().all()

    return ProgramListOut(programs=programs, total=total)
