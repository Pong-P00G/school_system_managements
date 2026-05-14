<<<<<<< HEAD
"""Program management endpoints with full CRUD operations."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.academic import Program, Department
from app.schemas.academic import (
    ProgramOut, ProgramListOut, ProgramCreate, ProgramUpdate
)

router = APIRouter()


@router.get("/", response_model=ProgramListOut)
async def list_programs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    department_id: int | None = Query(None),
    degree_level: str | None = Query(None),
    search: str | None = Query(None),
    is_active: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List programs with optional filters and pagination."""
    query = select(Program)
    count_query = select(func.count(Program.program_id))

    if department_id is not None:
        query = query.where(Program.department_id == department_id)
        count_query = count_query.where(Program.department_id == department_id)

    if degree_level:
        query = query.where(Program.degree_level == degree_level)
        count_query = count_query.where(Program.degree_level == degree_level)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            Program.program_name.ilike(search_term) |
            Program.program_code.ilike(search_term)
        )
        count_query = count_query.where(
            Program.program_name.ilike(search_term) |
            Program.program_code.ilike(search_term)
        )

    if is_active is not None:
        query = query.where(Program.is_active == is_active)
        count_query = count_query.where(Program.is_active == is_active)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(
        query.offset(skip).limit(limit).order_by(Program.program_name)
    )
    programs = result.scalars().all()
    return ProgramListOut(programs=programs, total=total)


