"""Attendance management API endpoints."""

from uuid import UUID
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_current_admin, get_current_teacher_or_admin
from app.core.database import get_db
from app.models.people import Attendance, Student, Enrollment
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

ABSENT_ALERT_THRESHOLD = 3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_attendance_or_404(db: AsyncSession, attendance_id: int) -> Attendance:
    result = await db.execute(
        select(Attendance).where(Attendance.attendance_id == attendance_id)
    )
    attendance = result.scalar_one_or_none()
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return attendance


async def _sync_enrollment_attendance(db: AsyncSession, section_id: int, student_id: UUID):
    """Recalculate and update attendance_percentage on the enrollment."""
    total = await db.scalar(
        select(func.count(Attendance.attendance_id)).where(
            Attendance.section_id == section_id,
            Attendance.student_id == student_id,
        )
    )
    present = await db.scalar(
        select(func.count(Attendance.attendance_id)).where(
            Attendance.section_id == section_id,
            Attendance.student_id == student_id,
            Attendance.attendance_status.in_(["present", "late"]),
        )
    )
    pct = round(present / total * 100, 2) if total > 0 else 0

    enrollment = await db.scalar(
        select(Enrollment).where(
            Enrollment.section_id == section_id,
            Enrollment.student_id == student_id,
        )
    )
    if enrollment:
        enrollment.attendance_percentage = pct


async def _check_absent_alert(db: AsyncSession, section_id: int, student_id: UUID, course_name: str | None):
    """Send alert if student hits absence threshold."""
    absent_count = await db.scalar(
        select(func.count(Attendance.attendance_id)).where(
            Attendance.section_id == section_id,
            Attendance.student_id == student_id,
            Attendance.attendance_status == "absent",
        )
    )
    if absent_count and absent_count >= ABSENT_ALERT_THRESHOLD and absent_count % ABSENT_ALERT_THRESHOLD == 0:
        notif = Notification(
            user_id=student_id,
            title="Attendance Warning",
            message=f"You have {absent_count} absences in {course_name or 'a course'}. Please contact your instructor.",
            notification_type="error",
            reference_type="attendance_alert",
            reference_id=str(section_id),
        )
        db.add(notif)


def _validate_not_future(class_date: date):
    if class_date > date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot record attendance for a future date",
        )


# ---------------------------------------------------------------------------
# Section endpoints (teacher/admin)
# ---------------------------------------------------------------------------

@router.get("/section/{section_id}", response_model=AttendanceListOut)
async def get_section_attendance(
    section_id: int,
    class_date: date | None = Query(None),
    start_date: date | None = Query(None, description="Filter from date"),
    end_date: date | None = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher_or_admin),
):
    """Get attendance records for a section with date-range filtering."""
    section = await db.scalar(
        select(CourseSection).where(CourseSection.section_id == section_id)
    )
    if not section:
        raise HTTPException(status_code=404, detail="Course section not found")

    query = select(Attendance).options(
        selectinload(Attendance.student).selectinload(Student.user)
    ).where(Attendance.section_id == section_id)

    count_query = select(func.count(Attendance.attendance_id)).where(
        Attendance.section_id == section_id
    )

    if class_date:
        query = query.where(Attendance.class_date == class_date)
        count_query = count_query.where(Attendance.class_date == class_date)
    if start_date:
        query = query.where(Attendance.class_date >= start_date)
        count_query = count_query.where(Attendance.class_date >= start_date)
    if end_date:
        query = query.where(Attendance.class_date <= end_date)
        count_query = count_query.where(Attendance.class_date <= end_date)

    total = await db.scalar(count_query) or 0
    query = query.order_by(Attendance.class_date.desc(), Attendance.student_id)
    query = query.offset((page - 1) * per_page).limit(per_page)
    records = (await db.execute(query)).scalars().all()

    return AttendanceListOut(attendance_records=records, total=total, page=page, per_page=per_page)


@router.get("/section/{section_id}/summary")
async def get_section_attendance_summary(
    section_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher_or_admin),
):
    """Get per-student attendance summary for a section."""
    section = await db.scalar(
        select(CourseSection).options(selectinload(CourseSection.course))
        .where(CourseSection.section_id == section_id)
    )
    if not section:
        raise HTTPException(status_code=404, detail="Course section not found")

    # Get all students with their attendance counts
    result = await db.execute(
        select(
            Attendance.student_id,
            Attendance.attendance_status,
            func.count(Attendance.attendance_id),
        )
        .where(Attendance.section_id == section_id)
        .group_by(Attendance.student_id, Attendance.attendance_status)
    )
    rows = result.all()

    # Build per-student summary
    students: dict = {}
    for student_id, att_status, count in rows:
        if student_id not in students:
            students[student_id] = {"student_id": str(student_id), "present": 0, "absent": 0, "late": 0, "excused": 0, "total": 0}
        students[student_id][att_status] = students[student_id].get(att_status, 0) + count
        students[student_id]["total"] += count

    for s in students.values():
        s["attendance_rate"] = round((s["present"] + s["late"]) / s["total"] * 100, 1) if s["total"] > 0 else 0

    # Total class sessions
    total_dates = await db.scalar(
        select(func.count(func.distinct(Attendance.class_date)))
        .where(Attendance.section_id == section_id)
    )

    return {
        "section_id": section_id,
        "course_name": section.course.course_name if section.course else None,
        "total_sessions": total_dates or 0,
        "students": list(students.values()),
    }


