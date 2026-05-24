"""add withdrawal_requests table

Revision ID: a1b2c3d4e5f6
Revises: e5807c3ba9fe
Create Date: 2026-05-25 00:50:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = 'a1b2c3d4e5f6'
down_revision = 'e5807c3ba9fe'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'withdrawal_requests',
        sa.Column('request_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('enrollment_id', sa.Integer(), nullable=False),
        sa.Column('student_id', UUID(as_uuid=True), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending', nullable=False),
        sa.Column('reviewed_by', UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewer_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('request_id'),
        sa.ForeignKeyConstraint(['enrollment_id'], ['enrollments.enrollment_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.student_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.user_id'], ondelete='SET NULL'),
    )


def downgrade() -> None:
    op.drop_table('withdrawal_requests')
