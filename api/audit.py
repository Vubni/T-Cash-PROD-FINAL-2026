from aiohttp import web
from aiohttp_apispec import docs

from api import validate
from config import logger
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
        items = [
            {
                "id": "audit_001",
                "entity_type": parsed.entity_type or "category",
                "entity_id": parsed.entity_id or "cat_restaurants",
                "action": parsed.action or "update",
                "actor": "admin@example.com",
                "created_at": "2026-03-13T10:00:00Z",
            }
        ]
        return web.json_response({"items": items, "total": len(items)}, status=200)
    except Exception as e:
        logger.error("list_audit error: ", e)
        return validate.format_500_error(request)
