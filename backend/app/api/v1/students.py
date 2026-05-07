"""Student management endpoints with full CRUD operations."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.people import Student, Enrollment, Assignment, AssignmentSubmission
from app.models.user import User
from app.models.academic import Program, CourseSection, Course
from app.schemas.people import (
    StudentOut, StudentListOut, StudentCreate, StudentUpdate
)
from app.api.deps import get_current_user

router = APIRouter()


# ──────────────────────────────────────────────
# /me  endpoints  (MUST come BEFORE /{student_id})
# ──────────────────────────────────────────────

@router.get("/me")
async def get_my_student_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the student profile for the currently authenticated user."""
    result = await db.execute(
        select(Student)
        .options(
            selectinload(Student.user),
            selectinload(Student.program),
            selectinload(Student.account),
        )
        .where(Student.student_id == current_user.user_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="No student profile linked to this user")
    return student


@router.get("/me/enrollments")
async def get_my_enrollments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get enrollments for the currently authenticated student."""
    result = await db.execute(
        select(Student).where(Student.student_id == current_user.user_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="No student profile linked to this user")

    query = (
        select(Enrollment)
        .options(
            selectinload(Enrollment.section)
            .selectinload(CourseSection.course),
            selectinload(Enrollment.section)
            .selectinload(CourseSection.term),
            selectinload(Enrollment.section)
            .selectinload(CourseSection.room),
        )
        .where(Enrollment.student_id == current_user.user_id)
    )
    enrollments_result = await db.execute(query)
    enrollments = enrollments_result.scalars().all()
    return {"enrollments": enrollments, "total": len(enrollments)}


@router.get("/me/assignments")
async def get_my_assignments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all assignments for courses the authenticated student is enrolled in,
    including course info and instructor details."""
    # Get enrolled section IDs
    enr_result = await db.execute(
        select(Enrollment.section_id)
        .where(Enrollment.student_id == current_user.user_id)
        .where(Enrollment.enrollment_status.in_(["enrolled", "completed"]))
    )
    section_ids = [row[0] for row in enr_result.all()]

    if not section_ids:
        return {"assignments": []}

    # Get assignments for those sections with full course + instructor
    asn_result = await db.execute(
        select(Assignment)
        .options(
            selectinload(Assignment.section)
            .selectinload(CourseSection.course),
            selectinload(Assignment.submissions),
        )
        .where(Assignment.section_id.in_(section_ids))
        .where(Assignment.is_published == True)
        .order_by(Assignment.due_date.asc().nullslast())
    )
    assignments = asn_result.scalars().all()

    # Get instructor info for each section
    instructor_ids = list(set(
        a.section.instructor_id for a in assignments
        if a.section and a.section.instructor_id
    ))
    instructors = {}
    if instructor_ids:
        instr_result = await db.execute(
            select(User)
            .options(selectinload(User.personal_info))
            .where(User.user_id.in_(instructor_ids))
        )
        for u in instr_result.scalars().all():
            name_parts = []
            if u.personal_info:
                name_parts = [u.personal_info.first_name or "", u.personal_info.last_name or ""]
            instructors[str(u.user_id)] = " ".join(name_parts).strip() or u.username

    # Build response
    out = []
    for a in assignments:
        section = a.section
        course = section.course if section else None
        instructor_name = instructors.get(str(section.instructor_id), "TBA") if section else "TBA"

        # Check if this student has submissions
        student_submissions = [
            s for s in (a.submissions or [])
            if str(s.student_id) == str(current_user.user_id)
        ]

        out.append({
            "assignment_id": a.assignment_id,
            "assignment_name": a.assignment_name,
            "assignment_type": a.assignment_type,
            "description": a.description,
            "max_points": float(a.max_points) if a.max_points else 0,
            "weight_percentage": float(a.weight_percentage) if a.weight_percentage else 0,
            "due_date": a.due_date.isoformat() if a.due_date else None,
            "is_group_assignment": a.is_group_assignment,
            "section_id": a.section_id,
            "course_code": course.course_code if course else "N/A",
            "course_name": course.course_name if course else "N/A",
            "instructor_name": instructor_name,
            "submitted": len(student_submissions) > 0,
            "submission_status": student_submissions[0].submission_status if student_submissions else None,
            "points_earned": float(student_submissions[0].points_earned) if student_submissions and student_submissions[0].points_earned else None,
        })

    return {"assignments": out}


@router.get("/", response_model=StudentListOut)
async def list_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    program_id: int | None = Query(None),
    enrollment_status: str | None = Query(None),
    academic_standing: str | None = Query(None),
    search: str | None = Query(None),
    search_name: str | None = Query(None, description="Search by first or last name"),
    search_username: str | None = Query(None, description="Search by username"),
    search_student_number: str | None = Query(None, description="Search by student number"),
    db: AsyncSession = Depends(get_db),
):
    """List students with optional filters and pagination."""
    query = select(Student).options(
        selectinload(Student.user),
        selectinload(Student.program),
        selectinload(Student.account)
    )
    count_query = select(func.count(Student.student_id))

    if program_id is not None:
        query = query.where(Student.program_id == program_id)
        count_query = count_query.where(Student.program_id == program_id)

    if enrollment_status:
        query = query.where(Student.enrollment_status == enrollment_status)
        count_query = count_query.where(Student.enrollment_status == enrollment_status)

    if academic_standing:
        query = query.where(Student.academic_standing == academic_standing)
        count_query = count_query.where(Student.academic_standing == academic_standing)

    if search:
        search_term = f"%{search}%"
        from app.models.user import UserPersonalInfo
        # Join with user table and personal info for search by name, username, email, student number
        query = query.join(User).outerjoin(UserPersonalInfo, User.user_id == UserPersonalInfo.user_id).where(
            User.username.ilike(search_term) |
            User.email.ilike(search_term) |
            Student.student_number.ilike(search_term) |
            UserPersonalInfo.first_name.ilike(search_term) |
            UserPersonalInfo.last_name.ilike(search_term)
        )
        count_query = count_query.join(User).outerjoin(UserPersonalInfo, User.user_id == UserPersonalInfo.user_id).where(
            User.username.ilike(search_term) |
            User.email.ilike(search_term) |
            Student.student_number.ilike(search_term) |
            UserPersonalInfo.first_name.ilike(search_term) |
            UserPersonalInfo.last_name.ilike(search_term)
        )
    elif search_name or search_username or search_student_number:
        from app.models.user import UserPersonalInfo
        query = query.join(User).outerjoin(UserPersonalInfo, User.user_id == UserPersonalInfo.user_id)
        count_query = count_query.join(User).outerjoin(UserPersonalInfo, User.user_id == UserPersonalInfo.user_id)
        
        conditions = []
        if search_name:
            name_term = f"%{search_name}%"
            conditions.append(
                UserPersonalInfo.first_name.ilike(name_term) |
                UserPersonalInfo.last_name.ilike(name_term)
            )
        if search_username:
            conditions.append(User.username.ilike(f"%{search_username}%"))
        if search_student_number:
            conditions.append(Student.student_number.ilike(f"%{search_student_number}%"))
        
        if conditions:
            from sqlalchemy import or_
            final_condition = conditions[0]
            for condition in conditions[1:]:
                final_condition = final_condition | condition
            query = query.where(final_condition)
            count_query = count_query.where(final_condition)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(
        query.offset(skip).limit(limit).order_by(Student.created_at.desc())
    )
    students = result.scalars().all()
    return StudentListOut(students=students, total=total)


