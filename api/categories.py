from aiohttp import web
from aiohttp_apispec import docs, request_schema

from api import validate
from config import logger
from database.database import Database
from docs import schems as sh


def _calc_rate(budget_amount: int, target_users: int, avg_spend_per_user: int) -> dict:
    try:
        if not budget_amount or not target_users or not avg_spend_per_user:
            return {"min": 5, "max": 15}
        total_expected_spend = target_users * avg_spend_per_user
        if total_expected_spend <= 0:
            return {"min": 5, "max": 15}
        base_rate = round(100 * budget_amount / total_expected_spend)
        base_rate = max(1, min(base_rate, 30))
        return {
            "min": max(1, base_rate - 2),
            "max": min(30, base_rate + 2),
        }
    except Exception:
        return {"min": 5, "max": 15}


def _row_to_category(item: dict) -> dict:
    rate = _calc_rate(
        budget_amount=item.get("budget_amount") or 0,
        target_users=item.get("target_users") or 0,
        avg_spend_per_user=item.get("avg_spend_per_user") or 0,
    )
    icon_key = item["icon_key"]
    return {
        "id": item["category_id"],
        "name": item["name"],
        "subtitle": item["subtitle"],
        "icon_key": icon_key,
        "icon_url": f"/icons/{icon_key}.svg",
        "status": item["status"],
        "budget": {
            "amount": item["budget_amount"],
            "currency": item["budget_currency"],
        },
        "rate": rate,
        "audience": {
            "segments": item["audience_segments"],
        },
        "rule": {
            "personalized": item["rule_personalized"],
            "budget_mode": item["rule_budget_mode"],
            "fallback_message": item["rule_fallback_message"],
        },
        "history": [],
    }


@docs(
    tags=["Cashback Admin"],
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
        async with Database() as db:
            if db is None:
                return validate.format_500_error(request)

            limit = parsed.limit or 50
            status = parsed.status
            sql = """
                SELECT
                    category_id,
                    name,
                    subtitle,
                    icon_key,
                    status,
                    budget_amount,
                    budget_currency,
                    target_users,
                    avg_spend_per_user,
                    audience_segments,
                    rule_personalized,
                    rule_budget_mode,
                    rule_fallback_message
                FROM categories
                WHERE ($1::text IS NULL OR status = $1)
                ORDER BY created_at DESC, category_id
                LIMIT $2
            """
            rows = await db.execute_all(sql, (status, limit)) or []
        items = [_row_to_category(row) for row in rows]
        return web.json_response({"items": items, "total": len(items)}, status=200)
    except Exception:
        logger.exception("list_categories handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Cashback Admin"],
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
        async with Database() as db:
            if db is None:
                return validate.format_500_error(request)

            sql = """
                INSERT INTO categories (
                    category_id,
                    name,
                    subtitle,
                    icon_key,
                    status,
                    budget_amount,
                    budget_currency,
                    target_users,
                    avg_spend_per_user,
                    audience_segments,
                    rule_personalized,
                    rule_budget_mode,
                    rule_fallback_message
                )
                VALUES (
                    $1, $2, $3, $4, $5,
                    $6, $7,
                    $8, $9,
                    $10,
                    $11, $12, $13
                )
            """
            category_id = parsed.category_id if hasattr(parsed, "category_id") else None
            if not category_id:
                from uuid import uuid4

                category_id = f"cat_{uuid4().hex[:8]}"

            await db.execute(
                sql,
                (
                    category_id,
                    parsed.name,
                    parsed.subtitle,
                    parsed.icon_key,
                    parsed.status,
                    parsed.budget_amount,
                    parsed.budget_currency,
                    parsed.target_users,
                    parsed.avg_spend_per_user,
                    parsed.audience_segments,
                    parsed.rule_personalized,
                    parsed.rule_budget_mode,
                    parsed.rule_fallback_message,
                ),
            )

            row_sql = """
                SELECT
                    category_id,
                    name,
                    subtitle,
                    icon_key,
                    status,
                    budget_amount,
                    budget_currency,
                    target_users,
                    avg_spend_per_user,
                    audience_segments,
                    rule_personalized,
                    rule_budget_mode,
                    rule_fallback_message
                FROM categories
                WHERE category_id = $1
            """
            row = await db.execute(row_sql, (category_id,))

        if row is None:
            return validate.format_500_error(request)

        response = _row_to_category(row)
        return web.json_response(response, status=201)
    except Exception:
        logger.exception("create_category handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Cashback Admin"],
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
        async with Database() as db:
            if db is None:
                return validate.format_500_error(request)

            sql = """
                SELECT
                    category_id,
                    name,
                    subtitle,
                    icon_key,
                    status,
                    budget_amount,
                    budget_currency,
                    target_users,
                    avg_spend_per_user,
                    audience_segments,
                    rule_personalized,
                    rule_budget_mode,
                    rule_fallback_message
                FROM categories
                WHERE category_id = $1
            """
            row = await db.execute(sql, (parsed.category_id,))

        if row is None:
            raise web.HTTPNotFound()

        return web.json_response(_row_to_category(row), status=200)
    except Exception:
        logger.exception("get_category handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Cashback Admin"],
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

        async with Database() as db:
            if db is None:
                return validate.format_500_error(request)

            fields = []
            params = []

            def add(field_name: str, value):
                if value is not None:
                    params.append(value)
                    fields.append(f"{field_name} = ${len(params)}")

            add("name", parsed.name)
            add("subtitle", parsed.subtitle)
            add("icon_key", parsed.icon_key)
            add("status", parsed.status)
            add("budget_amount", parsed.budget_amount)
            add("budget_currency", parsed.budget_currency)
            add("target_users", getattr(parsed, "target_users", None))
            add("avg_spend_per_user", getattr(parsed, "avg_spend_per_user", None))
            add("audience_segments", parsed.audience_segments)
            add("rule_personalized", parsed.rule_personalized)
            add("rule_budget_mode", parsed.rule_budget_mode)
            add("rule_fallback_message", parsed.rule_fallback_message)

            if fields:
                fields.append("updated_at = NOW()")
                params.append(category_id)
                sql_update = f"UPDATE categories SET {', '.join(fields)} WHERE category_id = ${len(params)}"
                await db.execute(sql_update, tuple(params))

            sql_select = """
                SELECT
                    category_id,
                    name,
                    subtitle,
                    icon_key,
                    status,
                    budget_amount,
                    budget_currency,
                    target_users,
                    avg_spend_per_user,
                    audience_segments,
                    rule_personalized,
                    rule_budget_mode,
                    rule_fallback_message
                FROM categories
                WHERE category_id = $1
            """
            row = await db.execute(sql_select, (category_id,))

        if row is None:
            raise web.HTTPNotFound()

        response = _row_to_category(row)
        return web.json_response(response, status=200)
    except Exception:
        logger.exception("update_category handler failed")
        return validate.format_500_error(request)