@router.get("/{program_id}", response_model=ProgramOut)
async def get_program(program_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single program by ID."""
    result = await db.execute(select(Program).where(Program.program_id == program_id))
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    return program


@router.post("/", response_model=ProgramOut, status_code=status.HTTP_201_CREATED)
async def create_program(data: ProgramCreate, db: AsyncSession = Depends(get_db)):
    """Create a new program."""
    # Check for existing program code or name
    existing = await db.execute(
        select(Program).where(
            (Program.program_code == data.program_code) |
            (Program.program_name == data.program_name)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Program code or name already exists",
        )

    # Verify department exists
    dept_result = await db.execute(
        select(Department).where(Department.department_id == data.department_id)
    )
    if not dept_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department not found",
        )

    payload = data.model_dump(exclude={"program_fee", "fee_per_year"})
    program = Program(**payload)
    db.add(program)
    await db.flush()
    await db.refresh(program)
    return program


@router.put("/{program_id}", response_model=ProgramOut)
async def update_program(program_id: int, data: ProgramUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing program."""
    result = await db.execute(select(Program).where(Program.program_id == program_id))
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")

    update_data = data.model_dump(exclude_unset=True, exclude={"program_fee", "fee_per_year"})

    # Check for conflicts if updating code or name
    if "program_code" in update_data or "program_name" in update_data:
        existing = await db.execute(
            select(Program).where(
                Program.program_id != program_id,
                (
                    Program.program_code == update_data.get("program_code", "") if "program_code" in update_data else False
                ) | (
                    Program.program_name == update_data.get("program_name", "") if "program_name" in update_data else False
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Program code or name already exists",
            )

    # Verify department exists if updating
    if "department_id" in update_data:
        dept_result = await db.execute(
            select(Department).where(Department.department_id == update_data["department_id"])
        )
        if not dept_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found",
            )

    for key, value in update_data.items():
        setattr(program, key, value)

    await db.flush()
    await db.refresh(program)
    return program


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_program(program_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a program (soft delete by setting is_active to False)."""
    result = await db.execute(select(Program).where(Program.program_id == program_id))
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")

    program.is_active = False
    await db.flush()
    return None


@router.get("/{program_id}/students")
async def get_program_students(
    program_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get all students enrolled in a program."""
    from app.models.people import Student
    from app.schemas.people import StudentListOut, StudentOut

    result = await db.execute(select(Program).where(Program.program_id == program_id))
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")

    count_query = select(func.count(Student.student_id)).where(Student.program_id == program_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = select(Student).where(Student.program_id == program_id).offset(skip).limit(limit)
    students_result = await db.execute(query)
    students = students_result.scalars().all()

    return StudentListOut(students=students, total=total)
=======
"""Program management endpoints with full CRUD operations."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.academic import Program, Department
from app.schemas.academic import (
    ProgramOut, ProgramListOut, ProgramCreate, ProgramUpdate
)

router = APIRouter()


@router.get("/", response_model=ProgramListOut)
async def list_programs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    department_id: int | None = Query(None),
    degree_level: str | None = Query(None),
    search: str | None = Query(None),
    is_active: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List programs with optional filters and pagination."""
    query = select(Program)
    count_query = select(func.count(Program.program_id))

    if department_id is not None:
        query = query.where(Program.department_id == department_id)
        count_query = count_query.where(Program.department_id == department_id)

    if degree_level:
        query = query.where(Program.degree_level == degree_level)
        count_query = count_query.where(Program.degree_level == degree_level)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            Program.program_name.ilike(search_term) |
            Program.program_code.ilike(search_term)
        )
        count_query = count_query.where(
            Program.program_name.ilike(search_term) |
            Program.program_code.ilike(search_term)
        )

    if is_active is not None:
        query = query.where(Program.is_active == is_active)
        count_query = count_query.where(Program.is_active == is_active)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(
        query.offset(skip).limit(limit).order_by(Program.program_name)
    )
    programs = result.scalars().all()
    return ProgramListOut(programs=programs, total=total)


@router.get("/{program_id}", response_model=ProgramOut)
async def get_program(program_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single program by ID."""
    result = await db.execute(select(Program).where(Program.program_id == program_id))
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    return program


@router.post("/", response_model=ProgramOut, status_code=status.HTTP_201_CREATED)
async def create_program(data: ProgramCreate, db: AsyncSession = Depends(get_db)):
    """Create a new program."""
    # Check for existing program code or name
    existing = await db.execute(
        select(Program).where(
            (Program.program_code == data.program_code) |
            (Program.program_name == data.program_name)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Program code or name already exists",
        )

    # Verify department exists
    dept_result = await db.execute(
        select(Department).where(Department.department_id == data.department_id)
    )
    if not dept_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department not found",
        )

    program = Program(**data.model_dump())
    db.add(program)
    await db.flush()
    await db.refresh(program)
    return program


@router.put("/{program_id}", response_model=ProgramOut)
async def update_program(program_id: int, data: ProgramUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing program."""
    result = await db.execute(select(Program).where(Program.program_id == program_id))
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")

    update_data = data.model_dump(exclude_unset=True)

    # Check for conflicts if updating code or name
    if "program_code" in update_data or "program_name" in update_data:
        existing = await db.execute(
            select(Program).where(
                Program.program_id != program_id,
                (
                    Program.program_code == update_data.get("program_code", "") if "program_code" in update_data else False
                ) | (
                    Program.program_name == update_data.get("program_name", "") if "program_name" in update_data else False
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Program code or name already exists",
            )

    # Verify department exists if updating
    if "department_id" in update_data:
        dept_result = await db.execute(
            select(Department).where(Department.department_id == update_data["department_id"])
        )
        if not dept_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found",
            )

    for key, value in update_data.items():
        setattr(program, key, value)

    await db.flush()
    await db.refresh(program)
    return program


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_program(program_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a program (soft delete by setting is_active to False)."""
    result = await db.execute(select(Program).where(Program.program_id == program_id))
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")

    program.is_active = False
    await db.flush()
    return None


@router.get("/{program_id}/students")
async def get_program_students(
    program_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get all students enrolled in a program."""
    from app.models.people import Student
    from app.schemas.people import StudentListOut, StudentOut

    result = await db.execute(select(Program).where(Program.program_id == program_id))
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")

    count_query = select(func.count(Student.student_id)).where(Student.program_id == program_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = select(Student).where(Student.program_id == program_id).offset(skip).limit(limit)
    students_result = await db.execute(query)
    students = students_result.scalars().all()

    return StudentListOut(students=students, total=total)
>>>>>>> a1077c5da31aaef6385c7850c5580088169ce36c
