"""API прогресса клиента по офферам/выборам."""

from aiohttp import web
from aiohttp_apispec import docs

from api import validate
from config import logger
from docs import schems as sh


@docs(
    tags=["Client"],
    summary="Прогресс клиента",
    description="Возвращает прогресс клиента по офферам и подтверждённым выборам. Сервер гарантирует лимиты и актуальность данных.",
    responses={
        200: {"description": "Список прогресса", "schema": sh.ProgressListResponseSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
)
async def get_progress(request: web.Request) -> web.Response:
    try:
        # Заглушка: прогресс пока возвращаем пустым списком.
        # В дальнейшем — выборки по подтверждённым selections и лимитам бюджета.
        return web.json_response({"items": [], "total": 0}, status=200)
    except Exception:
        logger.exception("get_progress handler failed")
        return validate.format_500_error(request)
