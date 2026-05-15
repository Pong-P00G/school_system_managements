"""Pydantic schemas for people-related endpoints (Student, Faculty, Staff, etc.)."""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID
from app.schemas.user import UserOut
from app.schemas.academic import CourseSectionOut



# --- Student Account schemas ---
class StudentAccountBase(BaseModel):
    student_id: UUID
    account_number: str = Field(..., max_length=20)


class StudentAccountCreate(StudentAccountBase):
    pass


class StudentAccountUpdate(BaseModel):
    total_charges: Decimal | None = None
    total_payments: Decimal | None = None
    total_credits: Decimal | None = None
    balance: Decimal | None = None
    has_hold: bool | None = None
    hold_reason: str | None = None


class StudentAccountOut(BaseModel):
    account_id: int
    student_id: UUID
    account_number: str
    total_charges: Decimal = Decimal("0.00")
    total_payments: Decimal = Decimal("0.00")
    total_credits: Decimal = Decimal("0.00")
    balance: Decimal = Decimal("0.00")
    has_hold: bool
    hold_reason: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class StudentAccountListOut(BaseModel):
    accounts: list[StudentAccountOut]
    total: int


# --- Student schemas ---
class StudentBase(BaseModel):
    student_number: str = Field(..., max_length=20)
    program_id: int
    enrollment_date: date
    expected_graduation_date: date | None = None
    current_term_id: int | None = None
    academic_standing: str = "good_standing"
    enrollment_status: str = "active"
    advisor_id: UUID | None = None
    admission_type: str | None = None
    is_international: bool = False
    visa_type: str | None = None


class StudentCreate(StudentBase):
    user_id: UUID  # Link to existing user


class StudentUpdate(BaseModel):
    student_number: str | None = None
    program_id: int | None = None
    enrollment_date: date | None = None
    expected_graduation_date: date | None = None
    actual_graduation_date: date | None = None
    current_term_id: int | None = None
    academic_standing: str | None = None
    enrollment_status: str | None = None
    gpa: Decimal | None = None
    cumulative_gpa: Decimal | None = None
    total_credits_earned: int | None = None
    total_credits_attempted: int | None = None
    advisor_id: UUID | None = None
    admission_type: str | None = None
    is_international: bool | None = None
    visa_type: str | None = None


class StudentOut(BaseModel):
    student_id: UUID
    student_number: str
    program_id: int
    enrollment_date: date
    expected_graduation_date: date | None = None
    actual_graduation_date: date | None = None
    current_term_id: int | None = None
    academic_standing: str
    enrollment_status: str
    gpa: Decimal = Decimal("0.00")
    cumulative_gpa: Decimal = Decimal("0.00")
    total_credits_earned: int = 0
    total_credits_attempted: int = 0
    advisor_id: UUID | None = None
    admission_type: str | None = None
    is_international: bool
    visa_type: str | None = None
    account: StudentAccountOut | None = None
    user: UserOut | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class StudentListOut(BaseModel):
    students: list[StudentOut]
    total: int


# --- Faculty schemas ---
class FacultyBase(BaseModel):
    employee_number: str = Field(..., max_length=20)
    department_id: int
    hire_date: date
    faculty_rank: str = Field(..., max_length=50)
    tenure_status: str = Field(..., max_length=30)
    employment_type: str = Field(..., max_length=30)
    employment_status: str = "active"
    office_room_id: int | None = None
    office_hours: str | None = None
    research_interests: str | None = None
    specializations: list[str] | None = None
    publications_count: int = 0
    teaching_load_credits: int = 0
    max_advisees: int = 20
    current_advisees: int = 0


class FacultyCreate(FacultyBase):
    user_id: UUID  # Link to existing user


class FacultyUpdate(BaseModel):
    employee_number: str | None = None
    department_id: int | None = None
    hire_date: date | None = None
    termination_date: date | None = None
    faculty_rank: str | None = None
    tenure_status: str | None = None
    employment_type: str | None = None
    employment_status: str | None = None
    office_room_id: int | None = None
    office_hours: str | None = None
    research_interests: str | None = None
    specializations: list[str] | None = None
    publications_count: int | None = None
    teaching_load_credits: int | None = None
    max_advisees: int | None = None
    current_advisees: int | None = None


