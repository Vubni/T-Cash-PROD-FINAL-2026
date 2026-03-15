from typing import Optional

from aiohttp import web
from aiohttp_apispec import docs, request_schema
from pydantic import BaseModel, field_validator, model_validator

from api import validate
from config import logger
from core import (
    get_all_categories,
    get_max_selection_count,
    load_categories_config,
    save_categories_config,
)
from docs import schems as sh
from functions import selection as sel_fns
from functions import users as users_fns


class Selection_submit_body(BaseModel):
    model_config = {"extra": "forbid"}

    category_ids: list[str]

    @field_validator("category_ids")
    @classmethod
    def category_ids_uuids(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("category_ids не может быть пустым")
        return [validate.validate_uuid(cid, "category_id") for cid in v]

    @model_validator(mode="after")
    def exactly_five_categories(self) -> "Selection_submit_body":
        required = get_max_selection_count()
        if len(self.category_ids) != required:
            raise ValueError(f"Нужно выбрать ровно {required} категорий, передано {len(self.category_ids)}")
        if len(set(self.category_ids)) != required:
            raise ValueError("Категории не должны повторяться")
        return self


class Admin_selection_settings(BaseModel):
    model_config = {"extra": "forbid"}

    all_categories: Optional[int] = None
    max_selection_count: Optional[int] = None

    @field_validator("max_selection_count")
    @classmethod
    def max_selection_count_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1:
            raise ValueError("max_selection_count must be at least 1")
        return v


@docs(
    tags=["Client"],
    summary="Сохранить выбор ровно из N категорий",
    description=(
        "Сохраняет выбор категорий для текущего авторизованного пользователя. "
        "user_id берётся из JWT-токена пользователя (заголовок Authorization: Bearer <token>, полученный через "
        "GET /api/v1/users/{user_id}/auth). В теле передаётся ровно N category_ids (UUID), "
        "где N задаётся в настройках; в selections создаётся N строк. **Обязательные** поля тела: "
        "category_ids (массив ровно из N UUID)."
    ),
    security=validate.SECURITY_USER_BEARER,
    responses={
        200: {"description": "Выбор сохранён", "schema": sh.SelectionSubmitResponseSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
)
@request_schema(sh.SelectionSubmitBodySchema)
@validate.validate(Selection_submit_body, require_auth=True)
async def confirm_selection(request: web.Request, parsed: Selection_submit_body) -> web.Response:
    try:
        payload = request.get("user_payload") or {}
        user_id = payload.get("user_id")
        if user_id is None:
            return validate.format_401_error(request, "Токен пользователя отсутствует или не содержит user_id")

        if not await users_fns.user_exists(user_id):
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

        current = await sel_fns.get_current_category_ids(user_id)
        if (
            current is not None
            and len(current) == len(parsed.category_ids)
            and set(current) == set(parsed.category_ids)
        ):
            return web.json_response({"category_ids": parsed.category_ids}, status=200)

        await sel_fns.save_selection_batch(user_id, parsed.category_ids)
        return web.json_response({"category_ids": parsed.category_ids}, status=200)
    except Exception:
        logger.exception("confirm_selection handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Admin"],
    summary="Обновить настройки выбора категорий",
    description="Позволяет обычному администратору менять глобальные настройки выбора категорий: флаг all_categories и лимит max_selection_count. Требуется JWT админа.",
    security=validate.SECURITY_ADMIN_BEARER,
    responses={
        200: {
            "description": "Настройки обновлены",
            "schema": sh.CategorySelectionSettingsResponseSchema,
        },
        **sh.RESPONSES_HTTP_ERROR,
    },
)
@request_schema(sh.CategorySelectionSettingsSchema)
@validate.validate(Admin_selection_settings, require_admin=True)
async def update_selection_settings(request: web.Request, parsed: Admin_selection_settings) -> web.Response:
    try:
        cfg = load_categories_config()

        if parsed.all_categories is not None:
            cfg["all_categories"] = int(parsed.all_categories)
        if parsed.max_selection_count is not None:
            cfg["max_selection_count"] = parsed.max_selection_count

        save_categories_config(cfg)

        return web.json_response(
            {
                "all_categories": get_all_categories(),
                "max_selection_count": get_max_selection_count(),
            },
            status=200,
        )
    except Exception:
        logger.exception("update_selection_settings handler failed")
        return validate.format_500_error(request)
