from aiohttp import web
from aiohttp_apispec import docs, request_schema

from api import validate
from config import logger
from docs import schems as sh
from functions import categories as cat_fns


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
        limit = parsed.limit or 50
        items = await cat_fns.list_categories(parsed.status, limit)
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
        category_id = getattr(parsed, "category_id", None)
        response = await cat_fns.create_category(
            category_id=category_id,
            name=parsed.name,
            subtitle=parsed.subtitle,
            icon_key=parsed.icon_key,
            status=parsed.status,
            budget_amount=parsed.budget_amount,
            budget_currency=parsed.budget_currency,
            target_users=parsed.target_users,
            avg_spend_per_user=parsed.avg_spend_per_user,
            audience_segments=parsed.audience_segments,
            rule_personalized=parsed.rule_personalized,
            rule_budget_mode=parsed.rule_budget_mode,
            rule_fallback_message=parsed.rule_fallback_message,
        )
        if response is None:
            return validate.format_500_error(request)
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
        response = await cat_fns.get_category(parsed.category_id)
        if response is None:
            raise web.HTTPNotFound()
        return web.json_response(response, status=200)
    except web.HTTPNotFound:
        raise
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
        response = await cat_fns.update_category(
            category_id,
            name=parsed.name,
            subtitle=parsed.subtitle,
            icon_key=parsed.icon_key,
            status=parsed.status,
            budget_amount=parsed.budget_amount,
            budget_currency=parsed.budget_currency,
            target_users=getattr(parsed, "target_users", None),
            avg_spend_per_user=getattr(parsed, "avg_spend_per_user", None),
            audience_segments=parsed.audience_segments,
            rule_personalized=parsed.rule_personalized,
            rule_budget_mode=parsed.rule_budget_mode,
            rule_fallback_message=parsed.rule_fallback_message,
        )
        if response is None:
            raise web.HTTPNotFound()
        return web.json_response(response, status=200)
    except web.HTTPNotFound:
        raise
    except Exception:
        logger.exception("update_category handler failed")
        return validate.format_500_error(request)
