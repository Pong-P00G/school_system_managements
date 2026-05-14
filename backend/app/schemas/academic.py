"""Pydantic schemas for academic-related endpoints."""

from datetime import datetime, date, time
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID


# --- Department schemas ---
class DepartmentBase(BaseModel):
    department_code: str = Field(..., max_length=10)
    department_name: str = Field(..., max_length=200)
    description: str | None = None
    head_faculty_id: UUID | None = None
    parent_department_id: int | None = None
    building: str | None = None
    phone: str | None = None
    email: str | None = None
    website_url: str | None = None
    established_date: date | None = None
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    department_code: str | None = None
    department_name: str | None = None
    description: str | None = None
    head_faculty_id: UUID | None = None
    parent_department_id: int | None = None
    building: str | None = None
    phone: str | None = None
    email: str | None = None
    website_url: str | None = None
    established_date: date | None = None
    is_active: bool | None = None


class DepartmentOut(BaseModel):
    department_id: int
    department_code: str
    department_name: str
    description: str | None = None
    head_faculty_id: UUID | None = None
    parent_department_id: int | None = None
    building: str | None = None
    phone: str | None = None
    email: str | None = None
    website_url: str | None = None
    established_date: date | None = None
    is_active: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class DepartmentListOut(BaseModel):
    departments: list[DepartmentOut]
    total: int


# --- Program schemas ---
class ProgramBase(BaseModel):
    program_code: str = Field(..., max_length=20)
    program_name: str = Field(..., max_length=200)
    department_id: int
    degree_level: str = Field(..., max_length=50)
    duration_years: Decimal | None = None
    total_credits_required: int
    program_fee: Decimal = Field(default=Decimal("0.00"))
    fee_per_year: Decimal = Field(default=Decimal("0.00"))
    description: str | None = None
    coordinator_id: UUID | None = None
    accreditation_status: str | None = None
    accreditation_body: str | None = None
    is_active: bool = True


class ProgramCreate(ProgramBase):
    pass


class ProgramUpdate(BaseModel):
    program_code: str | None = None
    program_name: str | None = None
    department_id: int | None = None
    degree_level: str | None = None
    duration_years: Decimal | None = None
    total_credits_required: int | None = None
    program_fee: Decimal | None = None
    fee_per_year: Decimal | None = None
    description: str | None = None
    coordinator_id: UUID | None = None
    accreditation_status: str | None = None
    accreditation_body: str | None = None
    is_active: bool | None = None


class ProgramOut(BaseModel):
    program_id: int
    program_code: str
    program_name: str
    department_id: int
    degree_level: str
    duration_years: Decimal | None = None
    total_credits_required: int
    program_fee: Decimal = Field(default=Decimal("0.00"))
    fee_per_year: Decimal = Field(default=Decimal("0.00"))
    description: str | None = None
    coordinator_id: UUID | None = None
    accreditation_status: str | None = None
    accreditation_body: str | None = None
    is_active: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ProgramListOut(BaseModel):
    programs: list[ProgramOut]
    total: int


# --- Course schemas ---
class CourseBase(BaseModel):
    course_code: str = Field(..., max_length=20)
    course_name: str = Field(..., max_length=200)
    department_id: int
    credits: int = Field(default=3)
    course_level: str | None = None
    lecture_hours: Decimal = Field(default=Decimal("0.00"))
    lab_hours: Decimal = Field(default=Decimal("0.00"))
    description: str | None = None
    learning_outcomes: str | None = None
    syllabus_url: str | None = None
    is_active: bool = True


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    course_code: str | None = None
    course_name: str | None = None
    department_id: int | None = None
    credits: int | None = None
    course_level: str | None = None
    lecture_hours: Decimal | None = None
    lab_hours: Decimal | None = None
    description: str | None = None
    learning_outcomes: str | None = None
    syllabus_url: str | None = None
    is_active: bool | None = None


class CourseOut(BaseModel):
    course_id: int
    course_code: str
    course_name: str
    department_id: int
    credits: int
    course_level: str | None = None
    lecture_hours: Decimal | None = None
    lab_hours: Decimal | None = None
    description: str | None = None
    learning_outcomes: str | None = None
    syllabus_url: str | None = None
    is_active: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class CourseListOut(BaseModel):
    courses: list[CourseOut]
    total: int


# --- Academic Term schemas ---
class AcademicTermBase(BaseModel):
    term_name: str = Field(..., max_length=100)
    term_code: str = Field(..., max_length=20)
    academic_year: str = Field(..., max_length=9)
    term_type: str = Field(..., max_length=20)
    start_date: date
    end_date: date
    registration_start_date: date | None = None
    registration_end_date: date | None = None
    add_drop_deadline: date | None = None
    withdrawal_deadline: date | None = None
    final_exam_start_date: date | None = None
    final_exam_end_date: date | None = None
    status: str = "upcoming"


class AcademicTermCreate(AcademicTermBase):
    pass


