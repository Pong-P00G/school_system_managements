import uuid
from datetime import datetime
from app.core.database import utcnow
from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Text, Date, Time, ForeignKey, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    student_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    student_number = Column(String(20), unique=True, nullable=False)
    program_id = Column(Integer, ForeignKey("programs.program_id", ondelete="CASCADE"), nullable=False)
    enrollment_date = Column(Date, nullable=False)
    expected_graduation_date = Column(Date, nullable=True)
    actual_graduation_date = Column(Date, nullable=True)
    current_term_id = Column(Integer, ForeignKey("academic_terms.term_id", ondelete="SET NULL"), nullable=True)
    academic_standing = Column(String(50), default="good_standing")
    enrollment_status = Column(String(50), default="active")
    gpa = Column(Numeric(3, 2), default=0.00)
    cumulative_gpa = Column(Numeric(3, 2), default=0.00)
    total_credits_earned = Column(Integer, default=0)
    total_credits_attempted = Column(Integer, default=0)
    advisor_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    admission_type = Column(String(50), nullable=True)
    is_international = Column(Boolean, default=False)
    visa_type = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[student_id], lazy="selectin")
    program = relationship("Program", back_populates="students", lazy="selectin")
    enrollments = relationship("Enrollment", back_populates="student", lazy="selectin", passive_deletes="all")
    attendance_records = relationship("Attendance", back_populates="student", lazy="selectin", passive_deletes="all")
    account = relationship("StudentAccount", back_populates="student", uselist=False, lazy="selectin", passive_deletes="all")


class Faculty(Base):
    __tablename__ = "faculty"

    faculty_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    employee_number = Column(String(20), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.department_id", ondelete="CASCADE"), nullable=False)
    hire_date = Column(Date, nullable=False)
    termination_date = Column(Date, nullable=True)
    faculty_rank = Column(String(50), nullable=False)
    tenure_status = Column(String(30), nullable=False)
    employment_type = Column(String(30), nullable=False)
    employment_status = Column(String(20), default="active")
    office_room_id = Column(Integer, ForeignKey("rooms.room_id", ondelete="SET NULL"), nullable=True)
    office_hours = Column(Text, nullable=True)
    research_interests = Column(Text, nullable=True)
    specializations = Column(ARRAY(Text), nullable=True)
    publications_count = Column(Integer, default=0)
    teaching_load_credits = Column(Integer, default=0)
    max_advisees = Column(Integer, default=20)
    current_advisees = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[faculty_id], lazy="selectin")
    reviews = relationship("Review", back_populates="faculty", passive_deletes="all")


class Staff(Base):
    __tablename__ = "staff"

    staff_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    employee_number = Column(String(20), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.department_id", ondelete="SET NULL"), nullable=True)
    hire_date = Column(Date, nullable=False)
    termination_date = Column(Date, nullable=True)
    job_title = Column(String(200), nullable=False)
    job_category = Column(String(50), nullable=False)
    employment_type = Column(String(30), nullable=False)
    employment_status = Column(String(20), default="active")
    office_room_id = Column(Integer, ForeignKey("rooms.room_id", ondelete="SET NULL"), nullable=True)
    supervisor_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    salary_grade = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[staff_id], lazy="selectin")


class Enrollment(Base):
    __tablename__ = "enrollments"

    enrollment_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    section_id = Column(Integer, ForeignKey("course_sections.section_id", ondelete="CASCADE"), nullable=False)
    enrollment_date = Column(DateTime, default=utcnow)
    enrollment_status = Column(String(20), default="enrolled")
    grade = Column(String(5), nullable=True)
    grade_points = Column(Numeric(3, 2), nullable=True)
    credits_earned = Column(Integer, default=0)
    attendance_percentage = Column(Numeric(5, 2), nullable=True)
    midterm_grade = Column(String(5), nullable=True)
    final_grade = Column(String(5), nullable=True)
    grade_submitted_date = Column(DateTime, nullable=True)
    grade_submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    is_audit = Column(Boolean, default=False)
    withdrawal_date = Column(DateTime, nullable=True)
    withdrawal_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    student = relationship("Student", back_populates="enrollments")
    section = relationship("CourseSection", back_populates="enrollments")
    reviews = relationship("Review", back_populates="enrollment", cascade="all, delete-orphan")





