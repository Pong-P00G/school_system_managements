"""add notifications table

Revision ID: 9384fd4343d5
Revises: 637dc4e08c2a
Create Date: 2026-05-08 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '9384fd4343d5'
down_revision: Union[str, None] = '637dc4e08c2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'notifications',
        sa.Column('notification_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('notification_type', sa.String(length=20), nullable=False, server_default='info'),
        sa.Column('reference_type', sa.String(length=50), nullable=True),
        sa.Column('reference_id', sa.String(length=50), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('notification_id'),
    )
    op.create_index(
        'ix_notifications_user_unread',
        'notifications',
        ['user_id', 'is_read'],
    )


def downgrade() -> None:
    op.drop_index('ix_notifications_user_unread', table_name='notifications')
    op.drop_table('notifications')
