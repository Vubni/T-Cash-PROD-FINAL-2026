"""CRUD для правил отбора: возраст (мин/макс), пол, заработок."""

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


async def get_rule(rule_id: str) -> dict | None:
    async with Database() as db:
        sql = f"SELECT {_RULE_SELECT} FROM rules WHERE rule_id = $1"
        row = await db.execute(sql, (rule_id,))
        if row is None:
            return None
        return row_to_rule(row)


async def create_rule(
    min_age: int | None = None,
    max_age: int | None = None,
    gender: str | None = None,
    income: int | None = None,
) -> dict | None:
    async with Database() as db:
        sql = """
            INSERT INTO rules (min_age, max_age, gender, income)
            VALUES ($1, $2, $3, $4)
            RETURNING rule_id
        """
        rule_id = await db.fetchval(sql, (min_age, max_age, gender, income))
        if rule_id is None:
            return None
        rule_id = str(rule_id)
        row = await db.execute(f"SELECT {_RULE_SELECT} FROM rules WHERE rule_id = $1", (rule_id,))
        if row is None:
            return None
        return row_to_rule(row)


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


async def delete_rule(rule_id: str) -> bool:
    """Удаляет правило по rule_id. Сначала обнуляет rule_id во всех категориях, затем удаляет правило. Возвращает True если удалено."""
    async with Database() as db:
        await db.execute(
            "UPDATE categories SET rule_id = NULL, updated_at = NOW() WHERE rule_id = $1",
            (rule_id,),
        )
        await db.execute("DELETE FROM rules WHERE rule_id = $1", (rule_id,))
        return True
