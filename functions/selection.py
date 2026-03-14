import uuid
from database.database import Database

REQUIRED_SELECTION_COUNT = 5


def row_to_selection_detail(row: dict) -> dict:
    return {
        "selection_id": str(row["selection_id"]),
        "category_id": str(row["category_id"]),
        "name": row["name"],
        "subtitle": row["subtitle"],
        "rate": {"min": row["rate_min"], "max": row["rate_max"]},
        "expected_benefit_amount": row["expected_benefit_amount"],
        "budget_message": row["availability_reason"],
    }


_SELECTION_JOIN_SQL = """
    SELECT
        s.selection_id,
        s.category_id,
        s.expected_benefit_amount,
        s.availability_reason,
        c.name,
        c.subtitle,
        c.rate_min,
        c.rate_max
    FROM selections s
    JOIN categories c ON c.category_id = s.category_id
    WHERE s.idempotency_key = $1
"""


async def get_selection(idempotency_key: str) -> list[dict] | None:
    """Возвращает список записей выбора по ключу идемпотентности (selection_id из path)."""
    async with Database() as db:
        rows = await db.execute_all(_SELECTION_JOIN_SQL, (idempotency_key,)) or []
    if not rows:
        return None
    return [row_to_selection_detail(r) for r in rows]


async def check_categories_exist(category_ids: list[str]) -> bool:
    """Проверяет, что все category_id существуют в categories."""
    if not category_ids:
        return False
    async with Database() as db:
        placeholders = ", ".join(f"${i+1}" for i in range(len(category_ids)))
        sql = f"SELECT 1 FROM categories WHERE category_id IN ({placeholders})"
        rows = await db.execute_all(sql, tuple(category_ids)) or []
    return len(rows) == len(category_ids)


IDEMPOTENCY_KEY_MAX_LENGTH = 128


def validate_idempotency_key(key: str | None) -> None:
    """Проверяет длину idempotency_key (VARCHAR(128) в БД)."""
    if key is None:
        return
    if len(key) > IDEMPOTENCY_KEY_MAX_LENGTH:
        raise ValueError(f"idempotency_key cannot exceed {IDEMPOTENCY_KEY_MAX_LENGTH} characters")


def _generate_selection_uuid() -> str:
    return str(uuid.uuid4())


async def save_selection_batch(
    user_id: str, category_ids: list[str], idempotency_key: str | None = None
) -> list[str]:
    """
    Сохраняет ровно 5 категорий в selections для пользователя.
    Старые записи по user_id удаляются, вставляются 5 новых.
    Возвращает список созданных selection_id (UUID строк).
    """
    validate_idempotency_key(idempotency_key)
    created_ids = []
    async with Database() as db:
        await db.execute("DELETE FROM selections WHERE user_id = $1::uuid", (user_id,))
        for cat_id in category_ids:
            sel_id = _generate_selection_uuid()
            await db.execute(
                """
                INSERT INTO selections (selection_id, user_id, category_id, idempotency_key)
                VALUES ($1, $2::uuid, $3, $4)
                """,
                (sel_id, user_id, cat_id, idempotency_key),
            )
            created_ids.append(sel_id)
    return created_ids