class FacultyOut(BaseModel):
    faculty_id: UUID
    employee_number: str
    department_id: int
    hire_date: date
    termination_date: date | None = None
    faculty_rank: str
    tenure_status: str
    employment_type: str
    employment_status: str
    office_room_id: int | None = None
    office_hours: str | None = None
    research_interests: str | None = None
    specializations: list[str] | None = None
    publications_count: int
    teaching_load_credits: int
    max_advisees: int
    current_advisees: int
    user: Optional[UserOut] = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class FacultyListOut(BaseModel):
    faculty: list[FacultyOut]
    total: int


# --- Staff schemas ---
class StaffBase(BaseModel):
    employee_number: str = Field(..., max_length=20)
    department_id: int | None = None
    hire_date: date
    job_title: str = Field(..., max_length=200)
    job_category: str = Field(..., max_length=50)
    employment_type: str = Field(..., max_length=30)
    employment_status: str = "active"
    office_room_id: int | None = None
    supervisor_id: UUID | None = None
    salary_grade: str | None = None


class StaffCreate(StaffBase):
    user_id: UUID  # Link to existing user


class StaffUpdate(BaseModel):
    employee_number: str | None = None
    department_id: int | None = None
    hire_date: date | None = None
    termination_date: date | None = None
    job_title: str | None = None
    job_category: str | None = None
    employment_type: str | None = None
    employment_status: str | None = None
    office_room_id: int | None = None
    supervisor_id: UUID | None = None
    salary_grade: str | None = None


class StaffOut(BaseModel):
    staff_id: UUID
    employee_number: str
    department_id: int | None = None
    hire_date: date
    termination_date: date | None = None
    job_title: str
    job_category: str
    employment_type: str
    employment_status: str
    office_room_id: int | None = None
    supervisor_id: UUID | None = None
    salary_grade: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class StaffListOut(BaseModel):
    staff: list[StaffOut]
    total: int


# --- Enrollment schemas ---
class EnrollmentBase(BaseModel):
    student_id: UUID
    section_id: int
    enrollment_status: str = "enrolled"
    is_audit: bool = False


class EnrollmentCreate(EnrollmentBase):
    pass


class EnrollmentUpdate(BaseModel):
    enrollment_status: str | None = None
    grade: str | None = None
    grade_points: Decimal | None = None
    credits_earned: int | None = None
    attendance_percentage: Decimal | None = None
    midterm_grade: str | None = None
    final_grade: str | None = None
    is_audit: bool | None = None
    withdrawal_reason: str | None = None


class EnrollmentOut(BaseModel):
    enrollment_id: int
    student_id: UUID
    section_id: int
    enrollment_date: datetime | None = None
    enrollment_status: str
    grade: str | None = None
    grade_points: Decimal | None = None
    credits_earned: int = 0
    attendance_percentage: Decimal | None = None
    midterm_grade: str | None = None
    final_grade: str | None = None
    grade_submitted_date: datetime | None = None
    is_audit: bool
    withdrawal_date: datetime | None = None
    withdrawal_reason: str | None = None
    student: StudentOut | None = None
    section: CourseSectionOut | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class EnrollmentListOut(BaseModel):
    enrollments: list[EnrollmentOut]
    total: int


# --- Assignment schemas ---
class AssignmentBase(BaseModel):
    section_id: int
    assignment_name: str = Field(..., max_length=200)
    assignment_type: str = Field(..., max_length=50)
    description: str | None = None
    max_points: Decimal
    weight_percentage: Decimal | None = None
    due_date: datetime | None = None
    late_submission_allowed: bool = False
    late_penalty_percentage: Decimal | None = None
    submission_type: str | None = None
    rubric_url: str | None = None
    is_published: bool = False
    is_group_assignment: bool = False


class AssignmentCreate(AssignmentBase):
    created_by: UUID | None = None


