from aiohttp import web
from aiohttp_apispec import docs, request_schema
from pydantic import BaseModel, field_validator, model_validator

from api import validate
from api.validate import validate_uuid
from config import logger
from docs import schems as sh
from functions import selection as sel_fns
from functions import users as users_fns


SELECTION_ID_MAX_LENGTH = 128
REQUIRED_SELECTION_COUNT = 5


class Selection_id_path(BaseModel):
    model_config = {"extra": "forbid"}

    selection_id: str

    @field_validator("selection_id")
    @classmethod
    def selection_id_uuid(cls, v: str) -> str:
        return validate_uuid(v, "selection_id")


class Selection_submit_body(BaseModel):
    model_config = {"extra": "forbid"}

    selection_id: str  # из path
    user_id: str
    category_ids: list[str]

    @field_validator("selection_id")
    @classmethod
    def selection_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("selection_id не может быть пустым")
        if len(v) > SELECTION_ID_MAX_LENGTH:
            raise ValueError(f"selection_id не длиннее {SELECTION_ID_MAX_LENGTH} символов")
        return v

    @field_validator("user_id")
    @classmethod
    def user_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("user_id не может быть пустым")
        return v

    @model_validator(mode="after")
    def exactly_five_categories(self) -> "Selection_submit_body":
        if len(self.category_ids) != REQUIRED_SELECTION_COUNT:
            raise ValueError(
                f"Нужно выбрать ровно {REQUIRED_SELECTION_COUNT} категорий, передано {len(self.category_ids)}"
            )
        if len(set(self.category_ids)) != REQUIRED_SELECTION_COUNT:
            raise ValueError("Категории не должны повторяться")
        return self


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
    summary="Сохранить выбор ровно из 5 категорий",
    description="В теле передаётся ровно 5 category_ids. В selections создаётся 5 строк (selection_id, category_id). selection_id в path — идентификатор запроса (идемпотентность).",
    responses={
        200: {"description": "Выбор сохранён", "schema": sh.SelectionSubmitResponseSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "path",
            "name": "selection_id",
            "schema": {"type": "string"},
            "required": True,
            "description": "Идентификатор запроса (например для идемпотентности)",
        },
    ],
)
@request_schema(sh.SelectionSubmitBodySchema)
@validate.validate(Selection_submit_body)
async def confirm_selection(request: web.Request, parsed: Selection_submit_body) -> web.Response:
    try:
        selection_id = parsed.selection_id

        if not await users_fns.user_exists(parsed.user_id):
            return validate.format_404_error(request, message="Пользователь не найден")

        exists = await sel_fns.check_categories_exist(parsed.category_ids)
        if not exists:
            return validate.format_422_error(
                request,
                message="Одна или несколько категорий не найдены",
                field_errors=[
                    {
                        "field": "category_ids",
                        "issue": "Все category_id должны существовать в системе",
                        "rejectedValue": parsed.category_ids,
                    }
                ],
            )

        created_selection_ids = await sel_fns.save_selection_batch(
            parsed.user_id, parsed.category_ids
        )
        return web.json_response(
            {
                "selection_id": selection_id,
                "user_id": parsed.user_id,
                "category_ids": parsed.category_ids,
                "selection_ids": created_selection_ids,
                "message": "Выбор из 5 категорий сохранён",
            },
            status=200,
        )
    except Exception:
        logger.exception("confirm_selection handler failed")
        return validate.format_500_error(request)
