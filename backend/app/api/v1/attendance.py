"""Attendance management API endpoints."""

from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_current_admin, get_current_teacher_or_admin
from app.core.database import get_db
from app.models.people import Attendance, Student
from app.models.academic import CourseSection
from app.models.user import User
from app.models.notification import Notification
from app.schemas.people import (
    AttendanceCreate,
    AttendanceUpdate,
    AttendanceOut,
    AttendanceListOut,
)

router = APIRouter()


async def _get_attendance_or_404(
    db: AsyncSession, attendance_id: int
) -> Attendance:
    """Fetch an attendance record by ID or raise 404."""
    result = await db.execute(
        select(Attendance).where(Attendance.attendance_id == attendance_id)
    )
    attendance = result.scalar_one_or_none()
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found",
        )
    return attendance


@router.get("/section/{section_id}", response_model=AttendanceListOut)
async def get_section_attendance(
    section_id: int,
    class_date: date | None = Query(None, description="Filter by class date"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher_or_admin),
):
    """Get attendance records for a course section. Requires teacher or admin."""
    # Verify section exists
    section_result = await db.execute(
        select(CourseSection)
        .options(selectinload(CourseSection.course))
        .where(CourseSection.section_id == section_id)
    )
    section = section_result.scalar_one_or_none()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course section not found",
        )

    query = select(Attendance).options(
        selectinload(Attendance.student)
        .selectinload(Student.user)
    ).where(Attendance.section_id == section_id)

    if class_date:
        query = query.where(Attendance.class_date == class_date)

    query = query.order_by(Attendance.class_date.desc(), Attendance.student_id)
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    records = result.scalars().all()

    # Get total count
    count_query = select(Attendance.attendance_id).where(
        Attendance.section_id == section_id
    )
    if class_date:
        count_query = count_query.where(Attendance.class_date == class_date)
    total_result = await db.execute(count_query)
    total = len(total_result.all())

    return AttendanceListOut(
        attendance_records=records,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/my", response_model=AttendanceListOut)
async def get_my_attendance(
    class_date: date | None = Query(None, description="Filter by class date"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get attendance records for the current student."""
    # Find the student profile for this user
    student_result = await db.execute(
        select(Student).where(Student.user_id == current_user.user_id)
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found",
        )

    query = (
        select(Attendance)
        .options(
            selectinload(Attendance.section)
            .selectinload(CourseSection.course)
        )
        .where(Attendance.student_id == student.student_id)
    )

    if class_date:
        query = query.where(Attendance.class_date == class_date)

    query = query.order_by(Attendance.class_date.desc())

    # Get total count
    count_query = select(Attendance.attendance_id).where(
        Attendance.student_id == student.student_id
    )
    if class_date:
        count_query = count_query.where(Attendance.class_date == class_date)
    total_result = await db.execute(count_query)
    total = len(total_result.all())

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    records = result.scalars().all()

    return AttendanceListOut(
        attendance_records=records,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{attendance_id}", response_model=AttendanceOut)
async def get_attendance_record(
    attendance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single attendance record."""
    attendance = await _get_attendance_or_404(db, attendance_id)
    return attendance


@router.post("/", response_model=AttendanceOut, status_code=status.HTTP_201_CREATED)
async def record_attendance(
    data: AttendanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher_or_admin),
):
    """Record attendance for a student in a course section. Requires teacher or admin."""
    # Validate student exists
    student_result = await db.execute(
        select(Student).where(Student.student_id == data.student_id)
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # Validate section exists and get course name for notification
    section_result = await db.execute(
        select(CourseSection)
        .options(selectinload(CourseSection.course))
        .where(CourseSection.section_id == data.section_id)
    )
    section = section_result.scalar_one_or_none()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course section not found",
        )

    # Check for duplicate attendance record
    dup_result = await db.execute(
        select(Attendance).where(
            Attendance.section_id == data.section_id,
            Attendance.student_id == data.student_id,
            Attendance.class_date == data.class_date,
        )
    )
    if dup_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance already recorded for this student on this date",
        )

    attendance = Attendance(
        section_id=data.section_id,
        student_id=data.student_id,
        class_date=data.class_date,
        attendance_status=data.attendance_status,
        arrival_time=data.arrival_time,
        notes=data.notes,
        recorded_by=current_user.user_id,
    )
    db.add(attendance)
    await db.flush()
    await db.refresh(attendance)

    # Send notification to the student
    course_name = section.course.course_name if section.course else None
    status_label = attendance.attendance_status.replace("_", " ").title()
    notif = Notification(
        user_id=student.student_id,
        title="Attendance Recorded",
        message=f"Your attendance for {course_name or f'Section #{data.section_id}'} on {data.class_date} has been marked as: {status_label}.",
        notification_type="info" if data.attendance_status == "present" else "warning",
        reference_type="attendance",
        reference_id=str(attendance.attendance_id),
    )
    db.add(notif)

    await db.commit()
    await db.refresh(attendance)
    return attendance


@router.post("/bulk", response_model=AttendanceListOut, status_code=status.HTTP_201_CREATED)
async def record_bulk_attendance(
    records: list[AttendanceCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher_or_admin),
):
    """Record attendance for multiple students at once. Requires teacher or admin."""
    if not records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No attendance records provided",
        )

    section_id = records[0].section_id
    class_date = records[0].class_date

    # Validate section exists
    section_result = await db.execute(
        select(CourseSection)
        .options(selectinload(CourseSection.course))
        .where(CourseSection.section_id == section_id)
    )
    section = section_result.scalar_one_or_none()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course section not found",
        )

    course_name = section.course.course_name if section.course else None
    created_records = []

    for data in records:
        # Validate section_id and class_date consistency
        if data.section_id != section_id or data.class_date != class_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All records must have the same section_id and class_date",
            )

        # Check for duplicates
        dup_result = await db.execute(
            select(Attendance).where(
                Attendance.section_id == data.section_id,
                Attendance.student_id == data.student_id,
                Attendance.class_date == data.class_date,
            )
        )
        if dup_result.scalar_one_or_none():
            continue  # Skip duplicates silently

        # Get student's user_id for notification
        student_result = await db.execute(
            select(Student).where(Student.student_id == data.student_id)
        )
        student = student_result.scalar_one_or_none()
        if not student:
            continue  # Skip invalid students

        attendance = Attendance(
            section_id=data.section_id,
            student_id=data.student_id,
            class_date=data.class_date,
            attendance_status=data.attendance_status,
            arrival_time=data.arrival_time,
            notes=data.notes,
            recorded_by=current_user.user_id,
        )
        db.add(attendance)
        await db.flush()
        await db.refresh(attendance)
        created_records.append(attendance)

        # Send notification
        status_label = attendance.attendance_status.replace("_", " ").title()
        notif = Notification(
            user_id=student.student_id,
            title="Attendance Recorded",
            message=f"Your attendance for {course_name or f'Section #{data.section_id}'} on {data.class_date} has been marked as: {status_label}.",
            notification_type="info" if data.attendance_status == "present" else "warning",
            reference_type="attendance",
            reference_id=str(attendance.attendance_id),
        )
        db.add(notif)

    await db.commit()

    # Refresh all created records
    for i, rec in enumerate(created_records):
        await db.refresh(rec)
        created_records[i] = rec

    return AttendanceListOut(
        attendance_records=created_records,
        total=len(created_records),
        page=1,
        per_page=len(created_records),
    )


@router.put("/{attendance_id}", response_model=AttendanceOut)
async def update_attendance(
    attendance_id: int,
    data: AttendanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher_or_admin),
):
    """Update an attendance record. Requires teacher or admin."""
    attendance = await _get_attendance_or_404(db, attendance_id)

    update_fields = data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(attendance, field, value)

    await db.commit()
    await db.refresh(attendance)
    return attendance


@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attendance(
    attendance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Delete an attendance record. Requires admin."""
    attendance = await _get_attendance_or_404(db, attendance_id)

    # Delete associated notifications
    await db.execute(
        delete(Notification).where(
            Notification.reference_type == "attendance",
            Notification.reference_id == str(attendance_id),
        )
    )

    await db.delete(attendance)
    await db.commit()
