"""Удаление audience_segments, добавление rate_min и rate_max в categories."""

from alembic import op
import sqlalchemy as sa

revision = "0004_drop_audience_add_rate_min_max"
down_revision = "0003_uuid_ids"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("categories", "audience_segments")

    op.add_column(
        "categories",
        sa.Column("rate_min", sa.Integer(), nullable=True),
    )
    op.add_column(
        "categories",
        sa.Column("rate_max", sa.Integer(), nullable=True),
    )
    op.execute("UPDATE categories SET rate_min = 5, rate_max = 15 WHERE rate_min IS NULL OR rate_max IS NULL")
    op.alter_column(
        "categories",
        "rate_min",
        nullable=False,
    )
    op.alter_column(
        "categories",
        "rate_max",
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("categories", "rate_max")
    op.drop_column("categories", "rate_min")
    op.execute("ALTER TABLE categories ADD COLUMN audience_segments TEXT[] NOT NULL DEFAULT '{}'")
