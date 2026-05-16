"""Fix audit trigger: use NULL for user_id on DELETE

Revision ID: e5807c3ba9fe
Revises: 9384fd4343d5
Create Date: 2025-06-17 11:11:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5807c3ba9fe'
down_revision: Union[str, None] = '9384fd4343d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ORIGINAL_FUNCTION = """
CREATE OR REPLACE FUNCTION log_user_activity()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (user_id, action, entity_type, entity_id, new_values)
        VALUES (NEW.user_id, 'create', TG_TABLE_NAME, NEW.user_id::TEXT, to_jsonb(NEW));
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (user_id, action, entity_type, entity_id, old_values, new_values)
        VALUES (NEW.user_id, 'update', TG_TABLE_NAME, NEW.user_id::TEXT, to_jsonb(OLD), to_jsonb(NEW));
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (user_id, action, entity_type, entity_id, old_values)
        VALUES (OLD.user_id, 'delete', TG_TABLE_NAME, OLD.user_id::TEXT, to_jsonb(OLD));
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;
"""


FIXED_FUNCTION = """
CREATE OR REPLACE FUNCTION log_user_activity()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (user_id, action, entity_type, entity_id, new_values)
        VALUES (NEW.user_id, 'create', TG_TABLE_NAME, NEW.user_id::TEXT, to_jsonb(NEW));
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (user_id, action, entity_type, entity_id, old_values, new_values)
        VALUES (NEW.user_id, 'update', TG_TABLE_NAME, NEW.user_id::TEXT, to_jsonb(OLD), to_jsonb(NEW));
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (user_id, action, entity_type, entity_id, old_values)
        VALUES (NULL, 'delete', TG_TABLE_NAME, OLD.user_id::TEXT, to_jsonb(OLD));
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    op.execute(FIXED_FUNCTION)


def downgrade() -> None:
    op.execute(ORIGINAL_FUNCTION)
