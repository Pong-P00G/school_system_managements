"""Assignment management endpoints with full CRUD operations."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.people import Assignment
from app.models.academic import CourseSection
from app.schemas.people import (
    AssignmentOut, AssignmentListOut, AssignmentCreate, AssignmentUpdate
)
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=AssignmentListOut)
async def list_assignments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    section_id: int | None = Query(None),
    assignment_type: str | None = Query(None),
    is_published: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List assignments with optional filters and pagination."""
    query = select(Assignment)
    count_query = select(func.count(Assignment.assignment_id))

    if section_id is not None:
        query = query.where(Assignment.section_id == section_id)
        count_query = count_query.where(Assignment.section_id == section_id)

    if assignment_type:
        query = query.where(Assignment.assignment_type == assignment_type)
        count_query = count_query.where(Assignment.assignment_type == assignment_type)

    if is_published is not None:
        query = query.where(Assignment.is_published == is_published)
        count_query = count_query.where(Assignment.is_published == is_published)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    result = await db.execute(
        query.offset(skip).limit(limit).order_by(Assignment.due_date.desc())
    )
    assignments = result.scalars().all()
    return AssignmentListOut(assignments=assignments, total=total)


@router.get("/{assignment_id}", response_model=AssignmentOut)
async def get_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single assignment by ID."""
    result = await db.execute(
        select(Assignment).where(Assignment.assignment_id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    return assignment


@router.post("/", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
async def create_new_assignment(
    data: AssignmentCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new assignment."""
    # Check if section exists
    section_result = await db.execute(select(CourseSection).where(CourseSection.section_id == data.section_id))
    if not section_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course section not found")

    assignment = Assignment(**data.model_dump())
    assignment.created_by = current_user.user_id
    db.add(assignment)
    await db.flush()
    await db.refresh(assignment)
    return assignment


@router.put("/{assignment_id}", response_model=AssignmentOut)
async def update_existing_assignment(
    assignment_id: int, 
    data: AssignmentUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Update an existing assignment."""
    result = await db.execute(select(Assignment).where(Assignment.assignment_id == assignment_id))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(assignment, key, value)

    await db.flush()
    await db.refresh(assignment)
    return assignment


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an assignment."""
    result = await db.execute(select(Assignment).where(Assignment.assignment_id == assignment_id))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    await db.delete(assignment)
    await db.flush()
    return None
    await db.delete(assignment)
    await db.flush()
    return None


# --- Assignment Teams ---

@router.post("/{assignment_id}/teams", status_code=status.HTTP_201_CREATED)
async def create_assignment_team(
    assignment_id: int,
    name: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    """Create a new team for an assignment."""
    from app.models.groups import AssignmentTeam
    
    # Verify assignment exists
    assignment = await db.scalar(select(Assignment).where(Assignment.assignment_id == assignment_id))
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    team = AssignmentTeam(assignment_id=assignment_id, name=name)
    db.add(team)
    await db.commit()
    return {"team_id": team.team_id, "name": team.name, "assignment_id": team.assignment_id}


@router.get("/{assignment_id}/teams")
async def get_assignment_teams(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all teams for an assignment with members."""
    from app.models.groups import AssignmentTeam, AssignmentTeamMember
    from app.models.people import Student
    from app.models.user import User

    result = await db.execute(
        select(AssignmentTeam)
        .options(
            selectinload(AssignmentTeam.members)
            .selectinload(AssignmentTeamMember.student)
            .selectinload(Student.user)
            .selectinload(User.personal_info)
        )
        .where(AssignmentTeam.assignment_id == assignment_id)
        .order_by(AssignmentTeam.name)
    )
    teams = result.scalars().all()

    out = []
    for t in teams:
        members = []
        for m in t.members:
            user = m.student.user if m.student else None
            info = user.personal_info if user else None
            if info:
                name = f"{info.first_name} {info.last_name}".strip()
            else:
                name = user.username if user else "Unknown"
            members.append({
                "student_id": m.student_id,
                "name": name,
                "student_number": m.student.student_number if m.student else None,
                "joined_at": m.joined_at
            })
        out.append({
            "team_id": t.team_id,
            "name": t.name,
            "members": members
        })
    return out


@router.post("/teams/{team_id}/members", status_code=status.HTTP_201_CREATED)
async def add_team_member(
    team_id: int,
    student_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Add a student to a team."""
    from app.models.groups import AssignmentTeam, AssignmentTeamMember
    
    team = await db.scalar(select(AssignmentTeam).where(AssignmentTeam.team_id == team_id))
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Check member existence
    existing = await db.scalar(
        select(AssignmentTeamMember).where(
            AssignmentTeamMember.team_id == team_id,
            AssignmentTeamMember.student_id == student_id
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Student already in this team")

    member = AssignmentTeamMember(team_id=team_id, student_id=student_id)
    db.add(member)
    await db.commit()
    return {"message": "Member added"}


@router.delete("/teams/{team_id}/members/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: int,
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Remove a student from a team."""
    from app.models.groups import AssignmentTeamMember
    
    member = await db.scalar(
        select(AssignmentTeamMember).where(
            AssignmentTeamMember.team_id == team_id,
            AssignmentTeamMember.student_id == student_id
        )
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in team")

    await db.delete(member)
    await db.commit()

