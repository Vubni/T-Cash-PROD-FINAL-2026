"""CRUD для правил отбора: возраст (мин/макс), пол, заработок."""

from uuid import uuid4

from database.database import Database

_RULE_SELECT = """
    rule_id,
    min_age,
    max_age,
    gender,
    income
"""


def row_to_rule(row: dict) -> dict:
    return {
        "rule_id": str(row["rule_id"]),
        "min_age": row["min_age"],
        "max_age": row["max_age"],
        "gender": row["gender"],
        "income": row["income"],
    }


async def list_rules(offset: int, limit: int) -> tuple[list[dict], int]:
    async with Database() as db:
        count_sql = "SELECT COUNT(*) AS n FROM rules"
        row_count = await db.execute(count_sql, ())
        total = row_count["n"] if row_count else 0
        sql = f"""
            SELECT {_RULE_SELECT}
            FROM rules
            ORDER BY created_at DESC, rule_id
            OFFSET $1 LIMIT $2
        """
        rows = await db.execute_all(sql, (offset, limit)) or []
        return [row_to_rule(r) for r in rows], total


async def get_rule(rule_id: str) -> dict | None:
    async with Database() as db:
        sql = f"SELECT {_RULE_SELECT} FROM rules WHERE rule_id = $1"
        row = await db.execute(sql, (rule_id,))
        if row is None:
            return None
        return row_to_rule(row)


async def create_rule(
    *,
    rule_id: str | None,
    min_age: int | None = None,
    max_age: int | None = None,
    gender: str | None = None,
    income: int | None = None,
) -> dict | None:
    if not rule_id or not rule_id.strip():
        rule_id = str(uuid4())
    async with Database() as db:
        sql = """
            INSERT INTO rules (rule_id, min_age, max_age, gender, income)
            VALUES ($1, $2, $3, $4, $5)
        """
        await db.execute(sql, (rule_id, min_age, max_age, gender, income))
        return await get_rule(rule_id)


async def update_rule(
    rule_id: str,
    *,
    min_age: int | None = None,
    max_age: int | None = None,
    gender: str | None = None,
    income: int | None = None,
) -> dict | None:
    fields = []
    params = []

    def add(field: str, value):
        if value is not None:
            params.append(value)
            fields.append(f"{field} = ${len(params)}")

    add("min_age", min_age)
    add("max_age", max_age)
    add("gender", gender)
    add("income", income)

    if not fields:
        return await get_rule(rule_id)

    async with Database() as db:
        fields.append("updated_at = NOW()")
        params.append(rule_id)
        sql = f"UPDATE rules SET {', '.join(fields)} WHERE rule_id = ${len(params)}"
        await db.execute(sql, tuple(params))
        return await get_rule(rule_id)
