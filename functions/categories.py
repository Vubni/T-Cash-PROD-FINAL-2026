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
    return {
        "id": str(item["category_id"]),
        "name": item["name"],
        "subtitle": item["subtitle"],
        "icon_path": item.get("icon_path"),
        "budget": {"amount": item["budget_amount"]},
        "rate": {"min": item["rate_min"], "max": item["rate_max"]},
        "status": item.get("status") or "running",
        "rule": _rule_from_row(item),
        "history": [],
    }


def row_to_category_list_item(item: dict) -> dict:
    return {
        "id": str(item["category_id"]),
        "name": item["name"],
        "subtitle": item["subtitle"],
        "icon_path": item.get("icon_path"),
        "budget": {"amount": item["budget_amount"]},
        "rate": {"min": item["rate_min"], "max": item["rate_max"]},
        "status": item.get("status") or "running",
    }


_CATEGORY_SELECT_FIELDS = """
    c.category_id,
    c.name,
    c.subtitle,
    c.icon_path,
    c.budget_amount,
    c.rate_min,
    c.rate_max,
    c.rule_id,
    c.status,
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
    name: str,
    subtitle: str,
    budget_amount: int,
    rate_min: int,
    rate_max: int,
) -> dict | None:
    async with Database() as db:
        sql = """
            INSERT INTO categories (
                name, subtitle,
                budget_amount, rate_min, rate_max
            )
            VALUES ($1, $2, $3, $4, $5)
            RETURNING category_id
        """
        category_id = await db.fetchval(
            sql,
            (name, subtitle, budget_amount, rate_min, rate_max),
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
    icon_path: str | None = None,
    budget_amount: int | None = None,
    rate_min: int | None = None,
    rate_max: int | None = None,
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
    add("icon_path", icon_path)
    add("budget_amount", budget_amount)
    add("rate_min", rate_min)
    add("rate_max", rate_max)
    add("rule_id", rule_id)

    if not fields:
        return await get_category(category_id)

    async with Database() as db:
        fields.append("updated_at = NOW()")
        params.append(category_id)
        sql_update = f"UPDATE categories SET {', '.join(fields)} WHERE category_id = ${len(params)}"
        await db.execute(sql_update, tuple(params))
        return await _get_category(db, category_id)


async def update_category_status(category_id: str, status: str) -> dict | None:
    """
    Обновляет только статус категории.
    Возможные значения: running, paused, archived.
    """
    async with Database() as db:
        sql_update = """
            UPDATE categories
            SET status = $1, updated_at = NOW()
            WHERE category_id = $2
        """
        await db.execute(sql_update, (status, category_id))
        return await _get_category(db, category_id)
