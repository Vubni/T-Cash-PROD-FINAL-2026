"""Журнал аудита: чтение и запись записей в БД."""
import json
from config import logger
from database.database import Database

AUDIT_ENTITY_TYPE_MAX = 50
AUDIT_ENTITY_ID_MAX = 64
AUDIT_ACTION_MAX = 50
AUDIT_ACTOR_MAX = 255


def _check_audit_field(value: str, name: str, max_len: int) -> None:
    if not value or not value.strip():
        raise ValueError(f"audit {name} cannot be empty")
    if len(value) > max_len:
        raise ValueError(f"audit {name} cannot exceed {max_len} characters")


async def write_audit(
    entity_type: str,
    entity_id: str,
    action: str,
    actor: str,
    details: dict | None = None,
) -> None:
    """Пишет одну запись в audit_log (действия клиента или админа). Не бросает исключений."""
    try:
        _check_audit_field(entity_type, "entity_type", AUDIT_ENTITY_TYPE_MAX)
        _check_audit_field(entity_id, "entity_id", AUDIT_ENTITY_ID_MAX)
        _check_audit_field(action, "action", AUDIT_ACTION_MAX)
        _check_audit_field(actor, "actor", AUDIT_ACTOR_MAX)
        details_json = json.dumps(details) if details is not None else None
        async with Database() as db:
            await db.execute(
                """
                INSERT INTO audit_log (entity_type, entity_id, action, actor, details)
                VALUES ($1, $2, $3, $4, $5::jsonb)
                """,
                (entity_type, entity_id, action, actor, details_json),
            )
    except ValueError:
        raise
    except Exception as e:
        logger.warning("Ошибка записи в audit_log: %s", e)


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