class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"

    submission_id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey("assignments.assignment_id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    submission_date = Column(DateTime, default=utcnow)
    submission_url = Column(Text, nullable=True)
    submission_text = Column(Text, nullable=True)
    attachment_count = Column(Integer, default=0)
    is_late = Column(Boolean, default=False)
    points_earned = Column(Numeric(6, 2), nullable=True)
    feedback = Column(Text, nullable=True)
    graded_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    graded_date = Column(DateTime, nullable=True)
    submission_status = Column(String(20), default="submitted")
    attempts = Column(Integer, default=1)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")


class Assignment(Base):
    __tablename__ = "assignments"

    assignment_id = Column(Integer, primary_key=True, autoincrement=True)
    section_id = Column(Integer, ForeignKey("course_sections.section_id", ondelete="CASCADE"), nullable=False)
    assignment_name = Column(String(200), nullable=False)
    assignment_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    max_points = Column(Numeric(6, 2), nullable=False)
    weight_percentage = Column(Numeric(5, 2), nullable=True)
    due_date = Column(DateTime, nullable=True)
    late_submission_allowed = Column(Boolean, default=False)
    late_penalty_percentage = Column(Numeric(5, 2), nullable=True)
    submission_type = Column(String(30), nullable=True)
    rubric_url = Column(Text, nullable=True)
    is_published = Column(Boolean, default=False)
    is_group_assignment = Column(Boolean, default=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    section = relationship("CourseSection", back_populates="assignments")
    submissions = relationship("AssignmentSubmission", back_populates="assignment", cascade="all, delete-orphan")
    teams = relationship("AssignmentTeam", back_populates="assignment", cascade="all, delete-orphan", lazy="selectin")


class Attendance(Base):
    __tablename__ = "attendance"

    attendance_id = Column(Integer, primary_key=True, autoincrement=True)
    section_id = Column(Integer, ForeignKey("course_sections.section_id", ondelete="CASCADE"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    class_date = Column(Date, nullable=False)
    attendance_status = Column(String(20), nullable=False)
    arrival_time = Column(Time, nullable=True)
    notes = Column(Text, nullable=True)
    recorded_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    section = relationship("CourseSection", back_populates="attendance_records")
    student = relationship("Student", back_populates="attendance_records")
    recorder = relationship("User", back_populates="attendance_records")


class StudentAccount(Base):
    __tablename__ = "student_accounts"

    account_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.student_id", ondelete="CASCADE"), unique=True, nullable=False)
    account_number = Column(String(20), unique=True, nullable=False)
    total_charges = Column(Numeric(12, 2), default=0.00)
    total_payments = Column(Numeric(12, 2), default=0.00)
    total_credits = Column(Numeric(12, 2), default=0.00)
    balance = Column(Numeric(12, 2), default=0.00)
    has_hold = Column(Boolean, default=False)
    hold_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    student = relationship("Student", back_populates="account")
    transactions = relationship("FinancialTransaction", back_populates="account", lazy="selectin", passive_deletes="all")


class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"

    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("student_accounts.account_id", ondelete="CASCADE"), nullable=False)
    term_id = Column(Integer, ForeignKey("academic_terms.term_id", ondelete="SET NULL"), nullable=True)
    transaction_type = Column(String(20), nullable=False)
    transaction_category = Column(String(50), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(Text, nullable=True)
    reference_number = Column(String(50), nullable=True)
    transaction_date = Column(DateTime, default=utcnow)
    posted_date = Column(Date, nullable=True)
    processed_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    payment_method = Column(String(50), nullable=True)
    check_number = Column(String(20), nullable=True)
    card_last_four = Column(String(4), nullable=True)
    is_reversed = Column(Boolean, default=False)
    reversal_transaction_id = Column(Integer, ForeignKey("financial_transactions.transaction_id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    account = relationship("StudentAccount", back_populates="transactions")