class AcademicTermUpdate(BaseModel):
    term_name: str | None = None
    term_code: str | None = None
    academic_year: str | None = None
    term_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    registration_start_date: date | None = None
    registration_end_date: date | None = None
    add_drop_deadline: date | None = None
    withdrawal_deadline: date | None = None
    final_exam_start_date: date | None = None
    final_exam_end_date: date | None = None
    status: str | None = None


class AcademicTermOut(BaseModel):
    term_id: int
    term_name: str
    term_code: str
    academic_year: str
    term_type: str
    start_date: date
    end_date: date
    registration_start_date: date | None = None
    registration_end_date: date | None = None
    add_drop_deadline: date | None = None
    withdrawal_deadline: date | None = None
    final_exam_start_date: date | None = None
    final_exam_end_date: date | None = None
    status: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class AcademicTermListOut(BaseModel):
    terms: list[AcademicTermOut]
    total: int


# --- Building schemas ---
class BuildingBase(BaseModel):
    building_code: str = Field(..., max_length=10)
    building_name: str = Field(..., max_length=200)
    street_address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    total_floors: int | None = None
    year_built: int | None = None
    is_accessible: bool = True
    has_elevator: bool = False
    parking_available: bool = False
    is_active: bool = True


class BuildingCreate(BuildingBase):
    pass


class BuildingUpdate(BaseModel):
    building_code: str | None = None
    building_name: str | None = None
    street_address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    total_floors: int | None = None
    year_built: int | None = None
    is_accessible: bool | None = None
    has_elevator: bool | None = None
    parking_available: bool | None = None
    is_active: bool | None = None


class BuildingOut(BaseModel):
    building_id: int
    building_code: str
    building_name: str
    street_address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    total_floors: int | None = None
    year_built: int | None = None
    is_accessible: bool
    has_elevator: bool
    parking_available: bool
    is_active: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class BuildingListOut(BaseModel):
    buildings: list[BuildingOut]
    total: int


# --- Room schemas ---
class RoomBase(BaseModel):
    building_id: int
    room_number: str = Field(..., max_length=20)
    room_name: str | None = None
    room_type: str = Field(..., max_length=50)
    floor_number: int | None = None
    capacity: int | None = None
    area_sqft: Decimal | None = None
    features: list[str] | None = None
    equipment: list[str] | None = None
    is_accessible: bool = True
    is_active: bool = True


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    building_id: int | None = None
    room_number: str | None = None
    room_name: str | None = None
    room_type: str | None = None
    floor_number: int | None = None
    capacity: int | None = None
    area_sqft: Decimal | None = None
    features: list[str] | None = None
    equipment: list[str] | None = None
    is_accessible: bool | None = None
    is_active: bool | None = None


class RoomOut(BaseModel):
    room_id: int
    building_id: int
    room_number: str
    room_name: str | None = None
    room_type: str
    floor_number: int | None = None
    capacity: int | None = None
    area_sqft: Decimal | None = None
    features: list[str] | None = None
    equipment: list[str] | None = None
    is_accessible: bool
    is_active: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class RoomListOut(BaseModel):
    rooms: list[RoomOut]
    total: int


# --- Course Section schemas ---
class CourseSectionBase(BaseModel):
    course_id: int
    term_id: int
    section_number: str = Field(..., max_length=10)
    instructor_id: UUID | None = None
    max_capacity: int
    room_id: int | None = None
    schedule_pattern: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    start_date: date | None = None
    end_date: date | None = None
    delivery_mode: str
    meeting_url: str | None = None
    syllabus_url: str | None = None
    join_code: str | None = None
    status: str = "planned"


class CourseSectionCreate(CourseSectionBase):
    pass


class CourseSectionUpdate(BaseModel):
    course_id: int | None = None
    term_id: int | None = None
    section_number: str | None = None
    instructor_id: UUID | None = None
    max_capacity: int | None = None
    enrolled_count: int | None = None
    waiting_list_count: int | None = None
    room_id: int | None = None
    schedule_pattern: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    start_date: date | None = None
    end_date: date | None = None
    delivery_mode: str | None = None
    meeting_url: str | None = None
    syllabus_url: str | None = None
    join_code: str | None = None
    status: str | None = None


class CourseSectionOut(BaseModel):
    section_id: int
    course_id: int
    term_id: int
    section_number: str
    instructor_id: UUID | None = None
    max_capacity: int
    enrolled_count: int = 0
    waiting_list_count: int = 0
    room_id: int | None = None
    schedule_pattern: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    start_date: date | None = None
    end_date: date | None = None
    delivery_mode: str
    meeting_url: str | None = None
    syllabus_url: str | None = None
    join_code: str | None = None
    status: str
    course: CourseOut | None = None
    term: AcademicTermOut | None = None
    room: RoomOut | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class CourseSectionListOut(BaseModel):
    sections: list[CourseSectionOut]
    total: int
