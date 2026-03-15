import uuid

from core import (
    get_all_categories,
    get_max_selection_count as _get_max_selection_count,
    load_categories_config,
    save_categories_config,
)
from database.database import Database

from functions import calculate as calc_fns

REQUIRED_SELECTION_COUNT = 5


def get_max_selection_count() -> int:
    """Текущий лимит количества категорий в выборе (из настроек)."""
    return _get_max_selection_count()


def get_selection_settings() -> dict:
    """Возвращает текущие настройки выбора категорий."""
    return {
        "all_categories": get_all_categories(),
        "max_selection_count": get_max_selection_count(),
    }


def update_selection_settings(
    *,
    all_categories: int | None = None,
    max_selection_count: int | None = None,
) -> dict:
    """Обновляет настройки выбора и возвращает актуальные значения."""
    cfg = load_categories_config()
    if all_categories is not None:
        cfg["all_categories"] = int(all_categories)
    if max_selection_count is not None:
        cfg["max_selection_count"] = max_selection_count
    save_categories_config(cfg)
    return get_selection_settings()


def get_selection_submit_items(user_id: int, category_ids: list[str]) -> list[dict]:
    """
    Возвращает элементы для ответа подтверждения выбора по выбранным category_ids.
    Берёт данные из кэша offers/run в порядке category_ids.
    """
    cached = calc_fns.get_offers_run_cache(user_id)
    if not cached:
        return []
    id_to_item = {str(it["category_id"]): it for it in cached}
    result = []
    for cid in category_ids:
        it = id_to_item.get(cid)
        if it is not None:
            result.append({
                "category_id": str(it["category_id"]),
                "cashback": it.get("cashback"),
                "estimated_spend": it.get("estimated_spend"),
                "name": it.get("name"),
                "subtitle": it.get("subtitle"),
            })
    return result


async def get_current_category_ids(user_id: int) -> list[str] | None:
    """
    Возвращает список category_id выбранных категорий пользователя (только id, в порядке записей).
    None, если у пользователя нет выбора.
    """
    async with Database() as db:
        rows = (
            await db.execute_all(
                "SELECT category_id FROM selections WHERE user_id = $1::bigint ORDER BY created_at",
                (user_id,),
            )
            or []
        )
    if not rows:
        return None
    return [str(r["category_id"]) for r in rows]


async def check_categories_exist(category_ids: list[str]) -> bool:
    """Проверяет, что все category_id существуют в categories."""
    if not category_ids:
        return False
    async with Database() as db:
        placeholders = ", ".join(f"${i + 1}" for i in range(len(category_ids)))
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
