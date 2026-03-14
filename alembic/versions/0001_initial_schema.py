from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("category_id", sa.Text, nullable=False, unique=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("subtitle", sa.Text, nullable=False),
        sa.Column("budget_amount", sa.BigInteger, nullable=False),
        sa.Column("audience_segments", postgresql.ARRAY(sa.Text), nullable=False),
        sa.Column("rule_personalized", sa.Boolean, nullable=False),
        sa.Column("rule_budget_mode", sa.Text, nullable=False),
        sa.Column("rule_fallback_message", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_table(
        "selections",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("selection_id", sa.Text, nullable=False, unique=True),
        sa.Column("category_id", sa.Text, nullable=False),
        sa.Column("expected_benefit_amount", sa.BigInteger, nullable=True),
        sa.Column("availability_status", sa.Text, nullable=True),
        sa.Column("availability_reason", sa.Text, nullable=True),
        sa.Column("idempotency_key", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(["category_id"], ["categories.category_id"]),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("entity_type", sa.Text, nullable=False),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("actor", sa.Text, nullable=False),
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("selections")
    op.drop_table("categories")