# ---------------------------------------------------------------------------
# Student endpoints
# ---------------------------------------------------------------------------

@router.get("/my", response_model=AttendanceListOut)
async def get_my_attendance(
    section_id: int | None = Query(None),
    class_date: date | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get attendance records for the current student with date-range filtering."""
    student = await db.scalar(
        select(Student).where(Student.student_id == current_user.user_id)
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    query = (
        select(Attendance)
        .options(selectinload(Attendance.section).selectinload(CourseSection.course))
        .where(Attendance.student_id == student.student_id)
    )
    count_query = select(func.count(Attendance.attendance_id)).where(
        Attendance.student_id == student.student_id
    )

    if section_id:
        query = query.where(Attendance.section_id == section_id)
        count_query = count_query.where(Attendance.section_id == section_id)
    if class_date:
        query = query.where(Attendance.class_date == class_date)
        count_query = count_query.where(Attendance.class_date == class_date)
    if start_date:
        query = query.where(Attendance.class_date >= start_date)
        count_query = count_query.where(Attendance.class_date >= start_date)
    if end_date:
        query = query.where(Attendance.class_date <= end_date)
        count_query = count_query.where(Attendance.class_date <= end_date)

    total = await db.scalar(count_query) or 0
    query = query.order_by(Attendance.class_date.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    records = (await db.execute(query)).scalars().all()

    return AttendanceListOut(attendance_records=records, total=total, page=page, per_page=per_page)


@router.get("/my/summary")
async def get_my_attendance_summary(
    section_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get attendance summary for the current student."""
    student = await db.scalar(
        select(Student).where(Student.student_id == current_user.user_id)
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    query = (
        select(Attendance.attendance_status, func.count(Attendance.attendance_id))
        .where(Attendance.student_id == student.student_id)
    )
    if section_id:
        query = query.where(Attendance.section_id == section_id)
    query = query.group_by(Attendance.attendance_status)

    rows = (await db.execute(query)).all()
    summary = {row[0]: row[1] for row in rows}
    total = sum(summary.values())
    return {
        "total_classes": total,
        "present": summary.get("present", 0),
        "absent": summary.get("absent", 0),
        "late": summary.get("late", 0),
        "excused": summary.get("excused", 0),
        "attendance_rate": round((summary.get("present", 0) + summary.get("late", 0)) / total * 100, 1) if total > 0 else 0,
    }


# ---------------------------------------------------------------------------
# Single record
# ---------------------------------------------------------------------------

@router.get("/{attendance_id}", response_model=AttendanceOut)
async def get_attendance_record(
    attendance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single attendance record."""
    return await _get_attendance_or_404(db, attendance_id)


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@router.post("/", response_model=AttendanceOut, status_code=status.HTTP_201_CREATED)
async def record_attendance(
    data: AttendanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher_or_admin),
):
    """Record attendance for a student. Validates no future dates."""
    _validate_not_future(data.class_date)

    student = await db.scalar(select(Student).where(Student.student_id == data.student_id))
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    section = await db.scalar(
        select(CourseSection).options(selectinload(CourseSection.course))
        .where(CourseSection.section_id == data.section_id)
    )
    if not section:
        raise HTTPException(status_code=404, detail="Course section not found")

    # Check duplicate
    dup = await db.scalar(
        select(Attendance).where(
            Attendance.section_id == data.section_id,
            Attendance.student_id == data.student_id,
            Attendance.class_date == data.class_date,
        )
    )
    if dup:
        raise HTTPException(status_code=409, detail="Attendance already recorded for this student on this date")

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

    # Notification
    course_name = section.course.course_name if section.course else None
    status_label = data.attendance_status.replace("_", " ").title()
    db.add(Notification(
        user_id=student.student_id,
        title="Attendance Recorded",
        message=f"Your attendance for {course_name or f'Section #{data.section_id}'} on {data.class_date} has been marked as: {status_label}.",
        notification_type="info" if data.attendance_status == "present" else "warning",
        reference_type="attendance",
        reference_id=str(attendance.attendance_id),
    ))

    # Sync enrollment percentage
    await _sync_enrollment_attendance(db, data.section_id, data.student_id)

    # Check absent alert
    if data.attendance_status == "absent":
        await _check_absent_alert(db, data.section_id, data.student_id, course_name)

    await db.commit()
    await db.refresh(attendance)
    return attendance


# ---------------------------------------------------------------------------
# Bulk create
# ---------------------------------------------------------------------------

@router.post("/bulk", response_model=AttendanceListOut, status_code=status.HTTP_201_CREATED)
async def record_bulk_attendance(
    records: list[AttendanceCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher_or_admin),
):
    """Record attendance for multiple students at once."""
    if not records:
        raise HTTPException(status_code=400, detail="No attendance records provided")

    section_id = records[0].section_id
    class_date = records[0].class_date
    _validate_not_future(class_date)

    section = await db.scalar(
        select(CourseSection).options(selectinload(CourseSection.course))
        .where(CourseSection.section_id == section_id)
    )
    if not section:
        raise HTTPException(status_code=404, detail="Course section not found")

    course_name = section.course.course_name if section.course else None
    created = []

    for data in records:
        if data.section_id != section_id or data.class_date != class_date:
            raise HTTPException(status_code=400, detail="All records must have the same section_id and class_date")

        dup = await db.scalar(
            select(Attendance).where(
                Attendance.section_id == data.section_id,
                Attendance.student_id == data.student_id,
                Attendance.class_date == data.class_date,
            )
        )
        if dup:
            continue

        student = await db.scalar(select(Student).where(Student.student_id == data.student_id))
        if not student:
            continue

        att = Attendance(
            section_id=data.section_id, student_id=data.student_id,
            class_date=data.class_date, attendance_status=data.attendance_status,
            arrival_time=data.arrival_time, notes=data.notes,
            recorded_by=current_user.user_id,
        )
        db.add(att)
        await db.flush()
        await db.refresh(att)
        created.append(att)

        status_label = data.attendance_status.replace("_", " ").title()
        db.add(Notification(
            user_id=student.student_id,
            title="Attendance Recorded",
            message=f"Your attendance for {course_name or f'Section #{data.section_id}'} on {data.class_date} has been marked as: {status_label}.",
            notification_type="info" if data.attendance_status == "present" else "warning",
            reference_type="attendance",
            reference_id=str(att.attendance_id),
        ))

        await _sync_enrollment_attendance(db, data.section_id, data.student_id)
        if data.attendance_status == "absent":
            await _check_absent_alert(db, data.section_id, data.student_id, course_name)

    await db.commit()
    for rec in created:
        await db.refresh(rec)

    return AttendanceListOut(attendance_records=created, total=len(created), page=1, per_page=len(created) or 1)


# ---------------------------------------------------------------------------
# Bulk update
# ---------------------------------------------------------------------------

@router.put("/bulk", response_model=AttendanceListOut)
async def bulk_update_attendance(
    updates: list[AttendanceUpdate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher_or_admin),
):
    """Bulk update attendance records. Each item must include attendance_id."""
    updated = []
    for data in updates:
        if not data.attendance_id:
            continue
        att = await db.scalar(
            select(Attendance).where(Attendance.attendance_id == data.attendance_id)
        )
        if not att:
            continue
        fields = data.model_dump(exclude_unset=True, exclude={"attendance_id"})
        for k, v in fields.items():
            setattr(att, k, v)
        updated.append(att)

        # Sync percentage
        await _sync_enrollment_attendance(db, att.section_id, att.student_id)

    await db.commit()
    for rec in updated:
        await db.refresh(rec)

    return AttendanceListOut(attendance_records=updated, total=len(updated), page=1, per_page=len(updated) or 1)


# ---------------------------------------------------------------------------
# Update / Delete
# ---------------------------------------------------------------------------

@router.put("/{attendance_id}", response_model=AttendanceOut)
async def update_attendance(
    attendance_id: int,
    data: AttendanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher_or_admin),
):
    """Update an attendance record."""
    attendance = await _get_attendance_or_404(db, attendance_id)
    fields = data.model_dump(exclude_unset=True, exclude={"attendance_id"})
    for k, v in fields.items():
        setattr(attendance, k, v)

    await _sync_enrollment_attendance(db, attendance.section_id, attendance.student_id)
    await db.commit()
    await db.refresh(attendance)
    return attendance


@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attendance(
    attendance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Delete an attendance record."""
    attendance = await _get_attendance_or_404(db, attendance_id)
    section_id, student_id = attendance.section_id, attendance.student_id

    await db.execute(
        delete(Notification).where(
            Notification.reference_type == "attendance",
            Notification.reference_id == str(attendance_id),
        )
    )
    await db.delete(attendance)
    await _sync_enrollment_attendance(db, section_id, student_id)
    await db.commit()
