import hashlib
import json

from asyncpg import UniqueViolationError

from database.database import Database

def _rule_from_row(item: dict) -> dict:
    r = item.get("rule_id")
    return {
        "rule_id": str(r) if r is not None else None,
        "min_age": item.get("min_age"),
        "max_age": item.get("max_age"),
        "gender": item.get("gender"),
        "income": item.get("income"),
    }


def row_to_category(item: dict) -> dict:
    has_rule = item.get("rule_id") is not None
    return {
        "id": str(item["category_id"]),
        "name": item["name"],
        "subtitle": item["subtitle"],
        "icon_url": item.get("icon_url"),
        "budget": {"amount": item["budget_amount"]},
        "rate": {"min": item["rate_min"], "max": item["rate_max"]},
        "status": item.get("status") or "running",
        "avg_cashback_percent": float(item["avg_cashback_percent"]) if item.get("avg_cashback_percent") is not None else None,
        "rule": _rule_from_row(item) if has_rule else None,
        "history": [],
    }


def row_to_category_list_item(item: dict) -> dict:
    return {
        "id": str(item["category_id"]),
        "name": item["name"],
        "subtitle": item["subtitle"],
        "icon_url": item.get("icon_url"),
        "budget": {"amount": item["budget_amount"]},
        "rate": {"min": item["rate_min"], "max": item["rate_max"]},
        "status": item.get("status") or "running",
        "avg_cashback_percent": float(item["avg_cashback_percent"]) if item.get("avg_cashback_percent") is not None else None,
    }


_CATEGORY_SELECT_FIELDS = """
    c.category_id,
    c.name,
    c.subtitle,
    c.icon_url,
    c.budget_amount,
    c.rate_min,
    c.rate_max,
    c.rule_id,
    c.status,
    r.min_age,
    r.max_age,
    r.gender,
    r.income,
    stats.avg_cashback_percent
"""
_CATEGORY_FROM_JOIN = """
FROM categories c
LEFT JOIN rules r ON r.rule_id = c.rule_id
LEFT JOIN LATERAL (
    SELECT
        AVG(
            (s.cashback::numeric * 100.0) / NULLIF(s.estimated_spend, 0)
        ) AS avg_cashback_percent
    FROM selections s
    WHERE
        s.category_id = c.category_id
        AND s.cashback IS NOT NULL
        AND s.estimated_spend IS NOT NULL
        AND s.estimated_spend > 0
) stats ON TRUE
"""

IDEMPOTENCY_KEY_MAX_LENGTH = 128


class DuplicateCategoryNameError(Exception):
    """Категория с таким названием уже существует."""


class CategoryIdempotencyConflictError(Exception):
    """Один и тот же Idempotency-Key использован с другим payload."""


def normalize_idempotency_key(idempotency_key: str | None) -> str | None:
    if idempotency_key is None:
        return None
    normalized = str(idempotency_key).strip()
    if not normalized:
        raise ValueError("Idempotency-Key не может быть пустым")
    if len(normalized) > IDEMPOTENCY_KEY_MAX_LENGTH:
        raise ValueError(f"Idempotency-Key не должен быть длиннее {IDEMPOTENCY_KEY_MAX_LENGTH} символов")
    return normalized


def _build_create_category_request_hash(
    name: str,
    subtitle: str,
    budget_amount: int,
    rate_min: int,
    rate_max: int,
    icon_url: str | None,
) -> str:
    payload = {
        "name": name,
        "subtitle": subtitle,
        "budget_amount": budget_amount,
        "rate_min": rate_min,
        "rate_max": rate_max,
        "icon_url": icon_url,
    }
    canonical_payload = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


async def list_categories(offset: int, limit: int, status: str | None = None) -> tuple[list[dict], int]:
    async with Database() as db:
        if status is not None:
            count_sql = "SELECT COUNT(*) AS n FROM categories WHERE status = $1"
            row_count = await db.execute(count_sql, (status,))
        else:
            count_sql = "SELECT COUNT(*) AS n FROM categories"
            row_count = await db.execute(count_sql, ())
        total = row_count["n"] if row_count else 0

        if status is not None:
            sql = f"""
                SELECT {_CATEGORY_SELECT_FIELDS}
                {_CATEGORY_FROM_JOIN}
                WHERE c.status = $1
                ORDER BY c.created_at DESC, c.category_id
                OFFSET $2 LIMIT $3
            """
            rows = await db.execute_all(sql, (status, offset, limit)) or []
        else:
            sql = f"""
                SELECT {_CATEGORY_SELECT_FIELDS}
                {_CATEGORY_FROM_JOIN}
                ORDER BY c.created_at DESC, c.category_id
                OFFSET $1 LIMIT $2
            """
            rows = await db.execute_all(sql, (offset, limit)) or []
        items = [row_to_category_list_item(row) for row in rows]
        return items, total


