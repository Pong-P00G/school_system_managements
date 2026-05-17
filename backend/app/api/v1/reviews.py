"""Review endpoints — student course evaluations with moderation."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.core.database import get_db
from app.models.academic import Course, AcademicTerm, CourseSection
from app.models.people import (
    Enrollment, Faculty, Student,
)
from app.models.review import Review
from app.models.user import User
from app.schemas.review import (
    ReviewCreate, ReviewUpdate, ReviewOut, ReviewListOut,
    ReviewSummaryOut, ReviewableEnrollmentOut,
)
from app.api.deps import get_current_user

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_enrollment_for_student(
    db: AsyncSession, enrollment_id: int, student_id: UUID,
) -> Enrollment | None:
    """Fetch an enrollment belonging to a specific student."""
    result = await db.execute(
        select(Enrollment)
        .options(
            selectinload(Enrollment.section).selectinload(CourseSection.course),
            selectinload(Enrollment.section).selectinload(CourseSection.term),
        )
        .where(
            Enrollment.enrollment_id == enrollment_id,
            Enrollment.student_id == student_id,
        )
    )
    return result.scalar_one_or_none()


async def _get_review_owner(
    db: AsyncSession, review_id: int, student_id: UUID,
) -> Review | None:
    """Fetch a review that belongs to a specific student."""
    result = await db.execute(
        select(Review)
        .join(Enrollment, Review.enrollment_id == Enrollment.enrollment_id)
        .where(
            Review.review_id == review_id,
            Enrollment.student_id == student_id,
        )
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Reviewable enrollments (student)
# ---------------------------------------------------------------------------


@router.get("/reviewable", response_model=list[ReviewableEnrollmentOut])
async def list_reviewable_enrollments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get enrollments the current student can review (completed or past term, not yet reviewed)."""
    # Find the student record for this user
    student = await db.scalar(
        select(Student).where(Student.student_id == current_user.user_id)
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # Fetch eligible enrollments
    now = datetime.now(timezone.utc).replace(tzinfo=None).date()
    result = await db.execute(
        select(Enrollment)
        .options(
            selectinload(Enrollment.section).selectinload(CourseSection.course),
            selectinload(Enrollment.section).selectinload(CourseSection.term),
            selectinload(Enrollment.section).selectinload(CourseSection.instructor),
        )
        .where(
            Enrollment.student_id == student.student_id,
            Enrollment.enrollment_status.in_(["completed", "enrolled"]),
        )
        .order_by(Enrollment.enrollment_id.desc())
    )
    enrollments = result.scalars().all()

    # Get already-reviewed enrollment IDs
    reviewed_ids_result = await db.execute(
        select(Review.enrollment_id).where(
            Review.enrollment_id.in_([e.enrollment_id for e in enrollments])
        )
    )
    reviewed_ids = set(reviewed_ids_result.scalars().all())

    out = []
    for e in enrollments:
        section = e.section
        if not section:
            continue
        term = section.term
        # Only show if term has ended or enrollment is completed
        if e.enrollment_status == "enrolled" and term and term.end_date and term.end_date > now:
            continue

        course = section.course
        instructor = section.instructor
        faculty_name = ""
        if instructor and instructor.user:
            info = instructor.user.personal_info
            if info:
                faculty_name = f"{info.first_name or ''} {info.last_name or ''}".strip()
            if not faculty_name:
                faculty_name = instructor.user.username

        out.append(ReviewableEnrollmentOut(
            enrollment_id=e.enrollment_id,
            section_id=section.section_id,
            course_name=course.course_name if course else "",
            course_code=course.course_code if course else "",
            term_name=term.term_name if term else "",
            faculty_name=faculty_name,
            has_reviewed=e.enrollment_id in reviewed_ids,
        ))

    return out


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.get("/", response_model=ReviewListOut)
async def list_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    course_id: int | None = Query(None),
    faculty_id: UUID | None = Query(None),
    term_id: int | None = Query(None),
    is_approved: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    """List reviews with optional filters. Non-admin users see only approved reviews."""
    query = select(Review)
    count_query = select(func.count(Review.review_id))

    # Filtering
    if course_id is not None:
        query = query.where(Review.course_id == course_id)
        count_query = count_query.where(Review.course_id == course_id)
    if faculty_id is not None:
        query = query.where(Review.faculty_id == faculty_id)
        count_query = count_query.where(Review.faculty_id == faculty_id)
    if term_id is not None:
        query = query.where(Review.term_id == term_id)
        count_query = count_query.where(Review.term_id == term_id)

    # Non-admin only sees approved reviews
    is_admin = current_user and any(
        getattr(getattr(ra, "role", None), "role_name", None) == "admin"
        for ra in getattr(current_user, "role_assignments", [])
    )
    if not is_admin and is_approved is not False:
        query = query.where(Review.is_approved == True)
        count_query = count_query.where(Review.is_approved == True)
    elif is_approved is not None:
        query = query.where(Review.is_approved == is_approved)
        count_query = count_query.where(Review.is_approved == is_approved)

    # Total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Fetch
    result = await db.execute(
        query
        .options(joinedload(Review.enrollment))
        .offset(skip)
        .limit(limit)
        .order_by(Review.created_at.desc())
    )
    reviews = result.scalars().all()

    return ReviewListOut(reviews=reviews, total=total)


@router.get("/{review_id}", response_model=ReviewOut)
async def get_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single review by ID."""
    result = await db.execute(
        select(Review).where(Review.review_id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if not review.is_approved:
        # Only the owner or an admin can see unapproved reviews
        is_admin = any(
            getattr(getattr(ra, "role", None), "role_name", None) == "admin"
            for ra in getattr(current_user, "role_assignments", [])
        )
        if not is_admin:
            # Check ownership
            owner_check = await db.scalar(
                select(Enrollment).where(
                    Enrollment.enrollment_id == review.enrollment_id,
                    Enrollment.student_id == current_user.user_id,
                )
            )
            if not owner_check:
                raise HTTPException(status_code=404, detail="Review not found")
    return review


@router.post("/", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def create_review(
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a review for a completed enrollment."""
    # Get student profile
    student = await db.scalar(
        select(Student).where(Student.student_id == current_user.user_id)
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # Verify enrollment exists and belongs to this student
    enrollment = await _get_enrollment_for_student(db, data.enrollment_id, student.student_id)
    if not enrollment:
        raise HTTPException(
            status_code=404,
            detail="Enrollment not found or does not belong to you",
        )

    # Check for duplicate review
    existing = await db.scalar(
        select(Review).where(Review.enrollment_id == data.enrollment_id)
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="You have already reviewed this enrollment",
        )

    # Check eligibility (must be completed or term ended)
    section = enrollment.section
    if not section:
        raise HTTPException(status_code=400, detail="Section not found for this enrollment")
    term = section.term
    now = datetime.now(timezone.utc).replace(tzinfo=None).date()
    if enrollment.enrollment_status == "enrolled" and term and term.end_date and term.end_date > now:
        raise HTTPException(
            status_code=400,
            detail="Cannot review this enrollment yet — the term has not ended",
        )

    # Get denormalized fields from enrollment
    course_id = section.course_id
    term_id = section.term_id
    faculty_id = section.instructor_id

    review = Review(
        enrollment_id=data.enrollment_id,
        course_id=course_id,
        faculty_id=faculty_id,
        term_id=term_id,
        overall_rating=data.overall_rating,
        teaching_rating=data.teaching_rating,
        content_rating=data.content_rating,
        workload_rating=data.workload_rating,
        title=data.title,
        comment=data.comment,
        is_anonymous=data.is_anonymous,
    )
    db.add(review)
    await db.flush()
    await db.refresh(review)
    return review


@router.patch("/{review_id}", response_model=ReviewOut)
async def update_review(
    review_id: int,
    data: ReviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update your own review."""
    student = await db.scalar(
        select(Student).where(Student.student_id == current_user.user_id)
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    review = await _get_review_owner(db, review_id, student.student_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(review, key, value)

    await db.flush()
    await db.refresh(review)
    return review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete your own review."""
    student = await db.scalar(
        select(Student).where(Student.student_id == current_user.user_id)
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    review = await _get_review_owner(db, review_id, student.student_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    await db.delete(review)
    await db.flush()


# ---------------------------------------------------------------------------
# Summary endpoints
# ---------------------------------------------------------------------------


@router.get("/summary/course/{course_id}", response_model=ReviewSummaryOut)
async def get_course_review_summary(
    course_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated rating summary for a course."""
    return await _build_summary(db, Review.course_id == course_id)


@router.get("/summary/faculty/{faculty_id}", response_model=ReviewSummaryOut)
async def get_faculty_review_summary(
    faculty_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated rating summary for a faculty member."""
    return await _build_summary(db, Review.faculty_id == faculty_id)


async def _build_summary(db: AsyncSession, filter_condition) -> ReviewSummaryOut:
    """Build a rating summary for a given filter condition."""
    # Only approved reviews
    base_filter = and_(filter_condition, Review.is_approved == True)

    # Count
    count_result = await db.execute(
        select(func.count(Review.review_id)).where(base_filter)
    )
    total = count_result.scalar()

    # Averages
    avg_result = await db.execute(
        select(
            func.avg(Review.overall_rating),
            func.avg(Review.teaching_rating),
            func.avg(Review.content_rating),
            func.avg(Review.workload_rating),
        ).where(base_filter)
    )
    row = avg_result.one()
    avg_overall = round(float(row[0]), 2) if row[0] else None
    avg_teaching = round(float(row[1]), 2) if row[1] else None
    avg_content = round(float(row[2]), 2) if row[2] else None
    avg_workload = round(float(row[3]), 2) if row[3] else None

    # Distribution of overall_rating
    dist_result = await db.execute(
        select(Review.overall_rating, func.count(Review.review_id))
        .where(base_filter)
        .group_by(Review.overall_rating)
        .order_by(Review.overall_rating)
    )
    distribution = {str(r): 0 for r in range(1, 6)}
    for rating, count in dist_result:
        distribution[str(rating)] = count

    return ReviewSummaryOut(
        total_reviews=total,
        average_overall=avg_overall,
        average_teaching=avg_teaching,
        average_content=avg_content,
        average_workload=avg_workload,
        distribution=distribution,
    )


# ---------------------------------------------------------------------------
# Admin moderation
# ---------------------------------------------------------------------------


@router.patch("/{review_id}/moderation", response_model=ReviewOut)
async def moderate_review(
    review_id: int,
    is_approved: bool = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve or reject a review (admin only)."""
    # Check admin role
    is_admin = any(
        getattr(getattr(ra, "role", None), "role_name", None) == "admin"
        for ra in getattr(current_user, "role_assignments", [])
    )
    if not is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.execute(select(Review).where(Review.review_id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.is_approved = is_approved
    await db.flush()
    await db.refresh(review)
    return review
