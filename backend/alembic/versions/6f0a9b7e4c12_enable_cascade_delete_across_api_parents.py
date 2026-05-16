"""enable cascade delete across api parents

Revision ID: 6f0a9b7e4c12
Revises: e5807c3ba9fe
Create Date: 2026-05-16 11:20:00.000000
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "6f0a9b7e4c12"
down_revision: Union[str, None] = "e5807c3ba9fe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("fk_course_dept", "courses", type_="foreignkey")
    op.create_foreign_key(
        "fk_course_dept",
        "courses",
        "departments",
        ["department_id"],
        ["department_id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_prog_dept", "programs", type_="foreignkey")
    op.create_foreign_key(
        "fk_prog_dept",
        "programs",
        "departments",
        ["department_id"],
        ["department_id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_faculty_dept", "faculty", type_="foreignkey")
    op.create_foreign_key(
        "fk_faculty_dept",
        "faculty",
        "departments",
        ["department_id"],
        ["department_id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_section_course", "course_sections", type_="foreignkey")
    op.create_foreign_key(
        "fk_section_course",
        "course_sections",
        "courses",
        ["course_id"],
        ["course_id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_section_term", "course_sections", type_="foreignkey")
    op.create_foreign_key(
        "fk_section_term",
        "course_sections",
        "academic_terms",
        ["term_id"],
        ["term_id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_student_program", "students", type_="foreignkey")
    op.create_foreign_key(
        "fk_student_program",
        "students",
        "programs",
        ["program_id"],
        ["program_id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_enroll_student", "enrollments", type_="foreignkey")
    op.create_foreign_key(
        "fk_enroll_student",
        "enrollments",
        "students",
        ["student_id"],
        ["student_id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_enroll_section", "enrollments", type_="foreignkey")
    op.create_foreign_key(
        "fk_enroll_section",
        "enrollments",
        "course_sections",
        ["section_id"],
        ["section_id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_account_student", "student_accounts", type_="foreignkey")
    op.create_foreign_key(
        "fk_account_student",
        "student_accounts",
        "students",
        ["student_id"],
        ["student_id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_trans_account", "financial_transactions", type_="foreignkey")
    op.create_foreign_key(
        "fk_trans_account",
        "financial_transactions",
        "student_accounts",
        ["account_id"],
        ["account_id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_trans_processed_by", "financial_transactions", type_="foreignkey")
    op.create_foreign_key(
        "fk_trans_processed_by",
        "financial_transactions",
        "users",
        ["processed_by"],
        ["user_id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_assign_created_by", "assignments", type_="foreignkey")
    op.create_foreign_key(
        "fk_assign_created_by",
        "assignments",
        "users",
        ["created_by"],
        ["user_id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_attend_recorded_by", "attendance", type_="foreignkey")
    op.create_foreign_key(
        "fk_attend_recorded_by",
        "attendance",
        "users",
        ["recorded_by"],
        ["user_id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("fk_ura_role", "user_role_assignments", type_="foreignkey")
    op.create_foreign_key(
        "fk_ura_role",
        "user_role_assignments",
        "user_roles",
        ["role_id"],
        ["role_id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("reviews_faculty_id_fkey", "reviews", type_="foreignkey")
    op.create_foreign_key(
        "reviews_faculty_id_fkey",
        "reviews",
        "faculty",
        ["faculty_id"],
        ["faculty_id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("reviews_faculty_id_fkey", "reviews", type_="foreignkey")
    op.create_foreign_key(
        "reviews_faculty_id_fkey",
        "reviews",
        "faculty",
        ["faculty_id"],
        ["faculty_id"],
        ondelete="SET NULL",
    )

    op.drop_constraint("fk_ura_role", "user_role_assignments", type_="foreignkey")
    op.create_foreign_key(
        "fk_ura_role",
        "user_role_assignments",
        "user_roles",
        ["role_id"],
        ["role_id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint("fk_attend_recorded_by", "attendance", type_="foreignkey")
    op.create_foreign_key(
        "fk_attend_recorded_by",
        "attendance",
        "users",
        ["recorded_by"],
        ["user_id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint("fk_assign_created_by", "assignments", type_="foreignkey")
    op.create_foreign_key(
        "fk_assign_created_by",
        "assignments",
        "users",
        ["created_by"],
        ["user_id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint("fk_trans_processed_by", "financial_transactions", type_="foreignkey")
    op.create_foreign_key(
        "fk_trans_processed_by",
        "financial_transactions",
        "users",
        ["processed_by"],
        ["user_id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint("fk_trans_account", "financial_transactions", type_="foreignkey")
    op.create_foreign_key(
        "fk_trans_account",
        "financial_transactions",
        "student_accounts",
        ["account_id"],
        ["account_id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint("fk_account_student", "student_accounts", type_="foreignkey")
    op.create_foreign_key(
        "fk_account_student",
        "student_accounts",
        "students",
        ["student_id"],
        ["student_id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint("fk_enroll_section", "enrollments", type_="foreignkey")
    op.create_foreign_key(
        "fk_enroll_section",
        "enrollments",
        "course_sections",
        ["section_id"],
        ["section_id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint("fk_enroll_student", "enrollments", type_="foreignkey")
    op.create_foreign_key(
        "fk_enroll_student",
        "enrollments",
        "students",
        ["student_id"],
        ["student_id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint("fk_student_program", "students", type_="foreignkey")
    op.create_foreign_key(
        "fk_student_program",
        "students",
        "programs",
        ["program_id"],
        ["program_id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint("fk_section_term", "course_sections", type_="foreignkey")
    op.create_foreign_key(
        "fk_section_term",
        "course_sections",
        "academic_terms",
        ["term_id"],
        ["term_id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint("fk_section_course", "course_sections", type_="foreignkey")
    op.create_foreign_key(
        "fk_section_course",
        "course_sections",
        "courses",
        ["course_id"],
        ["course_id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint("fk_faculty_dept", "faculty", type_="foreignkey")
    op.create_foreign_key(
        "fk_faculty_dept",
        "faculty",
        "departments",
        ["department_id"],
        ["department_id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint("fk_prog_dept", "programs", type_="foreignkey")
    op.create_foreign_key(
        "fk_prog_dept",
        "programs",
        "departments",
        ["department_id"],
        ["department_id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint("fk_course_dept", "courses", type_="foreignkey")
    op.create_foreign_key(
        "fk_course_dept",
        "courses",
        "departments",
        ["department_id"],
        ["department_id"],
        ondelete="RESTRICT",
    )
