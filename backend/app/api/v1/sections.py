<<<<<<< HEAD
from uuid import UUID
import secrets, string
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.academic import CourseSection, Course, AcademicTerm, Room
from app.models.user import User
from app.schemas.academic import (
    CourseSectionOut, CourseSectionListOut, CourseSectionCreate, CourseSectionUpdate
)

router = APIRouter()

JOIN_CODE_UNAVAILABLE = "Class join codes are unavailable until the database migration for the join_code column is applied."


@router.get("/", response_model=CourseSectionListOut)
async def list_sections(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    course_id: int | None = Query(None),
    term_id: int | None = Query(None),
    instructor_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    delivery_mode: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(CourseSection).options(
        selectinload(CourseSection.course),
        selectinload(CourseSection.term),
        selectinload(CourseSection.room),
    )
    count_query = select(func.count(CourseSection.section_id))

    if course_id is not None:
        query = query.where(CourseSection.course_id == course_id)
        count_query = count_query.where(CourseSection.course_id == course_id)

    if term_id is not None:
        query = query.where(CourseSection.term_id == term_id)
        count_query = count_query.where(CourseSection.term_id == term_id)

    if instructor_id is not None:
        query = query.where(CourseSection.instructor_id == instructor_id)
        count_query = count_query.where(CourseSection.instructor_id == instructor_id)

    if status_filter:
        query = query.where(CourseSection.status == status_filter)
        count_query = count_query.where(CourseSection.status == status_filter)

    if delivery_mode:
        query = query.where(CourseSection.delivery_mode == delivery_mode)
        count_query = count_query.where(CourseSection.delivery_mode == delivery_mode)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(
        query.offset(skip).limit(limit).order_by(CourseSection.section_number)
    )
    sections = result.scalars().all()
    return CourseSectionListOut(sections=sections, total=total)


@router.get("/{section_id}", response_model=CourseSectionOut)
async def get_section(section_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CourseSection)
        .options(
            selectinload(CourseSection.course),
            selectinload(CourseSection.term),
            selectinload(CourseSection.room)
        )
        .where(CourseSection.section_id == section_id)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course section not found")
    return section


=======
from uuid import UUID
import secrets, string
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.academic import CourseSection, Course, AcademicTerm, Room
from app.models.user import User
from app.schemas.academic import (
    CourseSectionOut, CourseSectionListOut, CourseSectionCreate, CourseSectionUpdate
)

router = APIRouter()


@router.get("/", response_model=CourseSectionListOut)
async def list_sections(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    course_id: int | None = Query(None),
    term_id: int | None = Query(None),
    instructor_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    delivery_mode: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(CourseSection).options(
        selectinload(CourseSection.course),
        selectinload(CourseSection.term),
        selectinload(CourseSection.room),
    )
    count_query = select(func.count(CourseSection.section_id))

    if course_id is not None:
        query = query.where(CourseSection.course_id == course_id)
        count_query = count_query.where(CourseSection.course_id == course_id)

    if term_id is not None:
        query = query.where(CourseSection.term_id == term_id)
        count_query = count_query.where(CourseSection.term_id == term_id)

    if instructor_id is not None:
        query = query.where(CourseSection.instructor_id == instructor_id)
        count_query = count_query.where(CourseSection.instructor_id == instructor_id)

    if status_filter:
        query = query.where(CourseSection.status == status_filter)
        count_query = count_query.where(CourseSection.status == status_filter)

    if delivery_mode:
        query = query.where(CourseSection.delivery_mode == delivery_mode)
        count_query = count_query.where(CourseSection.delivery_mode == delivery_mode)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(
        query.offset(skip).limit(limit).order_by(CourseSection.section_number)
    )
    sections = result.scalars().all()
    return CourseSectionListOut(sections=sections, total=total)


@router.get("/{section_id}", response_model=CourseSectionOut)
async def get_section(section_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CourseSection)
        .options(
            selectinload(CourseSection.course),
            selectinload(CourseSection.term),
            selectinload(CourseSection.room)
        )
        .where(CourseSection.section_id == section_id)
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course section not found")
    return section


>>>>>>> a1077c5da31aaef6385c7850c5580088169ce36c
@router.post("/", response_model=CourseSectionOut, status_code=status.HTTP_201_CREATED)
async def create_section(data: CourseSectionCreate, db: AsyncSession = Depends(get_db)):
    # Check if course exists
    course_result = await db.execute(select(Course).where(Course.course_id == data.course_id))
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    # Check if term exists
    term_result = await db.execute(select(AcademicTerm).where(AcademicTerm.term_id == data.term_id))
    term = term_result.scalar_one_or_none()
    if not term:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic term not found")

    # Check for existing section number for this course and term
    existing = await db.execute(
        select(CourseSection).where(
            CourseSection.course_id == data.course_id,
            CourseSection.term_id == data.term_id,
            CourseSection.section_number == data.section_number,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Section number already exists for this course in this term"
        )

    # Verify instructor exists if provided
    if data.instructor_id:
        instructor_result = await db.execute(select(User).where(User.user_id == data.instructor_id))
        if not instructor_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instructor not found")

    # Verify room exists if provided
    if data.room_id:
        room_result = await db.execute(select(Room).where(Room.room_id == data.room_id))
        if not room_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    section_data = data.model_dump()
    if section_data.get("section_number"):
        section_data["section_number"] = section_data["section_number"].strip()
    # Normalize delivery_mode to lowercase to match DB check constraint
    if section_data.get('delivery_mode'):
        section_data['delivery_mode'] = section_data['delivery_mode'].lower()
<<<<<<< HEAD
    section_data.pop("join_code", None)
    section = CourseSection(**section_data)
    db.add(section)
    await db.flush()

    # Re-query with eager loading so response_model can serialize relationships
=======
    # Auto-generate join_code if not provided
    if not section_data.get('join_code'):
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            existing_code = await db.execute(select(CourseSection).where(CourseSection.join_code == code))
            if not existing_code.scalar_one_or_none():
                section_data['join_code'] = code
                break
    section = CourseSection(**section_data)
    db.add(section)
    await db.flush()

    # Re-query with eager loading so response_model can serialize relationships
>>>>>>> a1077c5da31aaef6385c7850c5580088169ce36c
    result = await db.execute(
        select(CourseSection)
        .options(
            selectinload(CourseSection.course),
            selectinload(CourseSection.term),
            selectinload(CourseSection.room),
        )
        .where(CourseSection.section_id == section.section_id)
    )
    return result.scalar_one()


@router.put("/{section_id}", response_model=CourseSectionOut)
async def update_section(section_id: int, data: CourseSectionUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing course section."""
    result = await db.execute(select(CourseSection).where(CourseSection.section_id == section_id))
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course section not found")

    update_data = data.model_dump(exclude_unset=True)
    if "section_number" in update_data and update_data["section_number"]:
        update_data["section_number"] = update_data["section_number"].strip()

    # Verify referenced records for any FK updates
    if "course_id" in update_data:
        course_result = await db.execute(select(Course).where(Course.course_id == update_data["course_id"]))
        if not course_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    if "term_id" in update_data:
        term_result = await db.execute(select(AcademicTerm).where(AcademicTerm.term_id == update_data["term_id"]))
        if not term_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic term not found")

    if update_data.get("instructor_id"):
        instructor_result = await db.execute(select(User).where(User.user_id == update_data["instructor_id"]))
        if not instructor_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instructor not found")

    if "room_id" in update_data and update_data["room_id"] is not None:
        room_result = await db.execute(select(Room).where(Room.room_id == update_data["room_id"]))
        if not room_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    # Check for conflicts if updating section number, course, or term
    if any(k in update_data for k in ["section_number", "course_id", "term_id"]):
        course_id = update_data.get("course_id", section.course_id)
        term_id = update_data.get("term_id", section.term_id)
        section_num = update_data.get("section_number", section.section_number)
        
        existing = await db.execute(
            select(CourseSection).where(
                CourseSection.section_id != section_id,
                CourseSection.course_id == course_id,
                CourseSection.term_id == term_id,
                CourseSection.section_number == section_num,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Section number already exists for this course in this term"
            )

    for key, value in update_data.items():
        # Normalize delivery_mode to lowercase to match DB check constraint
        if key == 'delivery_mode' and value:
            value = value.lower()
        setattr(section, key, value)

    await db.flush()

    # Re-query with eager loading so response_model can serialize relationships
    result = await db.execute(
        select(CourseSection)
        .options(
            selectinload(CourseSection.course),
            selectinload(CourseSection.term),
            selectinload(CourseSection.room),
        )
        .where(CourseSection.section_id == section_id)
    )
    return result.scalar_one()
<<<<<<< HEAD


@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_section(section_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a course section."""
    result = await db.execute(select(CourseSection).where(CourseSection.section_id == section_id))
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course section not found")

    await db.delete(section)
    await db.flush()
    return None


@router.get("/{section_id}/enrollments")
async def get_section_enrollments(
    section_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get all enrollments for a course section."""
    from app.models.people import Enrollment, Student
    from app.models.user import User
    from app.schemas.people import EnrollmentListOut, EnrollmentOut
    from sqlalchemy.orm import selectinload

    result = await db.execute(select(CourseSection).where(CourseSection.section_id == section_id))
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course section not found")

    count_query = select(func.count(Enrollment.enrollment_id)).where(Enrollment.section_id == section_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = (
        select(Enrollment)
        .join(Student, Enrollment.student_id == Student.student_id)
        .join(User, Student.student_id == User.user_id)
        .options(
            selectinload(Enrollment.student).selectinload(Student.user),
            selectinload(Enrollment.section).selectinload(CourseSection.course),
            selectinload(Enrollment.section).selectinload(CourseSection.term),
            selectinload(Enrollment.section).selectinload(CourseSection.room),
        )
        .where(Enrollment.section_id == section_id)
    )

    if search:
        search_term = f"%{search}%"
        query = query.where(
            (User.first_name.ilike(search_term)) |
            (User.last_name.ilike(search_term)) |
            (User.email.ilike(search_term)) |
            (Student.student_number.ilike(search_term))
        )
        
        # Update total count for filtered results
        count_query = (
            select(func.count(Enrollment.enrollment_id))
            .join(Student, Enrollment.student_id == Student.student_id)
            .join(User, Student.student_id == User.user_id)
            .where(Enrollment.section_id == section_id)
            .where(
                (User.first_name.ilike(search_term)) |
                (User.last_name.ilike(search_term)) |
                (User.email.ilike(search_term)) |
                (Student.student_number.ilike(search_term))
            )
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar()

    query = query.offset(skip).limit(limit)
    enrollments_result = await db.execute(query)
    enrollments = enrollments_result.scalars().all()

    return EnrollmentListOut(enrollments=enrollments, total=total)


@router.get("/{section_id}/assignments")
async def get_section_assignments(
    section_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get all assignments for a course section."""
    from app.models.people import Assignment
    from app.schemas.people import AssignmentListOut, AssignmentOut

    result = await db.execute(select(CourseSection).where(CourseSection.section_id == section_id))
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course section not found")

    count_query = select(func.count(Assignment.assignment_id)).where(Assignment.section_id == section_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = select(Assignment).where(Assignment.section_id == section_id).offset(skip).limit(limit)
    assignments_result = await db.execute(query)
    assignments = assignments_result.scalars().all()

    return AssignmentListOut(assignments=assignments, total=total)


@router.post("/{section_id}/enroll", status_code=status.HTTP_201_CREATED)
async def enroll_student_manually(
    section_id: int,
    student_id: UUID = Query(..., description="UUID of the student to enroll"),
    db: AsyncSession = Depends(get_db),
):
    """Manually enroll a student in a course section."""
    from app.models.people import Enrollment, Student
    
    # Verify section exists
    section_result = await db.execute(select(CourseSection).where(CourseSection.section_id == section_id))
    section = section_result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course section not found")

    # Verify student exists
    student_result = await db.execute(select(Student).where(Student.student_id == student_id))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    # Check if already enrolled
    existing = await db.execute(
        select(Enrollment).where(
            Enrollment.section_id == section_id,
            Enrollment.student_id == student_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student is already enrolled in this section")

    # Enroll
    enrollment = Enrollment(
        section_id=section_id,
        student_id=student_id,
        enrollment_status="enrolled",
        enrollment_date=datetime.utcnow().date()
    )
    db.add(enrollment)
    
    # Update enrolled count
    section.enrolled_count += 1
    
    await db.commit()
    return {"message": "Student enrolled successfully", "enrollment_id": enrollment.enrollment_id}


@router.post("/join", status_code=status.HTTP_201_CREATED)
async def join_section_by_code(
    join_code: str = Body(..., embed=True, description="6-character class join code"),
    student_id: UUID = Body(..., embed=True, description="UUID of the student"),
    db: AsyncSession = Depends(get_db),
):
    """Allow a student to join a course section using the class join code."""
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=JOIN_CODE_UNAVAILABLE)
=======


@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_section(section_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a course section."""
    result = await db.execute(select(CourseSection).where(CourseSection.section_id == section_id))
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course section not found")

    await db.delete(section)
    await db.flush()
    return None


@router.get("/{section_id}/enrollments")
async def get_section_enrollments(
    section_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get all enrollments for a course section."""
    from app.models.people import Enrollment, Student
    from app.models.user import User
    from app.schemas.people import EnrollmentListOut, EnrollmentOut
    from sqlalchemy.orm import selectinload

    result = await db.execute(select(CourseSection).where(CourseSection.section_id == section_id))
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course section not found")

    count_query = select(func.count(Enrollment.enrollment_id)).where(Enrollment.section_id == section_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = (
        select(Enrollment)
        .join(Student, Enrollment.student_id == Student.student_id)
        .join(User, Student.student_id == User.user_id)
        .options(
            selectinload(Enrollment.student).selectinload(Student.user),
            selectinload(Enrollment.section).selectinload(CourseSection.course),
            selectinload(Enrollment.section).selectinload(CourseSection.term),
            selectinload(Enrollment.section).selectinload(CourseSection.room),
        )
        .where(Enrollment.section_id == section_id)
    )

    if search:
        search_term = f"%{search}%"
        query = query.where(
            (User.first_name.ilike(search_term)) |
            (User.last_name.ilike(search_term)) |
            (User.email.ilike(search_term)) |
            (Student.student_number.ilike(search_term))
        )
        
        # Update total count for filtered results
        count_query = (
            select(func.count(Enrollment.enrollment_id))
            .join(Student, Enrollment.student_id == Student.student_id)
            .join(User, Student.student_id == User.user_id)
            .where(Enrollment.section_id == section_id)
            .where(
                (User.first_name.ilike(search_term)) |
                (User.last_name.ilike(search_term)) |
                (User.email.ilike(search_term)) |
                (Student.student_number.ilike(search_term))
            )
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar()

    query = query.offset(skip).limit(limit)
    enrollments_result = await db.execute(query)
    enrollments = enrollments_result.scalars().all()

    return EnrollmentListOut(enrollments=enrollments, total=total)


@router.get("/{section_id}/assignments")
async def get_section_assignments(
    section_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get all assignments for a course section."""
    from app.models.people import Assignment
    from app.schemas.people import AssignmentListOut, AssignmentOut

    result = await db.execute(select(CourseSection).where(CourseSection.section_id == section_id))
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course section not found")

    count_query = select(func.count(Assignment.assignment_id)).where(Assignment.section_id == section_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = select(Assignment).where(Assignment.section_id == section_id).offset(skip).limit(limit)
    assignments_result = await db.execute(query)
    assignments = assignments_result.scalars().all()

    return AssignmentListOut(assignments=assignments, total=total)


@router.post("/{section_id}/enroll", status_code=status.HTTP_201_CREATED)
async def enroll_student_manually(
    section_id: int,
    student_id: UUID = Query(..., description="UUID of the student to enroll"),
    db: AsyncSession = Depends(get_db),
):
    """Manually enroll a student in a course section."""
    from app.models.people import Enrollment, Student
    
    # Verify section exists
    section_result = await db.execute(select(CourseSection).where(CourseSection.section_id == section_id))
    section = section_result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course section not found")

    # Verify student exists
    student_result = await db.execute(select(Student).where(Student.student_id == student_id))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    # Check if already enrolled
    existing = await db.execute(
        select(Enrollment).where(
            Enrollment.section_id == section_id,
            Enrollment.student_id == student_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student is already enrolled in this section")

    # Enroll
    enrollment = Enrollment(
        section_id=section_id,
        student_id=student_id,
        enrollment_status="enrolled",
        enrollment_date=datetime.utcnow().date()
    )
    db.add(enrollment)
    
    # Update enrolled count
    section.enrolled_count += 1
    
    await db.commit()
    return {"message": "Student enrolled successfully", "enrollment_id": enrollment.enrollment_id}


@router.post("/join", status_code=status.HTTP_201_CREATED)
async def join_section_by_code(
    join_code: str = Body(..., embed=True, description="6-character class join code"),
    student_id: UUID = Body(..., embed=True, description="UUID of the student"),
    db: AsyncSession = Depends(get_db),
):
    """Allow a student to join a course section using the class join code."""
    from app.models.people import Enrollment, Student

    # Find section by join code
    section_result = await db.execute(
        select(CourseSection)
        .options(selectinload(CourseSection.course))
        .where(CourseSection.join_code == join_code.strip().upper())
    )
    section = section_result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid class code. No section found.")

    # Verify student exists
    student_result = await db.execute(select(Student).where(Student.student_id == student_id))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    # Check capacity
    if section.enrolled_count >= section.max_capacity:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This class is full.")

    # Check if already enrolled
    existing = await db.execute(
        select(Enrollment).where(
            Enrollment.section_id == section.section_id,
            Enrollment.student_id == student_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You are already enrolled in this class.")

    # Enroll
    enrollment = Enrollment(
        section_id=section.section_id,
        student_id=student_id,
        enrollment_status="enrolled",
        enrollment_date=datetime.utcnow().date()
    )
    db.add(enrollment)
    section.enrolled_count += 1
    await db.commit()

    return {
        "message": "Successfully joined the class!",
        "enrollment_id": enrollment.enrollment_id,
        "course_name": section.course.course_name if section.course else None,
        "section_number": section.section_number
    }
>>>>>>> a1077c5da31aaef6385c7850c5580088169ce36c
