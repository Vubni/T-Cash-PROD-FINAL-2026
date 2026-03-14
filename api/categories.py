from typing import Optional

from aiohttp import web
from aiohttp_apispec import docs, request_schema
from pydantic import BaseModel, field_validator, model_validator

from api import validate
from config import logger
from docs import schems as sh
from functions import categories as cat_fns


LIMIT_MAX = 500
AUDIENCE_SEGMENTS_MAX = 50
STRING_FIELD_MAX_LENGTH = 500


class Admin_categories_list(BaseModel):
    model_config = {"extra": "forbid"}

    offset: int = 0
    limit: int = 50

    @field_validator("offset")
    @classmethod
    def offset_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("offset must be non-negative")
        return v

    @field_validator("limit")
    @classmethod
    def limit_in_range(cls, v: int) -> int:
        if v < 1 or v > LIMIT_MAX:
            raise ValueError(f"limit must be between 1 and {LIMIT_MAX}")
        return v


class Admin_category_create(BaseModel):
    model_config = {"extra": "forbid"}

    category_id: Optional[str] = None
    name: str
    subtitle: str
    icon_key: str
    budget_amount: float
    target_users: int
    avg_spend_per_user: int
    audience_segments: list[str]
    rule_id: str

    @field_validator("name", "subtitle", "icon_key")
    @classmethod
    def check_non_empty_strings(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        if len(v) > STRING_FIELD_MAX_LENGTH:
            raise ValueError(f"Field cannot exceed {STRING_FIELD_MAX_LENGTH} characters")
        return v

    @field_validator("category_id")
    @classmethod
    def category_id_uuid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate.validate_uuid(v, "category_id")

    @field_validator("rule_id")
    @classmethod
    def rule_id_uuid(cls, v: str) -> str:
        return validate.validate_uuid(v, "rule_id")

    @field_validator("audience_segments")
    @classmethod
    def check_segments(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("At least one audience segment is required")
        if len(v) > AUDIENCE_SEGMENTS_MAX:
            raise ValueError(f"audience_segments cannot exceed {AUDIENCE_SEGMENTS_MAX} items")
        return v

    @field_validator("target_users", "avg_spend_per_user")
    @classmethod
    def check_non_negative_int(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Value cannot be negative")
        return v

    @model_validator(mode="after")
    def check_budget(self) -> "Admin_category_create":
        if self.budget_amount < 0:
            raise ValueError("budget_amount cannot be negative")
        return self


class Admin_category_update(BaseModel):
    model_config = {"extra": "forbid"}

    category_id: str
    name: Optional[str] = None
    subtitle: Optional[str] = None
    icon_key: Optional[str] = None
    budget_amount: Optional[float] = None
    target_users: Optional[int] = None
    avg_spend_per_user: Optional[int] = None
    audience_segments: Optional[list[str]] = None
    rule_id: Optional[str] = None

    @field_validator("rule_id")
    @classmethod
    def rule_id_uuid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate.validate_uuid(v, "rule_id")

    @field_validator("audience_segments")
    @classmethod
    def check_segments_max(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is not None and len(v) > AUDIENCE_SEGMENTS_MAX:
            raise ValueError(f"audience_segments cannot exceed {AUDIENCE_SEGMENTS_MAX} items")
        return v

    @field_validator("target_users", "avg_spend_per_user")
    @classmethod
    def check_non_negative_int(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Value cannot be negative")
        return v

    @model_validator(mode="after")
    def check_payload(self) -> "Admin_category_update":
        has_any_value = any(
            value is not None
            for k, value in self.model_dump().items()
            if k != "category_id"
        )
        if not has_any_value:
            raise ValueError("At least one field must be provided")
        if self.budget_amount is not None and self.budget_amount < 0:
            raise ValueError("budget_amount cannot be negative")
        return self


class Category_id_path(BaseModel):
    model_config = {"extra": "forbid"}

    category_id: str

    @field_validator("category_id")
    @classmethod
    def category_id_uuid(cls, v: str) -> str:
        return validate.validate_uuid(v, "category_id")


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
            "name": "offset",
            "type": "integer",
            "required": False,
            "description": "Смещение для пагинации",
        },
        {
            "in": "query",
            "name": "limit",
            "type": "integer",
            "required": False,
            "description": "Максимальное количество элементов в ответе",
        },
    ],
)
@validate.validate(Admin_categories_list)
async def list_categories(request: web.Request, parsed: Admin_categories_list) -> web.Response:
    try:
        items, total = await cat_fns.list_categories(parsed.offset, parsed.limit)
        return web.json_response({"items": items, "total": total}, status=200)
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
@validate.validate(Admin_category_create)
async def create_category(request: web.Request, parsed: Admin_category_create) -> web.Response:
    try:
        response = await cat_fns.create_category(
            category_id=parsed.category_id,
            name=parsed.name,
            subtitle=parsed.subtitle,
            icon_key=parsed.icon_key,
            budget_amount=int(parsed.budget_amount),
            target_users=parsed.target_users,
            avg_spend_per_user=parsed.avg_spend_per_user,
            audience_segments=parsed.audience_segments,
            rule_id=parsed.rule_id,
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
            "type": "string",
            "required": True,
            "description": "Идентификатор категории",
        }
    ],
)
@validate.validate(Category_id_path)
async def get_category(request: web.Request, parsed: Category_id_path) -> web.Response:
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
            "type": "string",
            "required": True,
            "description": "Идентификатор категории",
        }
    ],
)
@request_schema(sh.CategoryUpdateSchema)
@validate.validate(Admin_category_update)
async def update_category(request: web.Request, parsed: Admin_category_update) -> web.Response:
    try:
        response = await cat_fns.update_category(
            parsed.category_id,
            name=parsed.name,
            subtitle=parsed.subtitle,
            icon_key=parsed.icon_key,
            budget_amount=int(parsed.budget_amount) if parsed.budget_amount is not None else None,
            target_users=parsed.target_users,
            avg_spend_per_user=parsed.avg_spend_per_user,
            audience_segments=parsed.audience_segments,
            rule_id=parsed.rule_id,
        )
        if response is None:
            raise web.HTTPNotFound()
        return web.json_response(response, status=200)
    except web.HTTPNotFound:
        raise
    except Exception:
        logger.exception("update_category handler failed")
        return validate.format_500_error(request)
