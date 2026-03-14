"""drop users role column and check constraint.
Revision ID: 0003_drop_users_role
Revises: 0002_users_and_selection_user_period
Create Date: 2026-03-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_drop_users_role"
down_revision = "0002_users_and_selection_user_period"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("users_role_check", "users", type_="check")
    op.drop_column("users", "role")


def downgrade() -> None:
    op.add_column("users", sa.Column("role", sa.Text(), nullable=True))
    op.execute("UPDATE users SET role = 'client' WHERE role IS NULL")
    op.alter_column("users", "role", nullable=False)
    op.create_check_constraint("users_role_check", "users", "role IN ('admin', 'client')")

