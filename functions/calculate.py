"""Расчёт списка категорий/выборов для клиента по user_id."""

from database.database import Database
from functions.rate import calc_rate


async def get_calculate_items(user_id: str) -> list[dict]:
    """
    Возвращает для пользователя его выборы (selections) с данными категории.
    Если выборов нет — возвращает все категории как доступные варианты.
    """
    async with Database() as db:
        sql = """
            SELECT
                s.selection_id,
                s.category_id,
                s.expected_benefit_amount,
                s.availability_status,
                s.availability_reason,
                c.name,
                c.subtitle,
                c.icon_key,
                c.budget_amount
            FROM selections s
            JOIN categories c ON c.category_id = s.category_id
            WHERE s.user_id = $1::uuid
        """
        rows = await db.execute_all(sql, (user_id,)) or []

    if rows:
        items = _rows_to_items(rows)
        return items

    async with Database() as db:
        sql = """
            SELECT
                category_id,
                name,
                subtitle,
                icon_key,
                budget_amount
            FROM categories
        """
        rows = await db.execute_all(sql) or []

    items = []
    for row in rows:
        rate = calc_rate(budget_amount=row.get("budget_amount") or 0)
        icon_key = row["icon_key"]
        items.append(
            {
                "selection_id": None,
                "category_id": row["category_id"],
                "name": row["name"],
                "subtitle": row["subtitle"],
                "icon_key": icon_key,
                "icon_url": f"/icons/{icon_key}.svg",
                "rate": rate,
                "expected_benefit_amount": None,
                "availability_status": "available",
                "availability_reason": None,
            }
        )
    return items


def _rows_to_items(rows: list) -> list[dict]:
    items = []
    for row in rows:
        rate = calc_rate(budget_amount=row.get("budget_amount") or 0)
        icon_key = row["icon_key"]
        items.append(
            {
                "selection_id": str(row["selection_id"]),
                "category_id": str(row["category_id"]),
                "name": row["name"],
                "subtitle": row["subtitle"],
                "icon_key": icon_key,
                "icon_url": f"/icons/{icon_key}.svg",
                "rate": rate,
                "expected_benefit_amount": row.get("expected_benefit_amount"),
                "availability_status": row.get("availability_status"),
                "availability_reason": row.get("availability_reason"),
            }
        )
    return items
