import os
from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from alembic import context

from sqlalchemy import MetaData, Table, Column, BigInteger
from sqlalchemy import Text, Integer, Boolean
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TIMESTAMP

config = context.config

# В Docker берём URL из DB_IP, DB_USER, DB_PASSWORD, DB_DB (как в docker-compose).
# Иначе — DATABASE_URL/ALEMBIC_DATABASE_URL или значение из alembic.ini.
_resolved_url = None
if os.environ.get("DB_IP"):
    _user = os.environ.get("DB_USER", "user")
    _password = os.environ.get("DB_PASSWORD", "password")
    _db = os.environ.get("DB_DB", "prod")
    _resolved_url = f"postgresql://{_user}:{_password}@{os.environ['DB_IP']}:5432/{_db}"
    config.set_main_option("sqlalchemy_url", _resolved_url)
else:
    _url = os.environ.get("DATABASE_URL") or os.environ.get("ALEMBIC_DATABASE_URL")
    if _url:
        _resolved_url = _url
        config.set_main_option("sqlalchemy_url", _resolved_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = MetaData()

categories = Table(
    "categories",
    target_metadata,
    Column("id", BigInteger, primary_key=True),
    Column("category_id", Text, nullable=False, unique=True),
    Column("name", Text, nullable=False),
    Column("subtitle", Text, nullable=False),
    Column("icon_key", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("budget_amount", BigInteger, nullable=False),
    Column("budget_currency", Text, nullable=False),
    Column("target_users", Integer, nullable=False),
    Column("avg_spend_per_user", BigInteger, nullable=False),
    Column("audience_segments", ARRAY(Text), nullable=False),
    Column("rule_personalized", Boolean, nullable=False),
    Column("rule_budget_mode", Text, nullable=False),
    Column("rule_fallback_message", Text, nullable=False),
    Column("created_at", TIMESTAMP(timezone=True), nullable=False),
    Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
)

selections = Table(
    "selections",
    target_metadata,
    Column("id", BigInteger, primary_key=True),
    Column("selection_id", Text, nullable=False, unique=True),
    Column("period_id", Text, nullable=False),
    Column("category_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("expected_benefit_amount", BigInteger, nullable=True),
    Column("currency", Text, nullable=True),
    Column("availability_status", Text, nullable=True),
    Column("availability_reason", Text, nullable=True),
    Column("idempotency_key", Text, nullable=True),
    Column("created_at", TIMESTAMP(timezone=True), nullable=False),
    Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
)

audit_log = Table(
    "audit_log",
    target_metadata,
    Column("id", BigInteger, primary_key=True),
    Column("entity_type", Text, nullable=False),
    Column("entity_id", Text, nullable=False),
    Column("action", Text, nullable=False),
    Column("actor", Text, nullable=False),
    Column("details", JSONB, nullable=True),
    Column("created_at", TIMESTAMP(timezone=True), nullable=False),
)


def run_migrations_offline() -> None:
    url = _resolved_url or config.get_main_option("sqlalchemy_url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = _resolved_url or config.get_main_option("sqlalchemy_url")
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

