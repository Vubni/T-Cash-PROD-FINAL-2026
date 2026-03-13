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


def _row_to_selection_detail(row: dict) -> dict:
    rate = _calc_rate(
        budget_amount=row.get("budget_amount") or 0,
        target_users=row.get("target_users") or 0,
        avg_spend_per_user=row.get("avg_spend_per_user") or 0,
    )
    icon_key = row["icon_key"]
    return {
        "selection_id": row["selection_id"],
        "category_id": row["category_id"],
        "name": row["name"],
        "subtitle": row["subtitle"],
        "icon_key": icon_key,
        "icon_url": f"/icons/{icon_key}.svg",
        "rate": rate,
        "expected_benefit_amount": row["expected_benefit_amount"],
        "currency": row["currency"] or row["budget_currency"],
        "status": row["status"],
        "budget_message": row["availability_reason"],
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
        async with Database() as db:
            if db is None:
                return validate.format_500_error(request)

            sql = """
                SELECT
                    s.selection_id,
                    s.category_id,
                    s.expected_benefit_amount,
                    s.currency,
                    s.status,
                    s.availability_reason,
                    c.name,
                    c.subtitle,
                    c.icon_key,
                    c.budget_amount,
                    c.budget_currency,
                    c.target_users,
                    c.avg_spend_per_user
                FROM selections s
                JOIN categories c ON c.category_id = s.category_id
                WHERE s.selection_id = $1
            """
            row = await db.execute(sql, (parsed.selection_id,))

        if row is None:
            raise web.HTTPNotFound()

        return web.json_response(_row_to_selection_detail(row), status=200)
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
        selection_id = parsed.selection_id
        idempotency_key = request.headers.get("Idempotency-Key")

        async with Database() as db:
            if db is None:
                return validate.format_500_error(request)

            new_status = "confirmed" if parsed.confirm else "pending"

            sql_update = """
                UPDATE selections
                SET status = $1,
                    idempotency_key = COALESCE($2, idempotency_key),
                    updated_at = NOW()
                WHERE selection_id = $3
            """
            await db.execute(sql_update, (new_status, idempotency_key, selection_id))

            sql_select = """
                SELECT
                    s.selection_id,
                    s.category_id,
                    s.expected_benefit_amount,
                    s.currency,
                    s.status,
                    s.availability_reason,
                    c.name,
                    c.subtitle,
                    c.icon_key,
                    c.budget_amount,
                    c.budget_currency,
                    c.target_users,
                    c.avg_spend_per_user
                FROM selections s
                JOIN categories c ON c.category_id = s.category_id
                WHERE s.selection_id = $1
            """
            row = await db.execute(sql_select, (selection_id,))

        if row is None:
            raise web.HTTPNotFound()

        detail = _row_to_selection_detail(row)
        response = {
            "selection_id": detail["selection_id"],
            "category_id": detail["category_id"],
            "status": detail["status"],
            "expected_benefit_amount": detail["expected_benefit_amount"],
            "currency": detail["currency"],
            "message": "Выбор принят и сохранён на стороне сервера",
        }
        return web.json_response(response, status=200)
    except Exception as e:
        logger.error("confirm_selection error: ", e)
        return validate.format_500_error(request)