class AssignmentUpdate(BaseModel):
    assignment_name: str | None = None
    assignment_type: str | None = None
    description: str | None = None
    max_points: Decimal | None = None
    weight_percentage: Decimal | None = None
    due_date: datetime | None = None
    late_submission_allowed: bool | None = None
    late_penalty_percentage: Decimal | None = None
    submission_type: str | None = None
    rubric_url: str | None = None
    is_published: bool | None = None
    is_group_assignment: bool | None = None


class AssignmentOut(BaseModel):
    assignment_id: int
    section_id: int
    assignment_name: str
    assignment_type: str
    description: str | None = None
    max_points: Decimal
    weight_percentage: Decimal | None = None
    due_date: datetime | None = None
    late_submission_allowed: bool
    late_penalty_percentage: Decimal | None = None
    submission_type: str | None = None
    rubric_url: str | None = None
    is_published: bool
    is_group_assignment: bool
    created_by: UUID
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class AssignmentListOut(BaseModel):
    assignments: list[AssignmentOut]
    total: int


# --- Assignment Submission schemas ---
class AssignmentSubmissionBase(BaseModel):
    assignment_id: int
    student_id: UUID
    submission_url: str | None = None
    submission_text: str | None = None
    attachment_count: int = 0


class AssignmentSubmissionCreate(AssignmentSubmissionBase):
    pass


class AssignmentSubmissionUpdate(BaseModel):
    submission_url: str | None = None
    submission_text: str | None = None
    attachment_count: int | None = None
    points_earned: Decimal | None = None
    feedback: str | None = None
    graded_by: UUID | None = None
    graded_date: datetime | None = None
    submission_status: str | None = None


class AssignmentSubmissionOut(BaseModel):
    submission_id: int
    assignment_id: int
    student_id: UUID
    submission_date: datetime | None = None
    submission_url: str | None = None
    submission_text: str | None = None
    attachment_count: int
    is_late: bool
    points_earned: Decimal | None = None
    feedback: str | None = None
    graded_by: UUID | None = None
    graded_date: datetime | None = None
    submission_status: str
    attempts: int
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class AssignmentSubmissionListOut(BaseModel):
    submissions: list[AssignmentSubmissionOut]
    total: int


# --- Attendance schemas ---
class AttendanceBase(BaseModel):
    section_id: int
    student_id: UUID
    class_date: date
    attendance_status: str
    arrival_time: str | None = None
    notes: str | None = None


class AttendanceCreate(AttendanceBase):
    recorded_by: UUID


class AttendanceUpdate(BaseModel):
    attendance_status: str | None = None
    arrival_time: str | None = None
    notes: str | None = None


class AttendanceOut(BaseModel):
    attendance_id: int
    section_id: int
    student_id: UUID
    class_date: date
    attendance_status: str
    arrival_time: str | None = None
    notes: str | None = None
    recorded_by: UUID
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class AttendanceListOut(BaseModel):
    attendance_records: list[AttendanceOut]
    total: int





# --- Financial Transaction schemas ---
class FinancialTransactionBase(BaseModel):
    account_id: int
    term_id: int | None = None
    transaction_type: str
    transaction_category: str | None = None
    amount: Decimal
    description: str | None = None
    reference_number: str | None = None
    posted_date: date | None = None
    payment_method: str | None = None
    check_number: str | None = None
    card_last_four: str | None = None


class FinancialTransactionCreate(FinancialTransactionBase):
    processed_by: UUID


class FinancialTransactionUpdate(BaseModel):
    transaction_category: str | None = None
    description: str | None = None
    reference_number: str | None = None
    posted_date: date | None = None
    is_reversed: bool | None = None


class FinancialTransactionOut(BaseModel):
    transaction_id: int
    account_id: int
    term_id: int | None = None
    transaction_type: str
    transaction_category: str | None = None
    amount: Decimal
    description: str | None = None
    reference_number: str | None = None
    transaction_date: datetime | None = None
    posted_date: date | None = None
    processed_by: UUID
    payment_method: str | None = None
    check_number: str | None = None
    card_last_four: str | None = None
    is_reversed: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class FinancialTransactionListOut(BaseModel):
    transactions: list[FinancialTransactionOut]
    total: int