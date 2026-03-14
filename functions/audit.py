"""Журнал аудита: чтение записей из БД."""
from database.database import Database


async def list_audit(
    entity_type: str | None,
    entity_id: str | None,
    action: str | None,
    limit: int,
) -> list[dict]:
    """Возвращает список записей аудита с фильтрами."""
    async with Database() as db:
        sql = """
            SELECT
                id,
                entity_type,
                entity_id,
                action,
                actor,
                created_at
            FROM audit_log
            WHERE ($1::text IS NULL OR entity_type = $1)
              AND ($2::text IS NULL OR entity_id = $2)
              AND ($3::text IS NULL OR action = $3)
            ORDER BY created_at DESC, id DESC
            LIMIT $4
        """
        rows = await db.execute_all(
            sql,
            (entity_type, entity_id, action, limit),
        ) or []
    return [
        {
            "id": row["id"],
            "entity_type": row["entity_type"],
            "entity_id": row["entity_id"],
            "action": row["action"],
            "actor": row["actor"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
