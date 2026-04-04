"""Course management endpoints with full CRUD operations."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.academic import Course, Department
from app.schemas.academic import (
    CourseOut, CourseListOut, CourseCreate, CourseUpdate
)

router = APIRouter()


@router.get("/", response_model=CourseListOut)
async def list_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    department_id: int | None = Query(None),
    search: str | None = Query(None),
    is_active: bool | None = Query(None),
    course_level: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List courses with optional filters and pagination."""
    query = select(Course)
    count_query = select(func.count(Course.course_id))

    if department_id is not None:
        query = query.where(Course.department_id == department_id)
        count_query = count_query.where(Course.department_id == department_id)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            Course.course_name.ilike(search_term) |
            Course.course_code.ilike(search_term)
        )
        count_query = count_query.where(
            Course.course_name.ilike(search_term) |
            Course.course_code.ilike(search_term)
        )

    if is_active is not None:
        query = query.where(Course.is_active == is_active)
        count_query = count_query.where(Course.is_active == is_active)

    if course_level:
        query = query.where(Course.course_level == course_level)
        count_query = count_query.where(Course.course_level == course_level)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(
        query.offset(skip).limit(limit).order_by(Course.course_code)
    )
    courses = result.scalars().all()
    return CourseListOut(courses=courses, total=total)


@router.get("/{course_id}", response_model=CourseOut)
async def get_course(course_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single course by ID."""
    result = await db.execute(select(Course).where(Course.course_id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


@router.post("/", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
async def create_course(data: CourseCreate, db: AsyncSession = Depends(get_db)):
    """Create a new course."""
    # Check for existing course code
    existing = await db.execute(
        select(Course).where(Course.course_code == data.course_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Course code already exists",
        )

    # Verify department exists
    dept_result = await db.execute(
        select(Department).where(Department.department_id == data.department_id)
    )
    if not dept_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department not found",
        )

    course = Course(**data.model_dump())
    db.add(course)
    await db.flush()
    await db.refresh(course)
    return course


@router.put("/{course_id}", response_model=CourseOut)
async def update_course(course_id: int, data: CourseUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing course."""
    result = await db.execute(select(Course).where(Course.course_id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    update_data = data.model_dump(exclude_unset=True)

    # Check for conflicts if updating course code
    if "course_code" in update_data:
        existing = await db.execute(
            select(Course).where(
                Course.course_id != course_id,
                Course.course_code == update_data["course_code"]
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Course code already exists",
            )

    # Verify department exists if updating
    if "department_id" in update_data:
        dept_result = await db.execute(
            select(Department).where(Department.department_id == update_data["department_id"])
        )
        if not dept_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found",
            )

    for key, value in update_data.items():
        setattr(course, key, value)

    await db.flush()
    await db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(course_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a course (soft delete by setting is_active to False)."""
    result = await db.execute(select(Course).where(Course.course_id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    course.is_active = False
    await db.flush()
    return None


@router.get("/{course_id}/sections")
async def get_course_sections(
    course_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    term_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get all sections for a course."""
    from app.models.academic import CourseSection
    from app.schemas.academic import CourseSectionListOut, CourseSectionOut

    result = await db.execute(select(Course).where(Course.course_id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    query = select(CourseSection).where(CourseSection.course_id == course_id)
    count_query = select(func.count(CourseSection.section_id)).where(CourseSection.course_id == course_id)

    if term_id:
        query = query.where(CourseSection.term_id == term_id)
        count_query = count_query.where(CourseSection.term_id == term_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.offset(skip).limit(limit).order_by(CourseSection.section_number)
    sections_result = await db.execute(query)
    sections = sections_result.scalars().all()

    return CourseSectionListOut(sections=sections, total=total)
