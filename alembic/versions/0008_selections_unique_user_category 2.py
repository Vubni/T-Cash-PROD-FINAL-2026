from alembic import op

revision = "0008_selections_unique_user_category"
down_revision = "0007_budget_amount_bigint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "selections_user_id_category_id_key",
        "selections",
        ["user_id", "category_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "selections_user_id_category_id_key",
        "selections",
        type_="unique",
    )
