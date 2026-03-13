from aiohttp import web
from aiohttp_apispec import docs

from api import validate
from config import logger
from docs import schems as sh
from functions import audit as audit_fns


@docs(
    tags=["Admin"],
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
        limit = parsed.limit or 50
        items = await audit_fns.list_audit(
            parsed.entity_type,
            parsed.entity_id,
            parsed.action,
            limit,
        )
        return web.json_response({"items": items, "total": len(items)}, status=200)
    except Exception:
        logger.exception("list_audit handler failed")
        return validate.format_500_error(request)
