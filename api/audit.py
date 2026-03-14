from typing import Optional

from aiohttp import web
from aiohttp_apispec import docs
from pydantic import BaseModel, field_validator

from api import validate
from config import logger
from docs import schems as sh
from functions import audit as audit_fns


LIMIT_MAX = 500


class Audit_list(BaseModel):
    model_config = {"extra": "forbid"}

    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    action: Optional[str] = None
    limit: int = 50

    @field_validator("limit")
    @classmethod
    def limit_in_range(cls, v: int) -> int:
        if v < 1 or v > LIMIT_MAX:
            raise ValueError(f"limit must be between 1 and {LIMIT_MAX}")
        return v


@docs(
    tags=["Admin"],
    summary="Журнал аудита",
    description="Возвращает список событий аудита по изменениям категорий и связанным действиям в админке. Требуется JWT админа.",
    security=validate.SECURITY_ADMIN_BEARER,
    responses={
        200: {"description": "Журнал аудита получен", "schema": sh.AuditListResponseSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "query",
            "name": "entity_type",
            "type": "string",
            "required": False,
            "description": "Фильтр по типу сущности",
        },
        {
            "in": "query",
            "name": "entity_id",
            "type": "string",
            "required": False,
            "description": "Фильтр по идентификатору сущности",
        },
        {
            "in": "query",
            "name": "action",
            "type": "string",
            "required": False,
            "description": "Фильтр по действию",
        },
        {
            "in": "query",
            "name": "limit",
            "type": "integer",
            "required": False,
            "description": "Максимальное количество событий в ответе",
        },
    ],
)
@validate.validate(Audit_list, require_admin=True)
async def list_audit(request: web.Request, parsed: Audit_list) -> web.Response:
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
