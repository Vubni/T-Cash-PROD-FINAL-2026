from aiohttp import web
from aiohttp_apispec import docs, request_schema
from pydantic import BaseModel, field_validator, model_validator
import json
import os
from typing import Optional

from api import validate
from config import logger
from docs import schems as sh
from functions import audit as audit_fns
from functions import selection as sel_fns
from functions import users as users_fns


_DEFAULT_SELECTION_COUNT = 5
_CATEGORIES_CONFIG_PATH = os.getenv(
    "CATEGORIES_CONFIG_PATH", os.path.join("config", "categories_config.json")
)


def _load_categories_config() -> dict:
    try:
        with open(_CATEGORIES_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
        if not isinstance(data, dict):
            return {}
        return data
    except Exception:
        return {}


def _save_categories_config(cfg: dict) -> None:
    os.makedirs(os.path.dirname(_CATEGORIES_CONFIG_PATH), exist_ok=True)
    with open(_CATEGORIES_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def _load_required_selection_count() -> int:
    data = _load_categories_config()
    try:
        value = int(data.get("max_selection_count", _DEFAULT_SELECTION_COUNT))
        if value < 1:
            return _DEFAULT_SELECTION_COUNT
        return value
    except Exception:
        return _DEFAULT_SELECTION_COUNT


REQUIRED_SELECTION_COUNT = _load_required_selection_count()


class Selection_submit_body(BaseModel):
    model_config = {"extra": "forbid"}

    user_id: str
    category_ids: list[str]

    @field_validator("user_id")
    @classmethod
    def user_id_uuid(cls, v: str) -> str:
        return validate.validate_uuid(v, "user_id")

    @field_validator("category_ids")
    @classmethod
    def category_ids_uuids(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("category_ids не может быть пустым")
        return [validate.validate_uuid(cid, "category_id") for cid in v]

    @model_validator(mode="after")
    def exactly_five_categories(self) -> "Selection_submit_body":
        if len(self.category_ids) != REQUIRED_SELECTION_COUNT:
            raise ValueError(
                f"Нужно выбрать ровно {REQUIRED_SELECTION_COUNT} категорий, передано {len(self.category_ids)}"
            )
        if len(set(self.category_ids)) != REQUIRED_SELECTION_COUNT:
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
    description="В теле передаётся user_id (UUID) и ровно N category_ids (UUID), где N задаётся в настройках; в selections создаётся N строк. **Обязательные** поля: user_id, category_ids (массив ровно из N UUID).",
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
        await audit_fns.write_audit(
            entity_type="client",
            entity_id=str(parsed.user_id),
            action="selection",
            actor=str(parsed.user_id),
            details={"category_ids": parsed.category_ids, "selection_ids": created_selection_ids},
        )
        return web.json_response(
            {
                "user_id": str(parsed.user_id),
                "category_ids": parsed.category_ids,
                "selection_ids": created_selection_ids,
                "message": "Выбор из 5 категорий сохранён",
            },
            status=200,
        )
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
async def update_selection_settings(
    request: web.Request, parsed: Admin_selection_settings
) -> web.Response:
    try:
        cfg = _load_categories_config()

        if parsed.all_categories is not None:
            cfg["all_categories"] = int(parsed.all_categories)
        if parsed.max_selection_count is not None:
            cfg["max_selection_count"] = parsed.max_selection_count

        _save_categories_config(cfg)

        global REQUIRED_SELECTION_COUNT
        REQUIRED_SELECTION_COUNT = _load_required_selection_count()

        return web.json_response(
            {
                "all_categories": int(cfg.get("all_categories", 0) or 0),
                "max_selection_count": REQUIRED_SELECTION_COUNT,
            },
            status=200,
        )
    except Exception:
        logger.exception("update_selection_settings handler failed")
        return validate.format_500_error(request)
