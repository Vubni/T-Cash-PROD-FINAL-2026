"""Замена TEXT на VARCHAR с ограничениями и CHECK для правил, категорий, selections, audit_log, admin_users."""

from alembic import op
import sqlalchemy as sa

revision = "0005_varchar_and_check_constraints"
down_revision = "0004_drop_audience_add_rate_min_max"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "rules",
        "gender",
        existing_type=sa.TEXT(),
        type_=sa.String(20),
        existing_nullable=True,
    )
    op.create_check_constraint(
        "rules_gender_check",
        "rules",
        "gender IS NULL OR gender IN ('male', 'female', 'other')",
    )
    op.create_check_constraint(
        "rules_min_age_check",
        "rules",
        "min_age IS NULL OR min_age >= 0",
    )
    op.create_check_constraint(
        "rules_max_age_check",
        "rules",
        "max_age IS NULL OR max_age >= 0",
    )
    op.create_check_constraint(
        "rules_income_check",
        "rules",
        "income IS NULL OR income >= 0",
    )

    op.alter_column(
        "categories",
        "name",
        existing_type=sa.TEXT(),
        type_=sa.String(500),
        existing_nullable=False,
    )
    op.alter_column(
        "categories",
        "subtitle",
        existing_type=sa.TEXT(),
        type_=sa.String(500),
        existing_nullable=False,
    )
    op.create_check_constraint(
        "categories_name_check",
        "categories",
        "char_length(name) >= 1 AND char_length(name) <= 500",
    )
    op.create_check_constraint(
        "categories_subtitle_check",
        "categories",
        "char_length(subtitle) >= 1 AND char_length(subtitle) <= 500",
    )
    op.create_check_constraint(
        "categories_budget_amount_check",
        "categories",
        "budget_amount >= 0",
    )
    op.create_check_constraint(
        "categories_rate_min_check",
        "categories",
        "rate_min >= 0 AND rate_min <= 100",
    )
    op.create_check_constraint(
        "categories_rate_max_check",
        "categories",
        "rate_max >= 0 AND rate_max <= 100 AND rate_max >= rate_min",
    )

    op.alter_column(
        "selections",
        "availability_status",
        existing_type=sa.TEXT(),
        type_=sa.String(50),
        existing_nullable=True,
    )
    op.create_check_constraint(
        "selections_availability_status_check",
        "selections",
        "availability_status IS NULL OR availability_status IN ('available', 'budget_limited', 'unavailable')",
    )
    op.alter_column(
        "selections",
        "availability_reason",
        existing_type=sa.TEXT(),
        type_=sa.String(500),
        existing_nullable=True,
    )
    op.alter_column(
        "selections",
        "idempotency_key",
        existing_type=sa.TEXT(),
        type_=sa.String(128),
        existing_nullable=True,
    )
    op.create_check_constraint(
        "selections_expected_benefit_amount_check",
        "selections",
        "expected_benefit_amount IS NULL OR expected_benefit_amount >= 0",
    )

    op.alter_column(
        "audit_log",
        "entity_type",
        existing_type=sa.TEXT(),
        type_=sa.String(50),
        existing_nullable=False,
    )
    op.alter_column(
        "audit_log",
        "entity_id",
        existing_type=sa.TEXT(),
        type_=sa.String(64),
        existing_nullable=False,
    )
    op.alter_column(
        "audit_log",
        "action",
        existing_type=sa.TEXT(),
        type_=sa.String(50),
        existing_nullable=False,
    )
    op.alter_column(
        "audit_log",
        "actor",
        existing_type=sa.TEXT(),
        type_=sa.String(255),
        existing_nullable=False,
    )
    op.create_check_constraint(
        "audit_log_entity_type_check",
        "audit_log",
        "char_length(entity_type) >= 1 AND char_length(entity_type) <= 50",
    )
    op.create_check_constraint(
        "audit_log_entity_id_check",
        "audit_log",
        "char_length(entity_id) >= 1 AND char_length(entity_id) <= 64",
    )
    op.create_check_constraint(
        "audit_log_action_check",
        "audit_log",
        "char_length(action) >= 1 AND char_length(action) <= 50",
    )
    op.create_check_constraint(
        "audit_log_actor_check",
        "audit_log",
        "char_length(actor) >= 1 AND char_length(actor) <= 255",
    )

    op.alter_column(
        "admin_users",
        "login",
        existing_type=sa.TEXT(),
        type_=sa.String(255),
        existing_nullable=False,
    )
    op.alter_column(
        "admin_users",
        "password",
        existing_type=sa.TEXT(),
        type_=sa.String(255),
        existing_nullable=False,
    )
    op.create_check_constraint(
        "admin_users_login_check",
        "admin_users",
        "char_length(login) >= 1 AND char_length(login) <= 255",
    )
    op.create_check_constraint(
        "admin_users_password_check",
        "admin_users",
        "char_length(password) >= 1",
    )


def downgrade() -> None:
    op.drop_constraint("admin_users_password_check", "admin_users", type_="check")
    op.drop_constraint("admin_users_login_check", "admin_users", type_="check")
    op.alter_column(
        "admin_users",
        "password",
        existing_type=sa.String(255),
        type_=sa.TEXT(),
        existing_nullable=False,
    )
    op.alter_column(
        "admin_users",
        "login",
        existing_type=sa.String(255),
        type_=sa.TEXT(),
        existing_nullable=False,
    )

    for name in ("audit_log_actor_check", "audit_log_action_check", "audit_log_entity_id_check", "audit_log_entity_type_check"):
        op.drop_constraint(name, "audit_log", type_="check")
    op.alter_column("audit_log", "actor", existing_type=sa.String(255), type_=sa.TEXT(), existing_nullable=False)
    op.alter_column("audit_log", "action", existing_type=sa.String(50), type_=sa.TEXT(), existing_nullable=False)
    op.alter_column("audit_log", "entity_id", existing_type=sa.String(64), type_=sa.TEXT(), existing_nullable=False)
    op.alter_column("audit_log", "entity_type", existing_type=sa.String(50), type_=sa.TEXT(), existing_nullable=False)

    op.drop_constraint("selections_expected_benefit_amount_check", "selections", type_="check")
    op.drop_constraint("selections_availability_status_check", "selections", type_="check")
    op.alter_column("selections", "idempotency_key", existing_type=sa.String(128), type_=sa.TEXT(), existing_nullable=True)
    op.alter_column("selections", "availability_reason", existing_type=sa.String(500), type_=sa.TEXT(), existing_nullable=True)
    op.alter_column("selections", "availability_status", existing_type=sa.String(50), type_=sa.TEXT(), existing_nullable=True)

    for name in (
        "categories_rate_max_check",
        "categories_rate_min_check",
        "categories_budget_amount_check",
        "categories_subtitle_check",
        "categories_name_check",
    ):
        op.drop_constraint(name, "categories", type_="check")
    op.alter_column("categories", "subtitle", existing_type=sa.String(500), type_=sa.TEXT(), existing_nullable=False)
    op.alter_column("categories", "name", existing_type=sa.String(500), type_=sa.TEXT(), existing_nullable=False)

    op.drop_constraint("rules_income_check", "rules", type_="check")
    op.drop_constraint("rules_max_age_check", "rules", type_="check")
    op.drop_constraint("rules_min_age_check", "rules", type_="check")
    op.drop_constraint("rules_gender_check", "rules", type_="check")
    op.alter_column("rules", "gender", existing_type=sa.String(20), type_=sa.TEXT(), existing_nullable=True)