async def create_category(
    admin_id: int,
    name: str,
    subtitle: str,
    budget_amount: int,
    rate_min: int,
    rate_max: int,
    icon_url: str | None = None,
    idempotency_key: str | None = None,
) -> tuple[dict | None, bool]:
    request_hash = _build_create_category_request_hash(
        name,
        subtitle,
        budget_amount,
        rate_min,
        rate_max,
        icon_url,
    )

    async with Database() as db:
        if idempotency_key is not None:
            await db.execute("SELECT pg_advisory_xact_lock($1::bigint)", (admin_id,))
            existing_request = await db.execute(
                """
                SELECT request_hash, response_body
                FROM category_creation_idempotency_requests
                WHERE admin_id = $1 AND idempotency_key = $2
                """,
                (admin_id, idempotency_key),
            )
            if existing_request is not None:
                if existing_request["request_hash"] != request_hash:
                    raise CategoryIdempotencyConflictError
                return existing_request["response_body"], False

        sql = """
            INSERT INTO categories (
                name, subtitle, icon_url,
                budget_amount, rate_min, rate_max
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING category_id
        """
        try:
            category_id = await db.fetchval(
                sql,
                (name, subtitle, icon_url, budget_amount, rate_min, rate_max),
            )
        except UniqueViolationError as exc:
            raise DuplicateCategoryNameError("Категория с таким названием уже существует") from exc

        if category_id is None:
            return None, False

        response = await _get_category(db, category_id)
        if response is None:
            return None, False

        if idempotency_key is not None:
            await db.execute(
                """
                INSERT INTO category_creation_idempotency_requests (
                    admin_id,
                    idempotency_key,
                    request_hash,
                    response_body,
                    status_code
                )
                VALUES ($1, $2, $3, $4::jsonb, $5)
                """,
                (admin_id, idempotency_key, request_hash, json.dumps(response, ensure_ascii=False), 201),
            )
        return response, True


async def get_category(category_id: str) -> dict | None:
    async with Database() as db:
        return await _get_category(db, category_id)


async def _get_category(db: Database, category_id: str) -> dict | None:
    sql = f"""
        SELECT {_CATEGORY_SELECT_FIELDS}
        {_CATEGORY_FROM_JOIN}
        WHERE c.category_id = $1
    """
    row = await db.execute(sql, (category_id,))
    if row is None:
        return None
    return row_to_category(row)


async def update_category(
    category_id: str,
    *,
    name: str | None = None,
    subtitle: str | None = None,
    icon_url: str | None = None,
    budget_amount: int | None = None,
    rate_min: int | None = None,
    rate_max: int | None = None,
    status: str | None = None,
    rule_id: str | None = None,
    _rule_id_set_null: bool = False,
) -> dict | None:
    fields = []
    params = []

    def add(field_name: str, value):
        if value is not None:
            params.append(value)
            fields.append(f"{field_name} = ${len(params)}")

    add("name", name)
    add("subtitle", subtitle)
    add("icon_url", icon_url)
    add("budget_amount", budget_amount)
    add("rate_min", rate_min)
    add("rate_max", rate_max)
    add("status", status)
    if _rule_id_set_null:
        fields.append("rule_id = NULL")
    else:
        add("rule_id", rule_id)

    if not fields and not _rule_id_set_null:
        return await get_category(category_id)

    async with Database() as db:
        fields.append("updated_at = NOW()")
        params.append(category_id)
        sql_update = f"UPDATE categories SET {', '.join(fields)} WHERE category_id = ${len(params)}"
        try:
            await db.execute(sql_update, tuple(params))
        except UniqueViolationError as exc:
            raise DuplicateCategoryNameError("Категория с таким названием уже существует") from exc
        return await _get_category(db, category_id)


_CATEGORY_STATUS_TRANSITIONS = {
    ("running", "running"),
    ("running", "paused"),
    ("running", "archived"),
    ("paused", "running"),
    ("paused", "paused"),
    ("paused", "archived"),
    ("archived", "archived"),
}


async def update_category_status(category_id: str, status: str) -> dict | None:
    """
    Обновляет только статус категории.
    Допустимые значения: running, paused, archived.
    Переход разрешён только если пара (текущий_статус, новый_статус) в _CATEGORY_STATUS_TRANSITIONS.
    """
    async with Database() as db:
        row = await db.execute(
            "SELECT status FROM categories WHERE category_id = $1",
            (category_id,),
        )
        if row is None:
            return None
        current = row["status"]
        if (current or "").lower() == "archived" and status != "archived":
            raise ValueError(
                f"Invalid category status transition: {current!r} -> {status!r}. "
                "Archived categories cannot be restored or changed."
            )
        if (current, status) not in _CATEGORY_STATUS_TRANSITIONS:
            raise ValueError(
                f"Invalid category status transition: {current!r} -> {status!r}. "
                "Allowed transitions: running <-> paused, any -> archived, archived -> archived."
            )
        sql_update = """
            UPDATE categories
            SET status = $1, updated_at = NOW()
            WHERE category_id = $2
        """
        await db.execute(sql_update, (status, category_id))
        return await _get_category(db, category_id)
