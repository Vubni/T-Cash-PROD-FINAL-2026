from aiohttp import web
from aiohttp_apispec import docs, request_schema
from pydantic import BaseModel, field_validator, model_validator

from api import validate
from config import logger
from docs import schems as sh
from functions import selection as sel_fns
from functions import users as users_fns


REQUIRED_SELECTION_COUNT = 5


class Selection_submit_body(BaseModel):
    model_config = {"extra": "forbid"}

    user_id: int
    category_ids: list[str]

    @field_validator("user_id")
    @classmethod
    def user_id_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("user_id должен быть положительным целым числом")
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
    summary="Сохранить выбор ровно из 5 категорий",
    description="В теле передаётся user_id и ровно 5 category_ids. В selections создаётся 5 строк.",
    responses={
        200: {"description": "Выбор сохранён", "schema": sh.SelectionSubmitResponseSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
)
@request_schema(sh.SelectionSubmitBodySchema)
@validate.validate(Selection_submit_body)
async def confirm_selection(request: web.Request, parsed: Selection_submit_body) -> web.Response:
    try:
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
