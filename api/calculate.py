from aiohttp import web
from aiohttp_apispec import docs
from pydantic import BaseModel, field_validator

from api import validate
from config import logger
from docs import schems as sh
from functions import audit as audit_fns
from functions import calculate as calc_fns
from functions import users as users_fns


class Client_calculate(BaseModel):
    model_config = {"extra": "forbid"}

    user_id: str

    @field_validator("user_id")
    @classmethod
    def user_id_uuid(cls, v: str) -> str:
        return validate.validate_uuid(v, "user_id")


@docs(
    tags=["Client"],
    summary="Рассчитать категории для пользователя",
    description="По переданному в теле запроса user_id (UUID) возвращает категории/выборы для этого пользователя. На фронте — выбор пользователя без пароля. В теле: **обязательное** — user_id.",
    responses={
        200: {"description": "Список категорий рассчитан", "schema": sh.CalculateResponseSchema},
        404: {"description": "Пользователь не найден", "schema": sh.HttpErrorSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "body",
            "name": "user_id",
            "type": "string",
            "format": "uuid",
            "required": True,
            "description": "ID пользователя (UUID)",
        },
    ],
)
@validate.validate(Client_calculate)
async def calculate(request: web.Request, parsed: Client_calculate) -> web.Response:
    try:
        user_id = parsed.user_id

        if not await users_fns.user_exists(user_id):
            return validate.format_404_error(request, message="Пользователь не найден")

        items = await calc_fns.get_calculate_items(user_id)
        await audit_fns.write_audit(
            entity_type="client",
            entity_id=str(user_id),
            action="calculate",
            actor=str(user_id),
            details={"items_count": len(items)},
        )
        for it in items:
            it["category_id"] = str(it["category_id"])
            if it.get("selection_id") is not None:
                it["selection_id"] = str(it["selection_id"])
        return web.json_response(
            {"user_id": str(user_id), "items": items},
            status=200,
        )
    except Exception:
        logger.exception("calculate handler failed")
        return validate.format_500_error(request)
