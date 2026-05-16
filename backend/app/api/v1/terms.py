"""Academic term management endpoints with full CRUD operations."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.academic import AcademicTerm, CourseSection
from app.schemas.academic import (
    AcademicTermOut, AcademicTermListOut, AcademicTermCreate, AcademicTermUpdate
)

router = APIRouter()


@router.get("/", response_model=AcademicTermListOut)
async def list_terms(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    academic_year: str | None = Query(None),
    term_type: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    """List academic terms with optional filters and pagination."""
    query = select(AcademicTerm)
    count_query = select(func.count(AcademicTerm.term_id))

    if academic_year:
        query = query.where(AcademicTerm.academic_year == academic_year)
        count_query = count_query.where(AcademicTerm.academic_year == academic_year)

    if term_type:
        query = query.where(AcademicTerm.term_type == term_type)
        count_query = count_query.where(AcademicTerm.term_type == term_type)

    if status_filter:
        query = query.where(AcademicTerm.status == status_filter)
        count_query = count_query.where(AcademicTerm.status == status_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(
        query.offset(skip).limit(limit).order_by(AcademicTerm.start_date.desc())
    )
    terms = result.scalars().all()
    return AcademicTermListOut(terms=terms, total=total)


@router.get("/{term_id}", response_model=AcademicTermOut)
async def get_term(term_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single academic term by ID."""
    result = await db.execute(select(AcademicTerm).where(AcademicTerm.term_id == term_id))
    term = result.scalar_one_or_none()
    if not term:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic term not found")
    return term


@router.post("/", response_model=AcademicTermOut, status_code=status.HTTP_201_CREATED)
async def create_term(data: AcademicTermCreate, db: AsyncSession = Depends(get_db)):
    """Create a new academic term."""
    # Check for existing term code
    existing = await db.execute(
        select(AcademicTerm).where(AcademicTerm.term_code == data.term_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Academic term code already exists"
        )

    term = AcademicTerm(**data.model_dump())
    db.add(term)
    await db.flush()
    await db.refresh(term)
    return term


@router.put("/{term_id}", response_model=AcademicTermOut)
async def update_term(term_id: int, data: AcademicTermUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing academic term."""
    result = await db.execute(select(AcademicTerm).where(AcademicTerm.term_id == term_id))
    term = result.scalar_one_or_none()
    if not term:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic term not found")

    update_data = data.model_dump(exclude_unset=True)

    # Check for conflicts if updating term code
    if "term_code" in update_data:
        existing = await db.execute(
            select(AcademicTerm).where(
                AcademicTerm.term_id != term_id,
                AcademicTerm.term_code == update_data["term_code"]
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Academic term code already exists"
            )

    for key, value in update_data.items():
        setattr(term, key, value)

    await db.flush()
    await db.refresh(term)
    return term


@router.delete("/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_term(
    term_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an academic term and rely on database cascade rules."""
    result = await db.execute(select(AcademicTerm).where(AcademicTerm.term_id == term_id))
    term = result.scalar_one_or_none()
    if not term:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic term not found")

    await db.delete(term)
    await db.flush()
    return None


@router.get("/current/active")
async def get_current_term(db: AsyncSession = Depends(get_db)):
    """Get the currently active academic term."""
    result = await db.execute(
        select(AcademicTerm).where(AcademicTerm.status == "active").order_by(AcademicTerm.start_date.desc()).limit(1)
    )
    term = result.scalar_one_or_none()
    if not term:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active term found")
    return term


@router.get("/current/upcoming")
async def get_upcoming_terms(
    skip: int = Query(0, ge=0),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    """Get upcoming academic terms."""
    result = await db.execute(
        select(AcademicTerm)
        .where(AcademicTerm.status == "upcoming")
        .order_by(AcademicTerm.start_date)
        .offset(skip)
        .limit(limit)
    )
    terms = result.scalars().all()
    return AcademicTermListOut(terms=terms, total=len(terms))
