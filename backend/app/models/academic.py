"""Academic structure SQLAlchemy models matching school_system_db_v2.sql."""

from datetime import datetime
from app.core.database import utcnow
from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Text, Date, ForeignKey, Numeric, Time
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base


class Department(Base):
    __tablename__ = "departments"

    department_id = Column(Integer, primary_key=True, autoincrement=True)
    department_code = Column(String(10), unique=True, nullable=False)
    department_name = Column(String(200), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    head_faculty_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    parent_department_id = Column(Integer, ForeignKey("departments.department_id", ondelete="SET NULL"), nullable=True)
    building = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website_url = Column(String(500), nullable=True)
    established_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    courses = relationship("Course", back_populates="department", lazy="selectin", passive_deletes="all")
    programs = relationship("Program", back_populates="department", lazy="selectin", passive_deletes="all")
    parent = relationship("Department", remote_side=[department_id], lazy="selectin")


class Program(Base):
    __tablename__ = "programs"

    program_id = Column(Integer, primary_key=True, autoincrement=True)
    program_code = Column(String(20), unique=True, nullable=False)
    program_name = Column(String(200), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.department_id", ondelete="CASCADE"), nullable=False)
    degree_level = Column(String(50), nullable=False)
    duration_years = Column(Numeric(3, 1), nullable=True)
    total_credits_required = Column(Integer, nullable=False)
    program_fee = Column(Numeric(10, 2), default=0.00) # Total Fee represents graduate price
    fee_per_year = Column(Numeric(10, 2), default=0.00)
    description = Column(Text, nullable=True)
    coordinator_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    accreditation_status = Column(String(50), nullable=True)
    accreditation_body = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    department = relationship("Department", back_populates="programs", lazy="selectin")
    students = relationship("Student", back_populates="program", lazy="selectin", passive_deletes="all")


class Course(Base):
    __tablename__ = "courses"

    course_id = Column(Integer, primary_key=True, autoincrement=True)
    course_code = Column(String(20), unique=True, nullable=False)
    course_name = Column(String(200), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.department_id", ondelete="CASCADE"), nullable=False)
    credits = Column(Integer, nullable=False)
    course_level = Column(String(20), nullable=True)
    lecture_hours = Column(Numeric(4, 2), default=0)
    lab_hours = Column(Numeric(4, 2), default=0)
    description = Column(Text, nullable=True)
    learning_outcomes = Column(Text, nullable=True)
    syllabus_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    department = relationship("Department", back_populates="courses")
    sections = relationship("CourseSection", back_populates="course", lazy="selectin", passive_deletes="all")
    reviews = relationship("Review", back_populates="course")


class AcademicTerm(Base):
    __tablename__ = "academic_terms"

    term_id = Column(Integer, primary_key=True, autoincrement=True)
    term_name = Column(String(100), nullable=False)
    term_code = Column(String(20), unique=True, nullable=False)
    academic_year = Column(String(9), nullable=False)
    term_type = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    registration_start_date = Column(Date, nullable=True)
    registration_end_date = Column(Date, nullable=True)
    add_drop_deadline = Column(Date, nullable=True)
    withdrawal_deadline = Column(Date, nullable=True)
    final_exam_start_date = Column(Date, nullable=True)
    final_exam_end_date = Column(Date, nullable=True)
    status = Column(String(20), default="upcoming")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    sections = relationship("CourseSection", back_populates="term", lazy="selectin", passive_deletes="all")
    reviews = relationship("Review", back_populates="term")


class Building(Base):
    __tablename__ = "buildings"

    building_id = Column(Integer, primary_key=True, autoincrement=True)
    building_code = Column(String(10), unique=True, nullable=False)
    building_name = Column(String(200), nullable=False)
    street_address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    total_floors = Column(Integer, nullable=True)
    year_built = Column(Integer, nullable=True)
    is_accessible = Column(Boolean, default=True)
    has_elevator = Column(Boolean, default=False)
    parking_available = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    rooms = relationship("Room", back_populates="building", lazy="selectin")


class Room(Base):
    __tablename__ = "rooms"

    room_id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(Integer, ForeignKey("buildings.building_id", ondelete="RESTRICT"), nullable=False)
    room_number = Column(String(20), nullable=False)
    room_name = Column(String(100), nullable=True)
    room_type = Column(String(50), nullable=False)
    floor_number = Column(Integer, nullable=True)
    capacity = Column(Integer, nullable=True)
    area_sqft = Column(Numeric(10, 2), nullable=True)
    features = Column(ARRAY(Text), nullable=True)
    equipment = Column(ARRAY(Text), nullable=True)
    is_accessible = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    building = relationship("Building", back_populates="rooms")
    sections = relationship("CourseSection", back_populates="room", lazy="selectin")


class CourseSection(Base):
    __tablename__ = "course_sections"

    section_id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    term_id = Column(Integer, ForeignKey("academic_terms.term_id", ondelete="CASCADE"), nullable=False)
    section_number = Column(String(10), nullable=False)
    instructor_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    max_capacity = Column(Integer, nullable=False)
    enrolled_count = Column(Integer, default=0)
    waiting_list_count = Column(Integer, default=0)
    room_id = Column(Integer, ForeignKey("rooms.room_id", ondelete="SET NULL"), nullable=True)
    schedule_pattern = Column(String(50), nullable=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    delivery_mode = Column(String(20), nullable=False)
    meeting_url = Column(Text, nullable=True)
    syllabus_url = Column(Text, nullable=True)
    join_code = Column(String(8), unique=True, nullable=True)
    status = Column(String(20), default="planned")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    course = relationship("Course", back_populates="sections")
    instructor = relationship("User", foreign_keys=[instructor_id], lazy="selectin")
    term = relationship("AcademicTerm", back_populates="sections")
    room = relationship("Room", back_populates="sections")
    enrollments = relationship("Enrollment", back_populates="section", lazy="selectin", passive_deletes="all")
    attendance_records = relationship("Attendance", back_populates="section", lazy="selectin", passive_deletes="all")
    assignments = relationship("Assignment", back_populates="section", lazy="selectin", passive_deletes="all")
