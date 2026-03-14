from aiohttp import web
from aiohttp_apispec import docs, request_schema
from pydantic import BaseModel, field_validator

from api import validate
from api.validate import validate_uuid
from config import logger
from docs import schems as sh
from functions import selection as sel_fns


class Selection_id_path(BaseModel):
    model_config = {"extra": "forbid"}

    selection_id: str

    @field_validator("selection_id")
    @classmethod
    def selection_id_uuid(cls, v: str) -> str:
        return validate_uuid(v, "selection_id")


class Selection_confirm(BaseModel):
    model_config = {"extra": "forbid"}

    selection_id: str
    confirm: bool = True

    @field_validator("selection_id")
    @classmethod
    def selection_id_uuid(cls, v: str) -> str:
        return validate_uuid(v, "selection_id")


@docs(
    tags=["Client"],
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
@validate.validate(Selection_id_path)
async def get_selection(request: web.Request, parsed: Selection_id_path) -> web.Response:
    try:
        detail = await sel_fns.get_selection(parsed.selection_id)
        if detail is None:
            raise web.HTTPNotFound()
        return web.json_response(detail, status=200)
    except web.HTTPNotFound:
        raise
    except Exception:
        logger.exception("get_selection handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Client"],
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
@validate.validate(Selection_confirm)
async def confirm_selection(request: web.Request, parsed: Selection_confirm) -> web.Response:
    try:
        selection_id = parsed.selection_id
        idempotency_key = request.headers.get("Idempotency-Key")
        new_status = "confirmed" if parsed.confirm else "pending"
        detail = await sel_fns.confirm_selection(selection_id, new_status, idempotency_key)
        if detail is None:
            raise web.HTTPNotFound()
        response = {
            "selection_id": detail["selection_id"],
            "category_id": detail["category_id"],
            "expected_benefit_amount": detail["expected_benefit_amount"],
            "message": "Выбор принят и сохранён на стороне сервера",
        }
        return web.json_response(response, status=200)
    except web.HTTPNotFound:
        raise
    except Exception:
        logger.exception("confirm_selection handler failed")
        return validate.format_500_error(request)
