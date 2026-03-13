"""Расчёт списка категорий/выборов для клиента (period)."""

from database.database import Database
from functions.rate import calc_rate


async def get_calculate_items(period_id: str) -> list[dict]:
    """
    Возвращает список элементов для ответа calculate: выборы по period_id
    с данными категории и рассчитанной ставкой.
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
                c.budget_amount,
                c.target_users,
                c.avg_spend_per_user
            FROM selections s
            JOIN categories c ON c.category_id = s.category_id
            WHERE s.period_id = $1
        """
        rows = await db.execute_all(sql, (period_id,)) or []
    items = []
    for row in rows:
        rate = calc_rate(
            budget_amount=row.get("budget_amount") or 0,
            target_users=row.get("target_users") or 0,
            avg_spend_per_user=row.get("avg_spend_per_user") or 0,
        )
        icon_key = row["icon_key"]
        items.append(
            {
                "selection_id": row["selection_id"],
                "category_id": row["category_id"],
                "name": row["name"],
                "subtitle": row["subtitle"],
                "icon_key": icon_key,
                "icon_url": f"/icons/{icon_key}.svg",
                "rate": rate,
                "expected_benefit_amount": row["expected_benefit_amount"],
                "availability_status": row["availability_status"],
                "availability_reason": row["availability_reason"],
            }
        )
    return items
