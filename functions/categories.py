
from uuid import uuid4

from database.database import Database
from functions.rate import calc_rate


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
    rate = calc_rate(budget_amount=item.get("budget_amount") or 0)
    return {
        "id": str(item["category_id"]),
        "name": item["name"],
        "subtitle": item["subtitle"],
        "budget": {"amount": item["budget_amount"]},
        "rate": rate,
        "audience": {
            "segments": item["audience_segments"],
        },
        "rule": _rule_from_row(item),
        "history": [],
    }


def row_to_category_list_item(item: dict) -> dict:
    rate = calc_rate(budget_amount=item.get("budget_amount") or 0)
    return {
        "id": str(item["category_id"]),
        "name": item["name"],
        "subtitle": item["subtitle"],
        "budget": {"amount": item["budget_amount"]},
        "rate": rate,
    }


_CATEGORY_SELECT_FIELDS = """
    c.category_id,
    c.name,
    c.subtitle,
    c.budget_amount,
    c.audience_segments,
    c.rule_id,
    r.min_age,
    r.max_age,
    r.gender,
    r.income
"""
_CATEGORY_FROM_JOIN = "FROM categories c LEFT JOIN rules r ON r.rule_id = c.rule_id"


async def list_categories(offset: int, limit: int) -> tuple[list[dict], int]:
    async with Database() as db:
        count_sql = "SELECT COUNT(*) AS n FROM categories"
        row_count = await db.execute(count_sql, ())
        total = row_count["n"] if row_count else 0

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
    *,
    category_id: str | None,
    name: str,
    subtitle: str,
    budget_amount: int,
    audience_segments: list,
    rule_id: str,
) -> dict | None:
    if not category_id:
        category_id = str(uuid4())
    async with Database() as db:
        sql = """
            INSERT INTO categories (
                category_id, name, subtitle, icon_key,
                budget_amount, audience_segments, rule_id
            )
            VALUES ($1, $2, $3, '', $4, $5, $6)
        """
        await db.execute(
            sql,
            (
                category_id,
                name,
                subtitle,
                budget_amount,
                audience_segments,
                rule_id,
            ),
        )
        return await _get_category(db, category_id)


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
    budget_amount: int | None = None,
    audience_segments: list | None = None,
    rule_id: str | None = None,
) -> dict | None:
    fields = []
    params = []

    def add(field_name: str, value):
        if value is not None:
            params.append(value)
            fields.append(f"{field_name} = ${len(params)}")

    add("name", name)
    add("subtitle", subtitle)
    add("budget_amount", budget_amount)
    add("audience_segments", audience_segments)
    add("rule_id", rule_id)

    if not fields:
        return await get_category(category_id)

    async with Database() as db:
        fields.append("updated_at = NOW()")
        params.append(category_id)
        sql_update = f"UPDATE categories SET {', '.join(fields)} WHERE category_id = ${len(params)}"
        await db.execute(sql_update, tuple(params))
        return await _get_category(db, category_id)
