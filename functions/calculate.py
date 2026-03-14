"""Расчёт списка категорий/выборов для клиента по user_id."""

from database.database import Database
from core import serialize_json
import requests
from core import (
    get_all_categories,
)

async def get_calculate_items(user_id: int) -> list[dict]:
    async with Database() as db:
        sql = """
            SELECT
                s.selection_id,
                s.category_id,
                c.name,
                c.subtitle,
                c.rate_min,
                c.rate_max
            FROM selections s
            JOIN categories c ON c.category_id = s.category_id
            WHERE s.user_id = $1::bigint
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
                rate_min,
                rate_max
            FROM categories LIMIT $1
        """
        rows = await db.execute_all(sql, (get_all_categories(),)) or []

    items = []
    for row in rows:
        items.append(
            {
                "selection_id": None,
                "category_id": str(row["category_id"]),
                "name": row["name"],
                "subtitle": row["subtitle"],
                "rate": {"min": row["rate_min"], "max": row["rate_max"]},
                "expected_benefit_amount": None,
                "availability_status": "available",
                "availability_reason": None,
            }
        )
    return serialize_json(items)


def _rows_to_items(rows: list) -> list[dict]:
    items = []
    for row in rows:
        items.append(
            {
                "selection_id": str(row["selection_id"]),
                "category_id": str(row["category_id"]),
                "name": row["name"],
                "subtitle": row["subtitle"],
                "rate": {"min": row["rate_min"], "max": row["rate_max"]},
                "expected_benefit_amount": None,
                "availability_status": "available",
                "availability_reason": None,
            }
        )
    return items
