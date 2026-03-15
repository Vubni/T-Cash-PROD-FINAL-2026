from aiohttp import web
from aiohttp_apispec import docs
from pydantic import BaseModel, field_validator

from api import validate
from config import logger
from docs import schemas as sh
from functions import audit as audit_fns


LIMIT_MAX = 500


class Audit_list(BaseModel):
    model_config = {"extra": "forbid"}

    category_id: str
    limit: int = 50

    @field_validator("category_id")
    @classmethod
    def category_id_uuid(cls, v: str) -> str:
        return validate.validate_uuid(v, "category_id")

    @field_validator("limit")
    @classmethod
    def limit_in_range(cls, v: int) -> int:
        if v < 1 or v > LIMIT_MAX:
            raise ValueError(f"limit must be between 1 and {LIMIT_MAX}")
        return v


@docs(
    tags=["Admin"],
    summary="Журнал аудита по категории",
    description=("Возвращает список событий аудита по изменениям конкретной категории. Требуется JWT админа."),
    security=validate.SECURITY_ADMIN_BEARER,
    responses={
        200: {"description": "Журнал аудита получен", "schema": sh.AuditListResponseSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "path",
            "name": "category_id",
            "type": "string",
            "required": True,
            "description": "Идентификатор категории (UUID), для которой нужен журнал аудита.",
        },
        {
            "in": "query",
            "name": "limit",
            "type": "integer",
            "required": False,
            "description": "Максимальное количество событий в ответе. Опционально, по умолчанию 50.",
            "default": 50,
        },
    ],
)
@validate.validate(Audit_list, require_admin=True)
async def list_audit(request: web.Request, parsed: Audit_list) -> web.Response:
    try:
        items = await audit_fns.list_audit(
            entity_type="category",
            entity_id=parsed.category_id,
            action=None,
            limit=parsed.limit,
        )
        return web.json_response({"items": items, "total": len(items)}, status=200)
    except Exception:
        logger.exception("list_audit handler failed")
        return validate.format_500_error(request)
