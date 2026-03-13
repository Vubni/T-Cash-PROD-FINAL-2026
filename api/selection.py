from aiohttp import web
from aiohttp_apispec import docs, request_schema

from api import validate
from config import logger
from docs import schems as sh


def _build_selection(selection_id: str) -> dict:
    return {
        "selection_id": selection_id,
        "category_id": "cat_restaurants",
        "name": "Restaurants",
        "subtitle": "Кэшбэк в кафе и ресторанах",
        "rate": {
            "min": 5,
            "max": 15,
        },
        "expected_benefit_amount": 850,
        "currency": "RUB",
        "status": "available",
        "budget_message": None,
    }


@docs(
    tags=["Cashback Client"],
    summary="Получить выбор по идентификатору",
    description="Возвращает данные по конкретному выбору до подтверждения: категорию, диапазон ставки, ожидаемую выгоду и текущие ограничения.",
    responses={
        200: {"description": "Выбор получен", "schema": sh.SelectionDetailSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "path",
            "name": "selection_id",
            "schema": {"type": "string"},
            "required": True,
            "description": "Идентификатор выбора, полученный из calculate",
        }
    ],
)
@validate.validate(validate.Selection_id_path)
async def get_selection(request: web.Request, parsed: validate.Selection_id_path) -> web.Response:
    try:
        return web.json_response(_build_selection(parsed.selection_id), status=200)
    except Exception as e:
        logger.error("get_selection error: ", e)
        return validate.format_500_error(request)


@docs(
    tags=["Cashback Client"],
    summary="Подтвердить выбор по идентификатору",
    description="Подтверждает конкретный выбор пользователя. Идентификатор выбора передаётся в path, а в теле можно дополнительно передать период подтверждения.",
    responses={
        200: {"description": "Выбор подтверждён", "schema": sh.SelectionConfirmResponseSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "path",
            "name": "selection_id",
            "schema": {"type": "string"},
            "required": True,
            "description": "Идентификатор выбора, который пользователь подтверждает",
        },
        {
            "in": "header",
            "name": "Idempotency-Key",
            "schema": {"type": "string"},
            "required": False,
            "description": "Ключ идемпотентности для защиты от повторного подтверждения",
        },
    ],
)
@request_schema(sh.SelectionConfirmSchema)
@validate.validate(validate.Selection_confirm)
async def confirm_selection(request: web.Request, parsed: validate.Selection_confirm) -> web.Response:
    try:
        response = {
            "selection_id": parsed.selection_id,
            "category_id": "cat_restaurants",
            "status": "confirmed" if parsed.confirm else "pending",
            "expected_benefit_amount": 850,
            "currency": "RUB",
            "message": "Выбор принят и сохранён на стороне сервера",
        }
        return web.json_response(response, status=200)
    except Exception as e:
        logger.error("confirm_selection error: ", e)
        return validate.format_500_error(request)
