"""SQLAlchemy models reflecting the school_system_db_v2 schema."""

from app.models.user import User, UserRole, UserRoleAssignment, UserPersonalInfo, Permission, RolePermission, PagePermission
from app.models.academic import (
    Department, Program, Course, AcademicTerm, Building, Room, CourseSection
)
from app.models.people import (
    Student, Faculty, Staff, Enrollment, Assignment, AssignmentSubmission,
    Attendance, StudentAccount, FinancialTransaction
)
from app.models.review import Review
from app.models.notification import Notification

__all__ = [
    # User models
    "User",
    "UserRole",
    "UserRoleAssignment",
    "UserPersonalInfo",
    "Permission",
    "RolePermission",
    "PagePermission",
    # Academic models
    "Department",
    "Program",
    "Course",
    "AcademicTerm",
    "Building",
    "Room",
    "CourseSection",
    # People models
    "Student",
    "Faculty",
    "Staff",
    "Enrollment",
    "Assignment",
    "AssignmentSubmission",
    "Attendance",
    "StudentAccount",
    "FinancialTransaction",
    "AssignmentTeam",
    "AssignmentTeamMember",
    # Review models
    "Review",
    # Notification model
    "Notification",
]

from app.models.groups import AssignmentTeam, AssignmentTeamMember
