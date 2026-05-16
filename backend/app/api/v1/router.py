"""API v1 router aggregating all endpoint routers."""

from fastapi import APIRouter
from app.api.v1 import (
    health, auth, users, departments, courses, programs, 
    students, faculty, staff, enrollments, terms, sections,
    assignments, reviews, notifications, attendance, roles, permissions
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(departments.router, prefix="/departments", tags=["Departments"])
api_router.include_router(courses.router, prefix="/courses", tags=["Courses"])
api_router.include_router(programs.router, prefix="/programs", tags=["Programs"])
api_router.include_router(students.router, prefix="/students", tags=["Students"])
api_router.include_router(faculty.router, prefix="/faculty", tags=["Faculty"])
api_router.include_router(staff.router, prefix="/staff", tags=["Staff"])
api_router.include_router(enrollments.router, prefix="/enrollments", tags=["Enrollments"])
api_router.include_router(terms.router, prefix="/terms", tags=["Academic Terms"])
api_router.include_router(sections.router, prefix="/sections", tags=["Course Sections"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["Assignments"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["Permissions"])
