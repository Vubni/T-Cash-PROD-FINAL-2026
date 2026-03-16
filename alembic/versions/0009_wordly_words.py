"""Создание таблицы wordly_words для слов игры Wordly."""

from alembic import op
import sqlalchemy as sa


revision = "0009_wordly_words"
down_revision = "0008_selections_unique_user_category"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "wordly_words",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("word", sa.String(length=5), nullable=False),
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.create_unique_constraint(
        "wordly_words_word_key",
        "wordly_words",
        ["word"],
    )
    op.create_check_constraint(
        "wordly_words_word_length_check",
        "wordly_words",
        "char_length(word) = 5",
    )


def downgrade() -> None:
    op.drop_constraint("wordly_words_word_length_check", "wordly_words", type_="check")
    op.drop_constraint("wordly_words_word_key", "wordly_words", type_="unique")
    op.drop_table("wordly_words")

