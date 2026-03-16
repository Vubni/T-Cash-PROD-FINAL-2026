import uuid
import hashlib
import json

from core import (
    get_all_categories,
    get_max_selection_count as _get_max_selection_count,
    load_categories_config,
    save_categories_config,
)
from database.database import Database

from functions import calculate as calc_fns

REQUIRED_SELECTION_COUNT = 5
IDEMPOTENCY_KEY_MAX_LENGTH = 128


class IdempotencyConflictError(Exception):
    """Один и тот же Idempotency-Key был использован с другим payload."""


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


def normalize_idempotency_key(idempotency_key: str | None) -> str | None:
    """Нормализует значение заголовка Idempotency-Key или возвращает None, если заголовок не передан."""
    if idempotency_key is None:
        return None
    normalized = str(idempotency_key).strip()
    if not normalized:
        raise ValueError("Idempotency-Key не может быть пустым")
    if len(normalized) > IDEMPOTENCY_KEY_MAX_LENGTH:
        raise ValueError(f"Idempotency-Key не должен быть длиннее {IDEMPOTENCY_KEY_MAX_LENGTH} символов")
    return normalized


def _build_selection_response(user_id: int, category_ids: list[str]) -> dict:
    return {
        "user_id": user_id,
        "category_ids": category_ids,
        "items": get_selection_submit_items(user_id, category_ids),
    }


def _build_request_hash(user_id: int, category_ids: list[str]) -> str:
    payload = {"user_id": user_id, "category_ids": category_ids}
    canonical_payload = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


async def _get_current_category_ids_db(db: Database, user_id: int) -> list[str] | None:
    """Возвращает текущий выбор пользователя в рамках уже открытой транзакции."""
    rows = (
        await db.execute_all(
            "SELECT category_id FROM selections WHERE user_id = $1::bigint ORDER BY created_at, selection_id",
            (user_id,),
        )
        or []
    )
    if not rows:
        return None
    return [str(r["category_id"]) for r in rows]


async def get_current_category_ids(user_id: int) -> list[str] | None:
    """
    Возвращает список category_id выбранных категорий пользователя (только id, в порядке записей).
    None, если у пользователя нет выбора.
    """
    async with Database() as db:
        return await _get_current_category_ids_db(db, user_id)


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


async def _save_selection_batch_db(
    db: Database,
    user_id: int,
    category_ids: list[str],
    idempotency_key: str | None = None,
) -> list[str]:
    """Перезаписывает выбор пользователя в рамках уже открытой транзакции."""
    created_ids = []
    cached = calc_fns.get_offers_run_cache(user_id) or []
    cached_by_id = {str(it.get("category_id")): it for it in cached}
    await db.execute("DELETE FROM selections WHERE user_id = $1::bigint", (user_id,))
    for cat_id in category_ids:
        sel_id = _generate_selection_uuid()
        cached_item = cached_by_id.get(str(cat_id)) or {}
        cashback = cached_item.get("cashback")
        estimated_spend = cached_item.get("estimated_spend")
        await db.execute(
            """
            INSERT INTO selections (
                selection_id,
                user_id,
                category_id,
                cashback,
                estimated_spend,
                idempotency_key
            )
            VALUES ($1, $2::bigint, $3, $4, $5, $6)
            """,
            (sel_id, user_id, cat_id, cashback, estimated_spend, idempotency_key),
        )
        created_ids.append(sel_id)
    return created_ids


async def save_selection_batch(user_id: int, category_ids: list[str], idempotency_key: str | None = None) -> list[str]:
    """
    Сохраняет ровно N категорий в selections для пользователя.
    Старые записи по user_id удаляются, вставляются новые.
    Возвращает список созданных selection_id (UUID строк).
    """
    async with Database() as db:
        return await _save_selection_batch_db(db, user_id, category_ids, idempotency_key=idempotency_key)


async def confirm_selection(
    user_id: int,
    category_ids: list[str],
    *,
    idempotency_key: str | None = None,
) -> tuple[dict, int]:
    """
    Подтверждает выбор пользователя.

    Если передан Idempotency-Key, повторный запрос с тем же ключом и тем же payload
    вернёт ровно сохранённый ранее ответ. Тот же ключ с другим payload приводит к 409.
    """
    response_body = _build_selection_response(user_id, category_ids)
    if idempotency_key is None:
        current = await get_current_category_ids(user_id)
        if current is not None and len(current) == len(category_ids) and set(current) == set(category_ids):
            return response_body, 200
        await save_selection_batch(user_id, category_ids)
        return response_body, 200

    request_hash = _build_request_hash(user_id, category_ids)

    async with Database() as db:
        await db.execute("SELECT pg_advisory_xact_lock($1::bigint)", (user_id,))
        existing_request = await db.execute(
            """
            SELECT request_hash, response_body, status_code
            FROM selection_idempotency_requests
            WHERE user_id = $1::bigint AND idempotency_key = $2
            """,
            (user_id, idempotency_key),
        )
        if existing_request is not None:
            if existing_request["request_hash"] != request_hash:
                raise IdempotencyConflictError
            return existing_request["response_body"], int(existing_request.get("status_code") or 200)

        current = await _get_current_category_ids_db(db, user_id)
        if current is None or len(current) != len(category_ids) or set(current) != set(category_ids):
            await _save_selection_batch_db(db, user_id, category_ids, idempotency_key=idempotency_key)

        await db.execute(
            """
            INSERT INTO selection_idempotency_requests (
                user_id,
                idempotency_key,
                request_hash,
                response_body,
                status_code
            )
            VALUES ($1::bigint, $2, $3, $4::jsonb, $5::int)
            """,
            (user_id, idempotency_key, request_hash, json.dumps(response_body, ensure_ascii=False), 200),
        )
        return response_body, 200
