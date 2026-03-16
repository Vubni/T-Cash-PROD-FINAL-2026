"""Перевод rule_id, category_id, selection_id на тип UUID."""

from alembic import op
import sqlalchemy as sa

revision = "0003_uuid_ids"
down_revision = "0002_rules_and_category_rule_id"
branch_labels = None
depends_on = None

DEFAULT_RULE_UUID = "a0000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    op.execute(
        f"UPDATE rules SET rule_id = '{DEFAULT_RULE_UUID}' WHERE rule_id = 'default'"
    )
    op.execute("ALTER TABLE rules ALTER COLUMN rule_id TYPE UUID USING rule_id::uuid")

    op.drop_constraint("categories_rule_id_fkey", "categories", type_="foreignkey")
    op.execute(
        f"UPDATE categories SET rule_id = '{DEFAULT_RULE_UUID}' WHERE rule_id = 'default'"
    )
    op.execute(
        "ALTER TABLE categories ALTER COLUMN rule_id TYPE UUID USING rule_id::uuid"
    )
    op.create_foreign_key(
        "categories_rule_id_fkey",
        "categories",
        "rules",
        ["rule_id"],
        ["rule_id"],
    )

    op.drop_constraint(
        "selections_category_id_fkey", "selections", type_="foreignkey"
    )
    op.add_column(
        "categories",
        sa.Column("category_id_new", sa.UUID(), nullable=True),
    )
    op.execute("UPDATE categories SET category_id_new = gen_random_uuid()")
    op.alter_column(
        "categories",
        "category_id_new",
        nullable=False,
    )
    op.add_column(
        "selections",
        sa.Column("category_id_new", sa.UUID(), nullable=True),
    )
    op.execute("""
        UPDATE selections s SET category_id_new = c.category_id_new
        FROM categories c WHERE c.category_id::text = s.category_id::text
    """)
    op.alter_column(
        "selections",
        "category_id_new",
        nullable=False,
    )
    op.drop_column("selections", "category_id")
    op.alter_column(
        "selections",
        "category_id_new",
        new_column_name="category_id",
    )
    op.drop_column("categories", "category_id")
    op.alter_column(
        "categories",
        "category_id_new",
        new_column_name="category_id",
    )
    op.create_unique_constraint(
        "categories_category_id_key", "categories", ["category_id"]
    )
    op.create_foreign_key(
        "selections_category_id_fkey",
        "selections",
        "categories",
        ["category_id"],
        ["category_id"],
    )

    op.add_column(
        "selections",
        sa.Column("selection_id_new", sa.UUID(), nullable=True),
    )
    op.execute("UPDATE selections SET selection_id_new = gen_random_uuid()")
    op.alter_column(
        "selections",
        "selection_id_new",
        nullable=False,
    )
    op.drop_constraint("selections_selection_id_key", "selections", type_="unique")
    op.drop_column("selections", "selection_id")
    op.alter_column(
        "selections",
        "selection_id_new",
        new_column_name="selection_id",
    )
    op.create_unique_constraint(
        "selections_selection_id_key", "selections", ["selection_id"]
    )


def downgrade() -> None:
    op.drop_constraint("selections_selection_id_key", "selections", type_="unique")
    op.add_column(
        "selections",
        sa.Column("selection_id_old", sa.Text(), nullable=True),
    )
    op.execute(
        "UPDATE selections SET selection_id_old = selection_id::text"
    )
    op.drop_column("selections", "selection_id")
    op.alter_column(
        "selections",
        "selection_id_old",
        new_column_name="selection_id",
    )
    op.create_unique_constraint(
        "selections_selection_id_key", "selections", ["selection_id"]
    )

    op.drop_constraint("selections_category_id_fkey", "selections", type_="foreignkey")
    op.drop_constraint("categories_category_id_key", "categories", type_="unique")
    op.add_column(
        "categories",
        sa.Column("category_id_old", sa.Text(), nullable=True),
    )
    op.execute("UPDATE categories SET category_id_old = category_id::text")
    op.drop_column("categories", "category_id")
    op.alter_column(
        "categories",
        "category_id_old",
        new_column_name="category_id",
    )
    op.create_unique_constraint(
        "categories_category_id_key", "categories", ["category_id"]
    )
    op.add_column(
        "selections",
        sa.Column("category_id_old", sa.Text(), nullable=True),
    )
    op.execute("UPDATE selections SET category_id_old = category_id::text")
    op.drop_column("selections", "category_id")
    op.alter_column(
        "selections",
        "category_id_old",
        new_column_name="category_id",
    )
    op.create_foreign_key(
        "selections_category_id_fkey",
        "selections",
        "categories",
        ["category_id"],
        ["category_id"],
    )

    op.drop_constraint("categories_rule_id_fkey", "categories", type_="foreignkey")
    op.execute(
        "ALTER TABLE categories ALTER COLUMN rule_id TYPE TEXT USING rule_id::text"
    )
    op.execute(
        f"UPDATE categories SET rule_id = 'default' WHERE rule_id = '{DEFAULT_RULE_UUID}'"
    )
    op.execute("ALTER TABLE rules ALTER COLUMN rule_id TYPE TEXT USING rule_id::text")
    op.execute(
        "UPDATE rules SET rule_id = 'default' WHERE rule_id = 'a0000000-0000-0000-0000-000000000001'"
    )
    op.create_foreign_key(
        "categories_rule_id_fkey",
        "categories",
        "rules",
        ["rule_id"],
        ["rule_id"],
    )
