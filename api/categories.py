from aiohttp import web
from aiohttp_apispec import docs, request_schema

from api import validate
from config import logger
from docs import schems as sh


def _build_category_detail(category_id: str) -> dict:
    icon_key = "restaurants"
    return {
        "id": category_id,
        "name": "Restaurants",
        "subtitle": "Кэшбэк в кафе и ресторанах",
        "icon_key": icon_key,
        "icon_url": f"/icons/{icon_key}.svg",
        "status": "active",
        "budget": {
            "amount": 1500000,
            "currency": "RUB",
        },
        "rate": {
            "min": 5,
            "max": 15,
        },
        "audience": {
            "segments": ["mass", "active_spenders"],
        },
        "rule": {
            "personalized": True,
            "budget_mode": "hard_limit",
            "fallback_message": "Категория временно недоступна из-за лимита бюджета",
        },
        "history": [
            {
                "changed_at": "2026-03-13T10:00:00Z",
                "changed_by": "admin@example.com",
                "field": "budget_amount",
                "old_value": 1000000,
                "new_value": 1500000,
            }
        ],
    }


@docs(
    tags=["Admin"],
    summary="Список категорий кэшбэка",
    description="Возвращает список категорий для админки. Используется для просмотра всех настроенных категорий вместе с бюджетом и диапазоном ставок.",
    responses={
        200: {"description": "Список категорий получен", "schema": sh.CategoryListResponseSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "query",
            "name": "status",
            "schema": {"type": "string"},
            "required": False,
            "description": "Фильтр по статусу категории",
        },
        {
            "in": "query",
            "name": "limit",
            "schema": {"type": "integer", "default": 50},
            "required": False,
            "description": "Максимальное количество элементов в ответе",
        },
        {
            "in": "query",
            "name": "cursor",
            "schema": {"type": "string"},
            "required": False,
            "description": "Курсор пагинации",
        },
    ],
)
@validate.validate(validate.Admin_categories_list)
async def list_categories(request: web.Request, parsed: validate.Admin_categories_list) -> web.Response:
    try:
        items = [
            {
                "id": "cat_restaurants",
                "name": "Restaurants",
                "subtitle": "Кэшбэк в кафе и ресторанах",
                "icon_key": "restaurants",
                "icon_url": "/icons/restaurants.svg",
                "status": parsed.status or "active",
                "budget": {"amount": 1500000, "currency": "RUB"},
                "rate": {"min": 5, "max": 15},
            }
        ]
        return web.json_response({"items": items, "total": len(items)}, status=200)
    except Exception:
        logger.exception("list_categories handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Admin"],
    summary="Создать категорию кэшбэка",
    description="Создаёт новую категорию вместе с бюджетом, диапазоном ставок, аудиторией и правилом персонализации.",
    responses={
        201: {"description": "Категория создана", "schema": sh.CategoryDetailSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
)
@request_schema(sh.CategoryCreateSchema)
@validate.validate(validate.Admin_category_create)
async def create_category(request: web.Request, parsed: validate.Admin_category_create) -> web.Response:
    try:
        icon_url = f"/icons/{parsed.icon_key}.svg"
        response = {
            "id": "cat_new",
            "name": parsed.name,
            "subtitle": parsed.subtitle,
            "icon_key": parsed.icon_key,
            "icon_url": icon_url,
            "status": parsed.status,
            "budget": {
                "amount": parsed.budget_amount,
                "currency": parsed.budget_currency,
            },
            "rate": {
                "min": parsed.rate_min,
                "max": parsed.rate_max,
            },
            "audience": {
                "segments": parsed.audience_segments,
            },
            "rule": {
                "personalized": parsed.rule_personalized,
                "budget_mode": parsed.rule_budget_mode,
                "fallback_message": parsed.rule_fallback_message,
            },
            "history": [],
        }
        return web.json_response(response, status=201)
    except Exception:
        logger.exception("create_category handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Admin"],
    summary="Получить категорию кэшбэка",
    description="Возвращает одну категорию целиком: метаданные, бюджет, диапазон ставок, аудиторию, правило и историю изменений.",
    responses={
        200: {"description": "Категория получена", "schema": sh.CategoryDetailSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "path",
            "name": "category_id",
            "schema": {"type": "string"},
            "required": True,
            "description": "Идентификатор категории",
        }
    ],
)
@validate.validate(validate.Category_id_path)
async def get_category(request: web.Request, parsed: validate.Category_id_path) -> web.Response:
    try:
        return web.json_response(_build_category_detail(parsed.category_id), status=200)
    except Exception:
        logger.exception("get_category handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Admin"],
    summary="Изменить категорию кэшбэка",
    description="Частично обновляет категорию. Через этот endpoint можно менять бюджет, диапазон ставок, аудиторию, статус и правило категории.",
    responses={
        200: {"description": "Категория обновлена", "schema": sh.CategoryDetailSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "path",
            "name": "category_id",
            "schema": {"type": "string"},
            "required": True,
            "description": "Идентификатор категории",
        }
    ],
)
@request_schema(sh.CategoryUpdateSchema)
@validate.validate(validate.Admin_category_update)
async def update_category(request: web.Request, parsed: validate.Admin_category_update) -> web.Response:
    try:
        category_id = request.match_info["category_id"]
        response = _build_category_detail(category_id)

        if parsed.name is not None:
            response["name"] = parsed.name
        if parsed.subtitle is not None:
            response["subtitle"] = parsed.subtitle
        if parsed.icon_key is not None:
            response["icon_key"] = parsed.icon_key
        if parsed.status is not None:
            response["status"] = parsed.status
        if parsed.budget_amount is not None:
            response["budget"]["amount"] = parsed.budget_amount
        if parsed.budget_currency is not None:
            response["budget"]["currency"] = parsed.budget_currency
        if parsed.rate_min is not None:
            response["rate"]["min"] = parsed.rate_min
        if parsed.rate_max is not None:
            response["rate"]["max"] = parsed.rate_max
        if parsed.audience_segments is not None:
            response["audience"]["segments"] = parsed.audience_segments
        if parsed.rule_personalized is not None:
            response["rule"]["personalized"] = parsed.rule_personalized
        if parsed.rule_budget_mode is not None:
            response["rule"]["budget_mode"] = parsed.rule_budget_mode
        if parsed.rule_fallback_message is not None:
            response["rule"]["fallback_message"] = parsed.rule_fallback_message

        # пересчитываем icon_url по актуальному icon_key
        icon_key = response.get("icon_key")
        if icon_key:
            response["icon_url"] = f"/icons/{icon_key}.svg"

        return web.json_response(response, status=200)
    except Exception:
        logger.exception("update_category handler failed")
        return validate.format_500_error(request)
