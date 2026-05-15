from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.people import Faculty, Assignment
from app.models.user import User
from app.models.academic import Department, CourseSection, Course
from app.schemas.people import (
    FacultyOut, FacultyListOut, FacultyCreate, FacultyUpdate
)
from app.api.deps import get_current_user

router = APIRouter()


# ──────────────────────────────────────────────
# /me  endpoints  (MUST come BEFORE /{faculty_id})
# ──────────────────────────────────────────────

@router.get("/me")
async def get_my_faculty_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Faculty)
        .options(selectinload(Faculty.user))
        .where(Faculty.faculty_id == current_user.user_id)
    )
    faculty = result.scalar_one_or_none()
    if not faculty:
        raise HTTPException(status_code=404, detail="No faculty profile linked to this user")
    return faculty


@router.get("/me/sections")
async def get_my_sections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.schemas.academic import CourseSectionListOut
    
    # Verify faculty profile exists
    result = await db.execute(select(Faculty).where(Faculty.faculty_id == current_user.user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="No faculty profile linked to this user")

    query = (
        select(CourseSection)
        .options(
            selectinload(CourseSection.course),
            selectinload(CourseSection.term),
            selectinload(CourseSection.room),
            selectinload(CourseSection.enrollments) # For student counts
        )
        .where(CourseSection.instructor_id == current_user.user_id)
        .order_by(CourseSection.start_date.desc())
    )
    sections_result = await db.execute(query)
    sections = sections_result.scalars().all()
    
    return CourseSectionListOut(sections=sections, total=len(sections))


@router.get("/{faculty_id}/assignments")
async def get_faculty_assignments(
    faculty_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    # 1. Get section IDs taught by this faculty
    sections_result = await db.execute(
        select(CourseSection.section_id)
        .where(CourseSection.instructor_id == faculty_id)
    )
    section_ids = sections_result.scalars().all()
    
    if not section_ids:
        return {"assignments": []}

    # 2. Get assignments for these sections
    assignments_result = await db.execute(
        select(Assignment)
        .options(
            selectinload(Assignment.section).selectinload(CourseSection.course)
        )
        .where(Assignment.section_id.in_(section_ids))
        .order_by(Assignment.due_date.desc())
    )
    assignments = assignments_result.scalars().all()
    
    # Custom response format to include course info directly
    out = []
    for a in assignments:
        course = a.section.course if a.section else None
        out.append({
            "assignment_id": a.assignment_id,
            "assignment_name": a.assignment_name,
            "course_name": course.course_name if course else "Unknown",
            "course_code": course.course_code if course else "",
            "due_date": a.due_date,
            "section_number": a.section.section_number if a.section else "",
            "is_published": a.is_published
        })
        
    return {"assignments": out}

@router.get("/", response_model=FacultyListOut)
async def list_faculty(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    department_id: int | None = Query(None),
    employment_status: str | None = Query(None),
    faculty_rank: str | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Faculty).options(
        selectinload(Faculty.user),
    )
    count_query = select(func.count(Faculty.faculty_id))

    if department_id is not None:
        query = query.where(Faculty.department_id == department_id)
        count_query = count_query.where(Faculty.department_id == department_id)

    if employment_status:
        query = query.where(Faculty.employment_status == employment_status)
        count_query = count_query.where(Faculty.employment_status == employment_status)

    if faculty_rank:
        query = query.where(Faculty.faculty_rank == faculty_rank)
        count_query = count_query.where(Faculty.faculty_rank == faculty_rank)

    if search:
        search_term = f"%{search}%"
        query = query.join(User).where(
            User.username.ilike(search_term) |
            User.email.ilike(search_term) |
            Faculty.employee_number.ilike(search_term)
        )
        count_query = count_query.join(User).where(
            User.username.ilike(search_term) |
            User.email.ilike(search_term) |
            Faculty.employee_number.ilike(search_term)
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(
        query.offset(skip).limit(limit).order_by(Faculty.created_at.desc())
    )
    faculty = result.scalars().all()
    return FacultyListOut(faculty=faculty, total=total)


@router.get("/{faculty_id}", response_model=FacultyOut)
async def get_faculty(faculty_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single faculty member by ID."""
    result = await db.execute(
        select(Faculty)
        .options(selectinload(Faculty.user))
        .where(Faculty.faculty_id == faculty_id)
    )
    faculty = result.scalar_one_or_none()
    if not faculty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")
    return faculty


@router.post("/", response_model=FacultyOut, status_code=status.HTTP_201_CREATED)
async def create_faculty(data: FacultyCreate, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    user_result = await db.execute(select(User).where(User.user_id == data.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check if faculty already exists for this user
    existing_faculty = await db.execute(
        select(Faculty).where(Faculty.faculty_id == data.user_id)
    )
    if existing_faculty.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Faculty profile already exists for this user"
        )

    # Check for duplicate employee number
    existing_number = await db.execute(
        select(Faculty).where(Faculty.employee_number == data.employee_number)
    )
    if existing_number.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee number already exists"
        )

    # Verify department exists
    dept_result = await db.execute(
        select(Department).where(Department.department_id == data.department_id)
    )
    if not dept_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department not found"
        )

    faculty = Faculty(
        faculty_id=data.user_id,
        **data.model_dump(exclude={"user_id"})
    )
    db.add(faculty)
    await db.flush()
    await db.refresh(faculty)
    return faculty


@router.put("/{faculty_id}", response_model=FacultyOut)
async def update_faculty(faculty_id: UUID, data: FacultyUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Faculty).where(Faculty.faculty_id == faculty_id))
    faculty = result.scalar_one_or_none()
    if not faculty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")

    update_data = data.model_dump(exclude_unset=True)

    # Check for duplicate employee number if updating
    if "employee_number" in update_data:
        existing = await db.execute(
            select(Faculty).where(
                Faculty.faculty_id != faculty_id,
                Faculty.employee_number == update_data["employee_number"]
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Employee number already exists"
            )

    # Verify department exists if updating
    if "department_id" in update_data:
        dept_result = await db.execute(
            select(Department).where(Department.department_id == update_data["department_id"])
        )
        if not dept_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found"
            )

    for key, value in update_data.items():
        setattr(faculty, key, value)

    await db.flush()
    await db.refresh(faculty)
    return faculty


@router.delete("/{faculty_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faculty(faculty_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a faculty member."""
    result = await db.execute(select(Faculty).where(Faculty.faculty_id == faculty_id))
    faculty = result.scalar_one_or_none()
    if not faculty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")

    await db.delete(faculty)
    await db.flush()
    return None


@router.get("/{faculty_id}/sections")
async def get_faculty_sections(
    faculty_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    term_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    from app.models.academic import CourseSection
    from app.schemas.academic import CourseSectionListOut, CourseSectionOut

    result = await db.execute(select(Faculty).where(Faculty.faculty_id == faculty_id))
    faculty = result.scalar_one_or_none()
    if not faculty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")

    query = (
        select(CourseSection)
        .options(
            selectinload(CourseSection.course),
            selectinload(CourseSection.term),
            selectinload(CourseSection.room),
        )
        .where(CourseSection.instructor_id == faculty_id)
    )
    count_query = select(func.count(CourseSection.section_id)).where(CourseSection.instructor_id == faculty_id)

    if term_id:
        query = query.where(CourseSection.term_id == term_id)
        count_query = count_query.where(CourseSection.term_id == term_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.offset(skip).limit(limit)
    sections_result = await db.execute(query)
    sections = sections_result.scalars().all()

    return CourseSectionListOut(sections=sections, total=total)