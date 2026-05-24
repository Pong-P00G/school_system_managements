"""Announcements endpoints for class announcements."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.academic import Announcement, CourseSection
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_announcement(
    section_id: int = Query(...),
    title: str = Query(..., min_length=1),
    content: str = Query(..., min_length=1),
    is_pinned: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Teacher creates an announcement for a section."""
    announcement = Announcement(
        section_id=section_id,
        author_id=current_user.user_id,
        title=title,
        content=content,
        is_pinned=is_pinned,
    )
    db.add(announcement)
    await db.flush()
    await db.refresh(announcement)
    return {
        "announcement_id": announcement.announcement_id,
        "section_id": announcement.section_id,
        "title": announcement.title,
        "content": announcement.content,
        "is_pinned": announcement.is_pinned,
        "created_at": announcement.created_at,
    }


@router.get("/section/{section_id}")
async def get_section_announcements(
    section_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all announcements for a section."""
    result = await db.execute(
        select(Announcement)
        .options(selectinload(Announcement.author))
        .where(Announcement.section_id == section_id)
        .order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc())
    )
    announcements = result.scalars().all()
    return [
        {
            "announcement_id": a.announcement_id,
            "title": a.title,
            "content": a.content,
            "is_pinned": a.is_pinned,
            "author_name": a.author.username if a.author else "Unknown",
            "created_at": a.created_at,
        }
        for a in announcements
    ]


@router.get("/my-sections")
async def get_my_announcements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all announcements for sections the current user is enrolled in or teaches."""
    result = await db.execute(
        select(Announcement)
        .options(
            selectinload(Announcement.author),
            selectinload(Announcement.section).selectinload(CourseSection.course),
        )
        .order_by(Announcement.created_at.desc())
        .limit(50)
    )
    announcements = result.scalars().all()
    return [
        {
            "announcement_id": a.announcement_id,
            "title": a.title,
            "content": a.content,
            "is_pinned": a.is_pinned,
            "author_name": a.author.username if a.author else "Unknown",
            "course_code": a.section.course.course_code if a.section and a.section.course else "",
            "course_name": a.section.course.course_name if a.section and a.section.course else "",
            "section_id": a.section_id,
            "created_at": a.created_at,
        }
        for a in announcements
    ]


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    announcement_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an announcement."""
    result = await db.execute(select(Announcement).where(Announcement.announcement_id == announcement_id))
    announcement = result.scalar_one_or_none()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    if announcement.author_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not your announcement")
    await db.delete(announcement)
    await db.flush()
