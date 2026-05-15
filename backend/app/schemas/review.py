"""Pydantic schemas for Reviews."""

from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ReviewBase(BaseModel):
    """Fields a student can submit when creating/updating a review."""

    overall_rating: int = Field(..., ge=1, le=5)
    teaching_rating: Optional[int] = Field(None, ge=1, le=5)
    content_rating: Optional[int] = Field(None, ge=1, le=5)
    workload_rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    comment: Optional[str] = None
    is_anonymous: bool = False

    @field_validator("overall_rating", "teaching_rating", "content_rating", "workload_rating")
    @classmethod
    def check_rating_range(cls, v: int | None) -> int | None:
        if v is not None and (v < 1 or v > 5):
            raise ValueError("Rating must be between 1 and 5")
        return v


class ReviewCreate(ReviewBase):
    """Schema for creating a new review."""

    enrollment_id: int


class ReviewUpdate(BaseModel):
    """Schema for updating an existing review (all fields optional)."""

    overall_rating: Optional[int] = Field(None, ge=1, le=5)
    teaching_rating: Optional[int] = Field(None, ge=1, le=5)
    content_rating: Optional[int] = Field(None, ge=1, le=5)
    workload_rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    comment: Optional[str] = None
    is_anonymous: Optional[bool] = None


class ReviewOut(ReviewBase):
    """Schema for review response, includes system fields."""

    review_id: int
    enrollment_id: int
    course_id: Optional[int] = None
    faculty_id: Optional[UUID] = None
    term_id: Optional[int] = None
    is_approved: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewListOut(BaseModel):
    """Paginated list of reviews."""

    reviews: list[ReviewOut]
    total: int


class ReviewSummaryOut(BaseModel):
    """Aggregated rating summary for a course or faculty."""

    total_reviews: int
    average_overall: Optional[float] = None
    average_teaching: Optional[float] = None
    average_content: Optional[float] = None
    average_workload: Optional[float] = None
    distribution: dict[str, int]  # e.g., {"1": 5, "2": 10, "3": 25, "4": 40, "5": 20}


class ReviewableEnrollmentOut(BaseModel):
    """Enrollment that a student can review (simplified)."""

    enrollment_id: int
    section_id: int
    course_name: str
    course_code: str
    term_name: str
    faculty_name: str
    has_reviewed: bool = False

    model_config = {"from_attributes": True}
