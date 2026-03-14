from aiohttp import web
from aiohttp.client_exceptions import ClientConnectorError
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

    @field_validator("user_id", mode="before")
    @classmethod
    def user_id_bigint(cls, v: str | int) -> int:
        return validate.validate_user_id(v, "user_id")


@docs(
    tags=["Client"],
    summary="Рассчитать категории для пользователя",
    description="По переданному в теле запроса user_id (BIGINT) возвращает категории/выборы для этого пользователя. На фронте — выбор пользователя без пароля. В теле: **обязательное** — user_id.",
    responses={
        200: {"description": "Список категорий рассчитан", "schema": sh.CalculateResponseSchema},
        404: {"description": "Пользователь не найден", "schema": sh.HttpErrorSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
)
@request_schema(sh.CalculateRequestSchema)
@validate.validate(Client_calculate)
async def calculate(request: web.Request, parsed: Client_calculate) -> web.Response:
    try:
        user_id = parsed.user_id

        if not await users_fns.user_exists(user_id):
            return validate.format_404_error(request, message="Пользователь не найден")

        items = await calc_fns.get_calculate_items(user_id)
        return web.json_response({"items": items}, status=200)
    except (ClientConnectorError, ConnectionRefusedError, OSError) as e:
        logger.warning("calculate: external service unreachable: %s", e)
        return validate.format_500_error(request)
    except Exception:
        logger.exception("calculate handler failed")
        return validate.format_500_error(request)
