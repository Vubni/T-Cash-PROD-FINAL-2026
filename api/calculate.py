from aiohttp import web
from aiohttp_apispec import docs, request_schema
from pydantic import BaseModel, field_validator

from api import validate
from config import logger
from docs import schems as sh
from functions import calculate as calc_fns
from functions import users as users_fns


class Client_calculate(BaseModel):
    model_config = {"extra": "forbid"}

    user_id: int

    @field_validator("user_id")
    @classmethod
    def user_id_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("user_id должен быть положительным целым числом")
        return v


@docs(
    tags=["Client"],
    summary="Рассчитать категории для пользователя",
    description="По переданному user_id возвращает категории/выборы для этого пользователя. На фронте — выбор пользователя без пароля.",
    responses={
        200: {"description": "Список категорий рассчитан", "schema": sh.CalculateResponseSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "query",
            "name": "user_id",
            "type": "integer",
            "required": True,
            "description": "ID пользователя (BIGINT)",
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
        for it in items:
            it["category_id"] = str(it["category_id"])
            if it.get("selection_id") is not None:
                it["selection_id"] = str(it["selection_id"])
        return web.json_response(
            {"user_id": user_id, "items": items},
            status=200,
        )
    except Exception:
        logger.exception("calculate handler failed")
        return validate.format_500_error(request)
