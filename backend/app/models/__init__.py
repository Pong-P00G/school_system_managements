"""SQLAlchemy models reflecting the school_system_db_v2 schema."""

from app.models.user import User, UserRole, UserRoleAssignment, UserPersonalInfo
from app.models.academic import (
    Department, Program, Course, AcademicTerm, Building, Room, CourseSection
)
from app.models.people import (
    Student, Faculty, Staff, Enrollment, Assignment, AssignmentSubmission,
    Attendance, StudentAccount, FinancialTransaction
)

__all__ = [
    # User models
    "User",
    "UserRole",
    "UserRoleAssignment",
    "UserPersonalInfo",
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
]

from app.models.groups import AssignmentTeam, AssignmentTeamMember
