from aiohttp import web
from aiohttp_apispec import docs

from api import validate
from config import logger
from database.database import Database
from docs import schems as sh


@docs(
    tags=["Cashback Admin"],
    summary="Журнал аудита",
    description="Возвращает список событий аудита по изменениям категорий и связанным действиям в админке.",
    responses={
        200: {"description": "Журнал аудита получен", "schema": sh.AuditListResponseSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "query",
            "name": "entity_type",
            "schema": {"type": "string"},
            "required": False,
            "description": "Фильтр по типу сущности",
        },
        {
            "in": "query",
            "name": "entity_id",
            "schema": {"type": "string"},
            "required": False,
            "description": "Фильтр по идентификатору сущности",
        },
        {
            "in": "query",
            "name": "action",
            "schema": {"type": "string"},
            "required": False,
            "description": "Фильтр по действию",
        },
        {
            "in": "query",
            "name": "limit",
            "schema": {"type": "integer", "default": 50},
            "required": False,
            "description": "Максимальное количество событий в ответе",
        },
    ],
)
@validate.validate(validate.Audit_list)
async def list_audit(request: web.Request, parsed: validate.Audit_list) -> web.Response:
    try:
        async with Database() as db:
            if db is None:
                return validate.format_500_error(request)

            limit = parsed.limit or 50
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
                (
                    parsed.entity_type,
                    parsed.entity_id,
                    parsed.action,
                    limit,
                ),
            ) or []

        items = [
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
        return web.json_response({"items": items, "total": len(items)}, status=200)
    except Exception:
        logger.exception("list_audit handler failed")
        return validate.format_500_error(request)
