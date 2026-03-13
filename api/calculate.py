from aiohttp import web
from aiohttp_apispec import docs, request_schema

from api import validate
from config import logger
from docs import schems as sh


@docs(
    tags=["Cashback Client"],
    summary="Рассчитать список категорий для клиента",
    description="Возвращает список всех категорий для клиентского экрана. Backend сам решает, вернуть новый расчёт или уже актуальное состояние.",
    responses={
        200: {"description": "Список категорий рассчитан", "schema": sh.CalculateResponseSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
)
@request_schema(sh.CalculateRequestSchema)
@validate.validate(validate.Client_calculate)
async def calculate(request: web.Request, parsed: validate.Client_calculate) -> web.Response:
    try:
        period_id = parsed.period_id or "2026-03"
        items = [
            {
                "selection_id": "sel_restaurants",
                "category_id": "cat_restaurants",
                "name": "Restaurants",
                "subtitle": "Кэшбэк в кафе и ресторанах",
                "icon_key": "restaurants",
                "icon_url": "/icons/restaurants.svg",
                "rate": {"min": 5, "max": 15},
                "expected_benefit_amount": 850,
                "currency": "RUB",
                "availability_status": "available",
                "availability_reason": None,
            },
            {
                "selection_id": "sel_fuel",
                "category_id": "cat_fuel",
                "name": "Fuel",
                "subtitle": "Кэшбэк на АЗС",
                "icon_key": "fuel",
                "icon_url": "/icons/fuel.svg",
                "rate": {"min": 3, "max": 8},
                "expected_benefit_amount": 420,
                "currency": "RUB",
                "availability_status": "budget_limited",
                "availability_reason": "Доступность ограничена бюджетом категории",
            },
        ]
        return web.json_response({"period_id": period_id, "items": items}, status=200)
    except Exception as e:
        logger.error("calculate error: ", e)
        return validate.format_500_error(request)
