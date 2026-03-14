"""API запуска офферов для клиента (offers/run)."""

from aiohttp import web
from aiohttp_apispec import docs, request_schema

from api import validate
from config import logger
from docs import schems as sh
from functions import calculate as calc_fns


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
async def run_offers(request: web.Request) -> web.Response:
    try:
        items = await calc_fns.get_calculate_items()
        return web.json_response({"items": items}, status=200)
    except Exception:
        logger.exception("run_offers handler failed")
        return validate.format_500_error(request)
