from typing import Optional

from aiohttp import web
from aiohttp_apispec import docs, request_schema
from pydantic import BaseModel, field_validator

from api import validate
from config import logger
from docs import schems as sh
from functions import calculate as calc_fns


@docs(
    tags=["Client"],
    summary="Рассчитать список категорий для клиента",
    description="Возвращает список всех категорий для клиентского экрана. Backend сам решает, вернуть новый расчёт или уже актуальное состояние.",
    responses={
        200: {"description": "Список категорий рассчитан", "schema": sh.CalculateResponseSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
)
@request_schema(sh.CalculateRequestSchema)
async def calculate(request: web.Request) -> web.Response:
    try:
        items = await calc_fns.get_calculate_items()
        return web.json_response({"items": items}, status=200)
    except Exception:
        logger.exception("calculate handler failed")
        return validate.format_500_error(request)
