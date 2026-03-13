from typing import Optional

from aiohttp import web
from aiohttp_apispec import docs, request_schema
from pydantic import BaseModel, field_validator

from api import validate
from config import logger
from docs import schems as sh
from functions import calculate as calc_fns


PERIOD_ID_MAX_LENGTH = 32


class Client_calculate(BaseModel):
    model_config = {"extra": "forbid"}

    period_id: Optional[str] = None

    @field_validator("period_id")
    @classmethod
    def period_id_max_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > PERIOD_ID_MAX_LENGTH:
            raise ValueError(f"period_id cannot exceed {PERIOD_ID_MAX_LENGTH} characters")
        return v


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
@validate.validate(Client_calculate)
async def calculate(request: web.Request, parsed: Client_calculate) -> web.Response:
    try:
        period_id = parsed.period_id or "2026-03"
        items = await calc_fns.get_calculate_items(period_id)
        return web.json_response({"period_id": period_id, "items": items}, status=200)
    except Exception:
        logger.exception("calculate handler failed")
        return validate.format_500_error(request)
