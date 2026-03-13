
from database.database import Database
from functions.rate import calc_rate


def row_to_selection_detail(row: dict) -> dict:
    rate = calc_rate(
        budget_amount=row.get("budget_amount") or 0,
        target_users=row.get("target_users") or 0,
        avg_spend_per_user=row.get("avg_spend_per_user") or 0,
    )
    icon_key = row["icon_key"]
    return {
        "selection_id": row["selection_id"],
        "category_id": row["category_id"],
        "name": row["name"],
        "subtitle": row["subtitle"],
        "icon_key": icon_key,
        "icon_url": f"/icons/{icon_key}.svg",
        "rate": rate,
        "expected_benefit_amount": row["expected_benefit_amount"], 
        "budget_message": row["availability_reason"],
    }


_SELECTION_JOIN_SQL = """
    SELECT
        s.selection_id,
        s.category_id,
        s.expected_benefit_amount,
        s.status,
        s.availability_reason,
        c.name,
        c.subtitle,
        c.icon_key,
        c.budget_amount,
        c.target_users,
        c.avg_spend_per_user
    FROM selections s
    JOIN categories c ON c.category_id = s.category_id
    WHERE s.selection_id = $1
"""


async def get_selection(selection_id: str) -> dict | None:
    async with Database() as db:
        row = await db.execute(_SELECTION_JOIN_SQL, (selection_id,))
        if row is None:
            return None
        return row_to_selection_detail(row)


async def confirm_selection(
    selection_id: str,
    new_status: str,
    idempotency_key: str | None,
) -> dict | None:
    async with Database() as db:
        sql_update = """
            UPDATE selections
            SET status = $1,
                idempotency_key = COALESCE($2, idempotency_key),
                updated_at = NOW()
            WHERE selection_id = $3
        """
        await db.execute(sql_update, (new_status, idempotency_key, selection_id))
        row = await db.execute(_SELECTION_JOIN_SQL, (selection_id,))
        if row is None:
            return None
        return row_to_selection_detail(row)
