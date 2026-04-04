from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class AssignmentTeam(Base):
    __tablename__ = "assignment_teams"

    team_id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey("assignments.assignment_id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignment = relationship("Assignment", back_populates="teams")
    members = relationship("AssignmentTeamMember", back_populates="team", cascade="all, delete-orphan", lazy="selectin")


class AssignmentTeamMember(Base):
    __tablename__ = "assignment_team_members"

    team_id = Column(Integer, ForeignKey("assignment_teams.team_id", ondelete="CASCADE"), primary_key=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.student_id", ondelete="CASCADE"), primary_key=True)
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    team = relationship("AssignmentTeam", back_populates="members")
    student = relationship("Student")
