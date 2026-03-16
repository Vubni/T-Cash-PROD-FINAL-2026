from alembic import op
import sqlalchemy as sa

revision = "0007_budget_amount_bigint"
down_revision = "0006_selections_only_category_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "categories",
        "budget_amount",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "categories",
        "budget_amount",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=False,
    )
