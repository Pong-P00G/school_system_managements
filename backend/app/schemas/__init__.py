"""Pydantic schemas for the school management system."""

from app.schemas.user import (
    LoginRequest, TokenResponse, UserBase, UserCreate, UserOut, UserListOut,
    UserPersonalInfoOut, UserRoleOut
)
from app.schemas.academic import (
    DepartmentBase, DepartmentCreate, DepartmentUpdate, DepartmentOut, DepartmentListOut,
    ProgramBase, ProgramCreate, ProgramUpdate, ProgramOut, ProgramListOut,
    CourseBase, CourseCreate, CourseUpdate, CourseOut, CourseListOut,
    AcademicTermBase, AcademicTermCreate, AcademicTermUpdate, AcademicTermOut, AcademicTermListOut,
    BuildingBase, BuildingCreate, BuildingUpdate, BuildingOut, BuildingListOut,
    RoomBase, RoomCreate, RoomUpdate, RoomOut, RoomListOut,
    CourseSectionBase, CourseSectionCreate, CourseSectionUpdate, CourseSectionOut, CourseSectionListOut
)
from app.schemas.people import (
    StudentBase, StudentCreate, StudentUpdate, StudentOut, StudentListOut,
    FacultyBase, FacultyCreate, FacultyUpdate, FacultyOut, FacultyListOut,
    StaffBase, StaffCreate, StaffUpdate, StaffOut, StaffListOut,
    EnrollmentBase, EnrollmentCreate, EnrollmentUpdate, EnrollmentOut, EnrollmentListOut,
    AssignmentBase, AssignmentCreate, AssignmentUpdate, AssignmentOut, AssignmentListOut,
    AssignmentSubmissionBase, AssignmentSubmissionCreate, AssignmentSubmissionUpdate, AssignmentSubmissionOut, AssignmentSubmissionListOut,
    AttendanceBase, AttendanceCreate, AttendanceUpdate, AttendanceOut, AttendanceListOut,
    StudentAccountBase, StudentAccountCreate, StudentAccountUpdate, StudentAccountOut, StudentAccountListOut,
    FinancialTransactionBase, FinancialTransactionCreate, FinancialTransactionUpdate, FinancialTransactionOut, FinancialTransactionListOut
)

__all__ = [
    # User schemas
    "LoginRequest",
    "TokenResponse",
    "UserBase",
    "UserCreate",
    "UserOut",
    "UserListOut",
    "UserPersonalInfoOut",
    "UserRoleOut",
    # Department schemas
    "DepartmentBase",
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentOut",
    "DepartmentListOut",
    # Program schemas
    "ProgramBase",
    "ProgramCreate",
    "ProgramUpdate",
    "ProgramOut",
    "ProgramListOut",
    # Course schemas
    "CourseBase",
    "CourseCreate",
    "CourseUpdate",
    "CourseOut",
    "CourseListOut",
    # Academic Term schemas
    "AcademicTermBase",
    "AcademicTermCreate",
    "AcademicTermUpdate",
    "AcademicTermOut",
    "AcademicTermListOut",
    # Building schemas
    "BuildingBase",
    "BuildingCreate",
    "BuildingUpdate",
    "BuildingOut",
    "BuildingListOut",
    # Room schemas
    "RoomBase",
    "RoomCreate",
    "RoomUpdate",
    "RoomOut",
    "RoomListOut",
    # Course Section schemas
    "CourseSectionBase",
    "CourseSectionCreate",
    "CourseSectionUpdate",
    "CourseSectionOut",
    "CourseSectionListOut",
    # Student schemas
    "StudentBase",
    "StudentCreate",
    "StudentUpdate",
    "StudentOut",
    "StudentListOut",
    # Faculty schemas
    "FacultyBase",
    "FacultyCreate",
    "FacultyUpdate",
    "FacultyOut",
    "FacultyListOut",
    # Staff schemas
    "StaffBase",
    "StaffCreate",
    "StaffUpdate",
    "StaffOut",
    "StaffListOut",
    # Enrollment schemas
    "EnrollmentBase",
    "EnrollmentCreate",
    "EnrollmentUpdate",
    "EnrollmentOut",
    "EnrollmentListOut",
    # Assignment schemas
    "AssignmentBase",
    "AssignmentCreate",
    "AssignmentUpdate",
    "AssignmentOut",
    "AssignmentListOut",
    # Assignment Submission schemas
    "AssignmentSubmissionBase",
    "AssignmentSubmissionCreate",
    "AssignmentSubmissionUpdate",
    "AssignmentSubmissionOut",
    "AssignmentSubmissionListOut",
    # Attendance schemas
    "AttendanceBase",
    "AttendanceCreate",
    "AttendanceUpdate",
    "AttendanceOut",
    "AttendanceListOut",
    # Student Account schemas
    "StudentAccountBase",
    "StudentAccountCreate",
    "StudentAccountUpdate",
    "StudentAccountOut",
    "StudentAccountListOut",
    # Financial Transaction schemas
    "FinancialTransactionBase",
    "FinancialTransactionCreate",
    "FinancialTransactionUpdate",
    "FinancialTransactionOut",
    "FinancialTransactionListOut",
]
