"""API запуска офферов для клиента (offers/run)."""

from aiohttp import web
from aiohttp_apispec import docs, request_schema
from pydantic import BaseModel, field_validator

from api import validate
from config import logger
from docs import schems as sh
from functions import calculate as calc_fns
from functions import users as users_fns


class OffersRunBody(BaseModel):
    model_config = {"extra": "forbid"}
    user_id: int

    @field_validator("user_id", mode="before")
    @classmethod
    def user_id_bigint(cls, v):
        return validate.validate_user_id(v, "user_id")


@docs(
    tags=["Client"],
    summary="Запуск офферов",
    description="Запускает расчёт офферов для клиента. Сервер гарантирует диапазоны ставок, лимиты и проверку бюджетных инвариантов.",
    responses={
        200: {"description": "Список офферов", "schema": sh.CalculateResponseSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
)
@request_schema(sh.CalculateRequestSchema)
@validate.validate(OffersRunBody)
async def run_offers(request: web.Request, parsed: OffersRunBody) -> web.Response:
    try:
        user_id = parsed.user_id
        if not await users_fns.user_exists(user_id):
            return validate.format_404_error(request, message="Пользователь не найден")
        items = await calc_fns.get_calculate_items(user_id)
        return web.json_response({"items": items}, status=200)
    except Exception:
        logger.exception("run_offers handler failed")
        return validate.format_500_error(request)
