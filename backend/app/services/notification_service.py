"""Notification service for automatically creating notifications on system events."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.notification import Notification
from app.models.people import Enrollment, Student
from app.models.academic import CourseSection, Course


async def notify_enrollment_created(
    db: AsyncSession,
    student_id: UUID,
    section_id: int,
    course_name: str | None = None,
):
    """Send a notification to a student when they are enrolled in a course section."""
    if not course_name:
        section_result = await db.execute(
            select(CourseSection)
            .options(selectinload(CourseSection.course))
            .where(CourseSection.section_id == section_id)
        )
        section = section_result.scalar_one_or_none()
        if section and section.course:
            course_name = section.course.course_name
        else:
            course_name = f"Section #{section_id}"

    notification = Notification(
        user_id=student_id,
        title="Enrolled in Course",
        message=f"You have been enrolled in {course_name}.",
        notification_type="success",
        reference_type="enrollment",
        reference_id=str(section_id),
    )
    db.add(notification)


async def notify_grade_submitted(
    db: AsyncSession,
    student_id: UUID,
    enrollment_id: int,
    grade: str,
    course_name: str | None = None,
):
    """Send a notification to a student when a grade is submitted."""
    if not course_name:
        enrollment_result = await db.execute(
            select(Enrollment)
            .options(
                selectinload(Enrollment.section)
                .selectinload(CourseSection.course)
            )
            .where(Enrollment.enrollment_id == enrollment_id)
        )
        enrollment = enrollment_result.scalar_one_or_none()
        if enrollment and enrollment.section and enrollment.section.course:
            course_name = enrollment.section.course.course_name
        else:
            course_name = f"Enrollment #{enrollment_id}"

    notification = Notification(
        user_id=student_id,
        title="Grade Posted",
        message=f"Your grade for {course_name} has been posted: {grade}.",
        notification_type="info",
        reference_type="grade",
        reference_id=str(enrollment_id),
    )
    db.add(notification)


async def notify_withdrawal(
    db: AsyncSession,
    student_id: UUID,
    section_id: int,
    course_name: str | None = None,
):
    """Send a notification to a student when they are withdrawn from a section."""
    if not course_name:
        section_result = await db.execute(
            select(CourseSection)
            .options(selectinload(CourseSection.course))
            .where(CourseSection.section_id == section_id)
        )
        section = section_result.scalar_one_or_none()
        if section and section.course:
            course_name = section.course.course_name
        else:
            course_name = f"Section #{section_id}"

    notification = Notification(
        user_id=student_id,
        title="Withdrawn from Course",
        message=f"You have been withdrawn from {course_name}.",
        notification_type="warning",
        reference_type="enrollment",
        reference_id=str(section_id),
    )
    db.add(notification)


async def notify_assignment_created(
    db: AsyncSession,
    section_id: int,
    assignment_name: str,
    student_ids: list[UUID] | None = None,
):
    """Send notifications to all enrolled students when a new assignment is created.

    If student_ids is provided, only notify those students. Otherwise, notify all
    enrolled students in the section.
    """
    if student_ids is None:
        enrollment_result = await db.execute(
            select(Enrollment).where(
                Enrollment.section_id == section_id,
                Enrollment.enrollment_status == "enrolled",
            )
        )
        enrollments = enrollment_result.scalars().all()
        student_ids = [e.student_id for e in enrollments]

    for sid in student_ids:
        notification = Notification(
            user_id=sid,
            title="New Assignment",
            message=f"A new assignment has been posted: {assignment_name}.",
            notification_type="info",
            reference_type="assignment",
            reference_id=str(section_id),
        )
        db.add(notification)

