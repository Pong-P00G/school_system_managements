"""Review model for student course evaluations."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Review(Base):
    """Student review of a course section they were enrolled in."""

    __tablename__ = "reviews"

    review_id = Column(Integer, primary_key=True, autoincrement=True)
    enrollment_id = Column(
        Integer,
        ForeignKey("enrollments.enrollment_id", ondelete="CASCADE"),
        nullable=False,
    )

    # Denormalized for efficient summary queries
    course_id = Column(
        Integer,
        ForeignKey("courses.course_id", ondelete="SET NULL"),
        nullable=True,
    )
    faculty_id = Column(
        UUID(as_uuid=True),
        ForeignKey("faculty.faculty_id", ondelete="SET NULL"),
        nullable=True,
    )
    term_id = Column(
        Integer,
        ForeignKey("academic_terms.term_id", ondelete="SET NULL"),
        nullable=True,
    )

    # Ratings (1–5 scale)
    overall_rating = Column(Integer, nullable=False)
    teaching_rating = Column(Integer, nullable=True)
    content_rating = Column(Integer, nullable=True)
    workload_rating = Column(Integer, nullable=True)

    # Content
    title = Column(String(200), nullable=True)
    comment = Column(Text, nullable=True)

    # Flags
    is_anonymous = Column(Boolean, default=False, nullable=False)
    is_approved = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    enrollment = relationship("Enrollment", back_populates="reviews")
    course = relationship("Course", back_populates="reviews")
    faculty = relationship("Faculty", back_populates="reviews")
    term = relationship("AcademicTerm", back_populates="reviews")

    __table_args__ = (
        UniqueConstraint("enrollment_id", name="uq_review_enrollment"),
    )

    def __repr__(self) -> str:
        return f"<Review(id={self.review_id}, enrollment={self.enrollment_id}, rating={self.overall_rating})>"