@router.get("/{student_id}", response_model=StudentOut)
async def get_student(student_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single student by ID."""
    result = await db.execute(
        select(Student)
        .options(selectinload(Student.user), selectinload(Student.program), selectinload(Student.account))
        .where(Student.student_id == student_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


@router.post("/", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
async def create_student(data: StudentCreate, db: AsyncSession = Depends(get_db)):
    """Create a new student profile for an existing user."""
    # Check if user exists
    user_result = await db.execute(select(User).where(User.user_id == data.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check if student already exists for this user
    existing_student = await db.execute(
        select(Student).where(Student.student_id == data.user_id)
    )
    if existing_student.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student profile already exists for this user"
        )

    # Check for duplicate student number
    existing_number = await db.execute(
        select(Student).where(Student.student_number == data.student_number)
    )
    if existing_number.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student number already exists"
        )

    # Verify program exists
    program_result = await db.execute(
        select(Program).where(Program.program_id == data.program_id)
    )
    if not program_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Program not found"
        )

    student = Student(
        student_id=data.user_id,
        **data.model_dump(exclude={"user_id"})
    )
    db.add(student)
    await db.flush()
    await db.refresh(student)
    return student


@router.put("/{student_id}", response_model=StudentOut)
async def update_student(student_id: UUID, data: StudentUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing student."""
    result = await db.execute(select(Student).where(Student.student_id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    update_data = data.model_dump(exclude_unset=True)

    # Check for duplicate student number if updating
    if "student_number" in update_data:
        existing = await db.execute(
            select(Student).where(
                Student.student_id != student_id,
                Student.student_number == update_data["student_number"]
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Student number already exists"
            )

    # Verify program exists if updating
    if "program_id" in update_data:
        program_result = await db.execute(
            select(Program).where(Program.program_id == update_data["program_id"])
        )
        if not program_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Program not found"
            )

    for key, value in update_data.items():
        setattr(student, key, value)

    await db.flush()
    await db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(student_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a student profile."""
    result = await db.execute(select(Student).where(Student.student_id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    await db.delete(student)
    await db.flush()
    return None


@router.get("/{student_id}/enrollments")
async def get_student_enrollments(
    student_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get all enrollments for a student."""
    from app.models.people import Enrollment
    from app.schemas.people import EnrollmentListOut, EnrollmentOut

    result = await db.execute(select(Student).where(Student.student_id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    count_query = select(func.count(Enrollment.enrollment_id)).where(Enrollment.student_id == student_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = select(Enrollment).where(Enrollment.student_id == student_id).offset(skip).limit(limit)
    enrollments_result = await db.execute(query)
    enrollments = enrollments_result.scalars().all()

    return EnrollmentListOut(enrollments=enrollments, total=total)


@router.get("/{student_id}/account")
async def get_student_account(student_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get the financial account for a student."""
    from app.models.people import StudentAccount
    from app.schemas.people import StudentAccountOut

    result = await db.execute(select(Student).where(Student.student_id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    account_result = await db.execute(
        select(StudentAccount).where(StudentAccount.student_id == student_id)
    )
    account = account_result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student account not found")

    return StudentAccountOut.model_validate(account)
