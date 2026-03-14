import uuid
from database.database import Database
from functions.rate import calc_rate

REQUIRED_SELECTION_COUNT = 5


def row_to_selection_detail(row: dict) -> dict:
    rate = calc_rate(
        budget_amount=row.get("budget_amount") or 0,
        target_users=row.get("target_users") or 0,
        avg_spend_per_user=row.get("avg_spend_per_user") or 0,
    )
    icon_key = row["icon_key"]
    return {
        "selection_id": row["selection_id"],
        "category_id": str(row["category_id"]),
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


async def check_categories_exist(category_ids: list[str]) -> bool:
    """Проверяет, что все category_id существуют в categories."""
    if not category_ids:
        return False
    async with Database() as db:
        placeholders = ", ".join(f"${i+1}" for i in range(len(category_ids)))
        sql = f"SELECT 1 FROM categories WHERE category_id IN ({placeholders})"
        rows = await db.execute_all(sql, tuple(category_ids)) or []
    return len(rows) == len(category_ids)


def _generate_selection_id() -> str:
    return f"sel_{uuid.uuid4().hex[:12]}"


async def save_selection_batch(user_id: str, category_ids: list[str]) -> list[str]:
    """
    Сохраняет ровно 5 категорий в selections для пользователя.
    Старые записи по user_id удаляются, вставляются 5 новых.
    Возвращает список созданных selection_id.
    """
    created_ids = []
    async with Database() as db:
        await db.execute("DELETE FROM selections WHERE user_id = $1", (user_id,))
        for cat_id in category_ids:
            sel_id = _generate_selection_id()
            await db.execute(
                """
                INSERT INTO selections (selection_id, user_id, category_id)
                VALUES ($1, $2, $3)
                """,
                (sel_id, user_id, cat_id),
            )
            created_ids.append(sel_id)
    return created_ids
