from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0002_users_and_selection_user_period"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("role", sa.Text, nullable=False),
        sa.CheckConstraint("role IN ('admin', 'client')", name="users_role_check"),
    )
    op.add_column("selections", sa.Column("user_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_selections_user_id",
        "selections",
        "users",
        ["user_id"],
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_selections_user_id", "selections", type_="foreignkey")
    op.drop_column("selections", "user_id")
    op.drop_table("users")
