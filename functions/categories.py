
from uuid import uuid4

from database.database import Database
from functions.rate import calc_rate


def row_to_category(item: dict) -> dict:
    rate = calc_rate(
        budget_amount=item.get("budget_amount") or 0,
        target_users=item.get("target_users") or 0,
        avg_spend_per_user=item.get("avg_spend_per_user") or 0,
    )
    icon_key = item["icon_key"]
    return {
        "id": item["category_id"],
        "name": item["name"],
        "subtitle": item["subtitle"],
        "icon_key": icon_key,
        "icon_url": f"/icons/{icon_key}.svg",
        "status": item["status"],
        "budget": item["budget_amount"],
        "rate": rate,
        "audience": {
            "segments": item["audience_segments"],
        },
        "rule": {
            "personalized": item["rule_personalized"],
            "budget_mode": item["rule_budget_mode"],
            "fallback_message": item["rule_fallback_message"],
        },
        "history": [],
    }


def row_to_category_list_item(item: dict) -> dict:
    """Элемент списка без status (для list_categories)."""
    rate = calc_rate(
        budget_amount=item.get("budget_amount") or 0,
        target_users=item.get("target_users") or 0,
        avg_spend_per_user=item.get("avg_spend_per_user") or 0,
    )
    icon_key = item["icon_key"]
    return {
        "id": item["category_id"],
        "name": item["name"],
        "subtitle": item["subtitle"],
        "icon_key": icon_key,
        "icon_url": f"/icons/{icon_key}.svg",
        "budget": item["budget_amount"],
        "rate": rate,
    }


_CATEGORY_SELECT_FIELDS = """
    category_id,
    name,
    subtitle,
    icon_key,
    status,
    budget_amount,
    target_users,
    avg_spend_per_user,
    audience_segments,
    rule_personalized,
    rule_budget_mode,
    rule_fallback_message
"""


async def list_categories(offset: int, limit: int) -> tuple[list[dict], int]:
    async with Database() as db:
        count_sql = "SELECT COUNT(*) AS n FROM categories"
        row_count = await db.execute(count_sql, ())
        total = row_count["n"] if row_count else 0

        sql = f"""
            SELECT
                {_CATEGORY_SELECT_FIELDS}
            FROM categories
            ORDER BY created_at DESC, category_id
            OFFSET $1
            LIMIT $2
        """
        rows = await db.execute_all(sql, (offset, limit)) or []
        items = [row_to_category_list_item(row) for row in rows]
        return items, total


async def create_category(
    *,
    category_id: str | None,
    name: str,
    subtitle: str,
    icon_key: str,
    status: str,
    budget_amount: int,
    target_users: int,
    avg_spend_per_user: int,
    audience_segments: list,
    rule_personalized: bool,
    rule_budget_mode: str,
    rule_fallback_message: str,
) -> dict | None:
    if not category_id:
        category_id = f"cat_{uuid4().hex[:8]}"
    async with Database() as db:
        sql = """
            INSERT INTO categories (
                category_id,
                name,
                subtitle,
                icon_key,
                status,
                budget_amount,
                target_users,
                avg_spend_per_user,
                audience_segments,
                rule_personalized,
                rule_budget_mode,
                rule_fallback_message
            )
            VALUES (
                $1, $2, $3, $4, $5,
                $6, $7,
                $8, $9,
                $10,
                $11, $12, $13
            )
        """
        await db.execute(
            sql,
            (
                category_id,
                name,
                subtitle,
                icon_key,
                status,
                budget_amount,
                target_users,
                avg_spend_per_user,
                audience_segments,
                rule_personalized,
                rule_budget_mode,
                rule_fallback_message,
            ),
        )
        return await _get_category(db, category_id)


async def get_category(category_id: str) -> dict | None:
    async with Database() as db:
        return await _get_category(db, category_id)


async def _get_category(db: Database, category_id: str) -> dict | None:
    sql = f"""
        SELECT
            {_CATEGORY_SELECT_FIELDS}
        FROM categories
        WHERE category_id = $1
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
    icon_key: str | None = None,
    status: str | None = None,
    budget_amount: int | None = None,
    target_users: int | None = None,
    avg_spend_per_user: int | None = None,
    audience_segments: list | None = None,
    rule_personalized: bool | None = None,
    rule_budget_mode: str | None = None,
    rule_fallback_message: str | None = None,
) -> dict | None:
    fields = []
    params = []

    def add(field_name: str, value):
        if value is not None:
            params.append(value)
            fields.append(f"{field_name} = ${len(params)}")

    add("name", name)
    add("subtitle", subtitle)
    add("icon_key", icon_key)
    add("status", status)
    add("budget_amount", budget_amount)
    add("target_users", target_users)
    add("avg_spend_per_user", avg_spend_per_user)
    add("audience_segments", audience_segments)
    add("rule_personalized", rule_personalized)
    add("rule_budget_mode", rule_budget_mode)
    add("rule_fallback_message", rule_fallback_message)

    if not fields:
        return await get_category(category_id)

    async with Database() as db:
        fields.append("updated_at = NOW()")
        params.append(category_id)
        sql_update = f"UPDATE categories SET {', '.join(fields)} WHERE category_id = ${len(params)}"
        await db.execute(sql_update, tuple(params))
        return await _get_category(db, category_id)
