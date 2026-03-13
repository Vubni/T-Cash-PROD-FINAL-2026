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

        async with Database() as db:
            if db is None:
                return validate.format_500_error(request)

            sql = """
                SELECT
                    s.selection_id,
                    s.category_id,
                    s.expected_benefit_amount,
                    s.currency,
                    s.availability_status,
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
                WHERE s.period_id = $1
            """
            rows = await db.execute_all(sql, (period_id,)) or []

        items = []
        for row in rows:
            rate = _calc_rate(
                budget_amount=row.get("budget_amount") or 0,
                target_users=row.get("target_users") or 0,
                avg_spend_per_user=row.get("avg_spend_per_user") or 0,
            )
            icon_key = row["icon_key"]
            items.append(
                {
                    "selection_id": row["selection_id"],
                    "category_id": row["category_id"],
                    "name": row["name"],
                    "subtitle": row["subtitle"],
                    "icon_key": icon_key,
                    "icon_url": f"/icons/{icon_key}.svg",
                    "rate": rate,
                    "expected_benefit_amount": row["expected_benefit_amount"],
                    "currency": row["currency"] or row["budget_currency"],
                    "availability_status": row["availability_status"],
                    "availability_reason": row["availability_reason"],
                }
            )

        return web.json_response({"period_id": period_id, "items": items}, status=200)
    except Exception:
        logger.exception("calculate handler failed")
        return validate.format_500_error(request)
