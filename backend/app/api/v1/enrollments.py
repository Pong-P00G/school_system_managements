"""Enrollment management endpoints with full CRUD operations."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.people import Enrollment, Student
from app.models.academic import CourseSection
from app.schemas.people import (
    EnrollmentOut, EnrollmentListOut, EnrollmentCreate, EnrollmentUpdate
)

router = APIRouter()


@router.get("/", response_model=EnrollmentListOut)
async def list_enrollments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    student_id: UUID | None = Query(None),
    section_id: int | None = Query(None),
    enrollment_status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List enrollments with optional filters and pagination."""
    query = select(Enrollment).options(
        selectinload(Enrollment.student),
        selectinload(Enrollment.section)
    )
    count_query = select(func.count(Enrollment.enrollment_id))

    if student_id is not None:
        query = query.where(Enrollment.student_id == student_id)
        count_query = count_query.where(Enrollment.student_id == student_id)

    if section_id is not None:
        query = query.where(Enrollment.section_id == section_id)
        count_query = count_query.where(Enrollment.section_id == section_id)

    if enrollment_status:
        query = query.where(Enrollment.enrollment_status == enrollment_status)
        count_query = count_query.where(Enrollment.enrollment_status == enrollment_status)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(
        query.offset(skip).limit(limit).order_by(Enrollment.enrollment_date.desc())
    )
    enrollments = result.scalars().all()
    return EnrollmentListOut(enrollments=enrollments, total=total)


@router.get("/{enrollment_id}", response_model=EnrollmentOut)
async def get_enrollment(enrollment_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single enrollment by ID."""
    result = await db.execute(
        select(Enrollment)
        .options(selectinload(Enrollment.student), selectinload(Enrollment.section))
        .where(Enrollment.enrollment_id == enrollment_id)
    )
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
    return enrollment


@router.post("/", response_model=EnrollmentOut, status_code=status.HTTP_201_CREATED)
async def create_enrollment(data: EnrollmentCreate, db: AsyncSession = Depends(get_db)):
    """Create a new enrollment (enroll a student in a course section)."""
    # Check if student exists
    student_result = await db.execute(select(Student).where(Student.student_id == data.student_id))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    # Check if section exists
    section_result = await db.execute(
        select(CourseSection).where(CourseSection.section_id == data.section_id)
    )
    section = section_result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course section not found")

    # Check if already enrolled
    existing = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == data.student_id,
            Enrollment.section_id == data.section_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student already enrolled in this section"
        )

    # Check capacity
    if section.enrolled_count >= section.max_capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course section is full"
        )

    enrollment = Enrollment(**data.model_dump())
    db.add(enrollment)

    # Update enrolled count
    section.enrolled_count += 1

    await db.flush()
    await db.refresh(enrollment)
    return enrollment


@router.put("/{enrollment_id}", response_model=EnrollmentOut)
async def update_enrollment(enrollment_id: int, data: EnrollmentUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing enrollment (e.g., assign grade, change status)."""
    result = await db.execute(select(Enrollment).where(Enrollment.enrollment_id == enrollment_id))
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(enrollment, key, value)

    await db.flush()
    await db.refresh(enrollment)
    return enrollment


@router.delete("/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_enrollment(enrollment_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an enrollment (withdraw student from section)."""
    result = await db.execute(
        select(Enrollment)
        .options(selectinload(Enrollment.section))
        .where(Enrollment.enrollment_id == enrollment_id)
    )
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    # Update enrolled count
    if enrollment.section and enrollment.enrollment_status == "enrolled":
        enrollment.section.enrolled_count -= 1

    await db.delete(enrollment)
    await db.flush()
    return None


@router.post("/{enrollment_id}/withdraw", response_model=EnrollmentOut)
async def withdraw_from_enrollment(
    enrollment_id: int, 
    reason: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """Withdraw from an enrollment (soft delete by changing status)."""
    from datetime import datetime

    result = await db.execute(select(Enrollment).where(Enrollment.enrollment_id == enrollment_id))
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    if enrollment.enrollment_status != "enrolled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only withdraw from active enrollments"
        )

    enrollment.enrollment_status = "withdrawn"
    enrollment.withdrawal_date = datetime.utcnow()
    enrollment.withdrawal_reason = reason

    # Update enrolled count
    section_result = await db.execute(
        select(CourseSection).where(CourseSection.section_id == enrollment.section_id)
    )
    section = section_result.scalar_one_or_none()
    if section:
        section.enrolled_count -= 1

    await db.flush()
    await db.refresh(enrollment)
    return enrollment


@router.post("/{enrollment_id}/grade", response_model=EnrollmentOut)
async def submit_grade(
    enrollment_id: int,
    grade: str,
    grade_points: float | None = None,
    graded_by: UUID | None = None,
    db: AsyncSession = Depends(get_db)
):
    """Submit a grade for an enrollment."""
    from datetime import datetime

    result = await db.execute(select(Enrollment).where(Enrollment.enrollment_id == enrollment_id))
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

    enrollment.grade = grade
    enrollment.final_grade = grade
    if grade_points is not None:
        enrollment.grade_points = grade_points
    enrollment.grade_submitted_date = datetime.utcnow()
    enrollment.grade_submitted_by = graded_by
    enrollment.enrollment_status = "completed"

    await db.flush()
    await db.refresh(enrollment)
    return enrollment