import uuid
from database.database import Database

REQUIRED_SELECTION_COUNT = 5


async def get_current_category_ids(user_id: int) -> list[str] | None:
    """
    Возвращает список category_id выбранных категорий пользователя (только id, в порядке записей).
    None, если у пользователя нет выбора.
    """
    async with Database() as db:
        rows = await db.execute_all(
            "SELECT category_id FROM selections WHERE user_id = $1::bigint ORDER BY created_at",
            (user_id,),
        ) or []
    if not rows:
        return None
    return [str(r["category_id"]) for r in rows]


async def check_categories_exist(category_ids: list[str]) -> bool:
    """Проверяет, что все category_id существуют в categories."""
    if not category_ids:
        return False
    async with Database() as db:
        placeholders = ", ".join(f"${i+1}" for i in range(len(category_ids)))
        sql = f"SELECT 1 FROM categories WHERE category_id IN ({placeholders})"
        rows = await db.execute_all(sql, tuple(category_ids)) or []
    return len(rows) == len(category_ids)


def _generate_selection_uuid() -> str:
    return str(uuid.uuid4())


async def save_selection_batch(user_id: int, category_ids: list[str]) -> list[str]:
    """
    Сохраняет ровно N категорий в selections для пользователя.
    Старые записи по user_id удаляются, вставляются новые.
    Возвращает список созданных selection_id (UUID строк).
    """
    created_ids = []
    async with Database() as db:
        await db.execute("DELETE FROM selections WHERE user_id = $1::bigint", (user_id,))
        for cat_id in category_ids:
            sel_id = _generate_selection_uuid()
            await db.execute(
                """
                INSERT INTO selections (selection_id, user_id, category_id)
                VALUES ($1, $2::bigint, $3)
                """,
                (sel_id, user_id, cat_id),
            )
            created_ids.append(sel_id)
    return created_ids
