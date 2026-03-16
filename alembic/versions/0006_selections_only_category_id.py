"""Удаление из selections полей expected_benefit_amount, availability_status, availability_reason. Оставляем только связь с категориями (selection_id, user_id, category_id, idempotency_key)."""

from alembic import op
import sqlalchemy as sa

revision = "0006_selections_only_category_id"
down_revision = "0005_varchar_and_check_constraints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("selections_expected_benefit_amount_check", "selections", type_="check")
    op.drop_constraint("selections_availability_status_check", "selections", type_="check")
    op.drop_column("selections", "expected_benefit_amount")
    op.drop_column("selections", "availability_status")
    op.drop_column("selections", "availability_reason")


def downgrade() -> None:
    op.add_column("selections", sa.Column("expected_benefit_amount", sa.BigInteger(), nullable=True))
    op.add_column("selections", sa.Column("availability_status", sa.String(50), nullable=True))
    op.add_column("selections", sa.Column("availability_reason", sa.String(500), nullable=True))
    op.create_check_constraint(
        "selections_expected_benefit_amount_check",
        "selections",
        "expected_benefit_amount IS NULL OR expected_benefit_amount >= 0",
    )
    op.create_check_constraint(
        "selections_availability_status_check",
        "selections",
        "availability_status IS NULL OR availability_status IN ('available', 'budget_limited', 'unavailable')",
    )
