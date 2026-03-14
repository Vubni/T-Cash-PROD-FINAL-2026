"""rules table and categories.rule_id; drop old rule_* columns."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_rules_and_category_rule_id"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rules",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("rule_id", sa.Text(), nullable=False, unique=True),
        sa.Column("min_age", sa.Integer(), nullable=True),
        sa.Column("max_age", sa.Integer(), nullable=True),
        sa.Column("gender", sa.Text(), nullable=True),
        sa.Column("income", sa.BigInteger(), nullable=True),
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

    # Дефолтное правило для существующих категорий
    op.execute(
        "INSERT INTO rules (rule_id, min_age, max_age, gender, income) "
        "VALUES ('default', NULL, NULL, NULL, NULL)"
    )

    op.add_column(
        "categories",
        sa.Column("rule_id", sa.Text(), nullable=True),
    )
    op.execute("UPDATE categories SET rule_id = 'default' WHERE rule_id IS NULL")
    op.alter_column(
        "categories",
        "rule_id",
        nullable=False,
    )
    op.create_foreign_key(
        "categories_rule_id_fkey",
        "categories",
        "rules",
        ["rule_id"],
        ["rule_id"],
    )

    op.drop_column("categories", "rule_personalized")
    op.drop_column("categories", "rule_budget_mode")
    op.drop_column("categories", "rule_fallback_message")


def downgrade() -> None:
    op.add_column(
        "categories",
        sa.Column("rule_personalized", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.add_column(
        "categories",
        sa.Column("rule_budget_mode", sa.Text(), nullable=False, server_default="soft_limit"),
    )
    op.add_column(
        "categories",
        sa.Column("rule_fallback_message", sa.Text(), nullable=False, server_default=""),
    )
    op.drop_constraint("categories_rule_id_fkey", "categories", type_="foreignkey")
    op.drop_column("categories", "rule_id")
    op.drop_table("rules")
