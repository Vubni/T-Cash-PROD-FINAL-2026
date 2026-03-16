from typing import Optional
import os

from aiohttp import web
from aiohttp_apispec import docs, request_schema
from pydantic import BaseModel, field_validator, model_validator

from api import validate
from config import logger
from docs import schemas as sh
from functions import audit as audit_fns
from functions import categories as cat_fns
from functions import rules as rules_fns


def _admin_actor(request: web.Request) -> str:
    """Идентификатор админа для audit_log"""
    payload = request.get("admin_payload") or {}
    return f"admin:{payload.get('admin_id', '')}"


LIMIT_MAX = 500
STRING_FIELD_MAX_LENGTH = 500


class Admin_categories_list(BaseModel):
    model_config = {"extra": "forbid"}

    offset: int = 0
    limit: int = 10
    status: Optional[str] = "running"

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

    @field_validator("status")
    @classmethod
    def status_allowed(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return "running"
        allowed = {"running", "paused", "archived"}
        value = v.strip().lower()
        if value not in allowed:
            raise ValueError(f"status must be one of: {', '.join(sorted(allowed))}")
        return value


RATE_MIN_LIMIT = 0
RATE_MAX_LIMIT = 100


class Admin_category_create(BaseModel):
    model_config = {"extra": "forbid"}

    name: str
    subtitle: str
    budget_amount: float
    rate_min: int
    rate_max: int

    @field_validator("name", "subtitle")
    @classmethod
    def check_non_empty_strings(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        if len(v) > STRING_FIELD_MAX_LENGTH:
            raise ValueError(f"Field cannot exceed {STRING_FIELD_MAX_LENGTH} characters")
        return v

    @field_validator("rate_min", "rate_max")
    @classmethod
    def check_rate_range(cls, v: int) -> int:
        if v < RATE_MIN_LIMIT or v > RATE_MAX_LIMIT:
            raise ValueError(f"rate must be between {RATE_MIN_LIMIT} and {RATE_MAX_LIMIT}")
        return v

    @model_validator(mode="after")
    def check_budget_and_rate(self) -> "Admin_category_create":
        if self.budget_amount < 0:
            raise ValueError("budget_amount cannot be negative")
        if self.rate_min > self.rate_max:
            raise ValueError("rate_min cannot be greater than rate_max")
        return self


class Admin_category_update(BaseModel):
    model_config = {"extra": "forbid"}

    category_id: str
    name: Optional[str] = None
    subtitle: Optional[str] = None
    budget_amount: Optional[float] = None
    icon_path: Optional[str] = None
    rate_min: Optional[int] = None
    rate_max: Optional[int] = None
    status: Optional[str] = None

    @field_validator("name", "subtitle")
    @classmethod
    def check_string_length(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty")
        if len(v) > STRING_FIELD_MAX_LENGTH:
            raise ValueError(f"Field cannot exceed {STRING_FIELD_MAX_LENGTH} characters")
        return v

    @field_validator("icon_path")
    @classmethod
    def icon_path_length(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            return None
        if len(v) > STRING_FIELD_MAX_LENGTH:
            raise ValueError(f"icon_path cannot exceed {STRING_FIELD_MAX_LENGTH} characters")
        return v

    @field_validator("rate_min", "rate_max")
    @classmethod
    def check_rate_range(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < RATE_MIN_LIMIT or v > RATE_MAX_LIMIT):
            raise ValueError(f"rate must be between {RATE_MIN_LIMIT} and {RATE_MAX_LIMIT}")
        return v

    @field_validator("status")
    @classmethod
    def status_allowed(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"running", "paused", "archived"}
        value = v.strip().lower()
        if value not in allowed:
            raise ValueError(f"status must be one of: {', '.join(sorted(allowed))}")
        return value

    @model_validator(mode="after")
    def check_payload(self) -> "Admin_category_update":
        has_any_value = any(value is not None for k, value in self.model_dump().items() if k != "category_id")
        if not has_any_value:
            raise ValueError("At least one field must be provided")
        if self.budget_amount is not None and self.budget_amount < 0:
            raise ValueError("budget_amount cannot be negative")
        if (self.rate_min is not None and self.rate_max is not None) and self.rate_min > self.rate_max:
            raise ValueError("rate_min cannot be greater than rate_max")
        return self


class Category_id_path(BaseModel):
    model_config = {"extra": "forbid"}

    category_id: str

    @field_validator("category_id")
    @classmethod
    def category_id_uuid(cls, v: str) -> str:
        return validate.validate_uuid(v, "category_id")


GENDER_ALLOWED = ("male", "female", "other")


class Category_rule_create(BaseModel):
    """Тело запроса создания правила и привязки к категории. category_id приходит из пути."""

    model_config = {"extra": "forbid"}

    category_id: str
    rule_id: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    gender: Optional[str] = None
    income: Optional[int] = None

    @field_validator("category_id")
    @classmethod
    def category_id_uuid(cls, v: str) -> str:
        return validate.validate_uuid(v, "category_id")

    @field_validator("rule_id")
    @classmethod
    def rule_id_uuid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate.validate_uuid(v, "rule_id")

    @field_validator("min_age", "max_age")
    @classmethod
    def age_non_negative(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("age must be non-negative")
        return v

    @field_validator("income")
    @classmethod
    def income_non_negative(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("income must be non-negative")
        return v

    @field_validator("gender")
    @classmethod
    def gender_allowed(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if v.strip().lower() not in GENDER_ALLOWED:
            raise ValueError(f"gender must be one of: {', '.join(GENDER_ALLOWED)}")
        return v.strip().lower()


@docs(
    tags=["Admin"],
    summary="Список категорий кэшбэка",
    description="Возвращает список категорий для админки. Используется для просмотра всех настроенных категорий вместе с бюджетом и диапазоном ставок. Требуется JWT админа.",
    security=validate.SECURITY_ADMIN_BEARER,
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
            "description": "Смещение для пагинации. Опционально, по умолчанию 0.",
            "default": 0,
        },
        {
            "in": "query",
            "name": "limit",
            "type": "integer",
            "required": False,
            "description": "Максимальное количество элементов в ответе. Опционально, по умолчанию 10.",
            "default": 10,
        },
        {
            "in": "query",
            "name": "status",
            "type": "string",
            "required": False,
            "description": "Статус категорий для вывода: running (запущены), paused (на паузе) или archived (архив). По умолчанию running.",
            "default": "running",
        },
    ],
)
@validate.validate(Admin_categories_list, require_admin=True)
async def list_categories(request: web.Request, parsed: Admin_categories_list) -> web.Response:
    try:
        items, total = await cat_fns.list_categories(parsed.offset, parsed.limit, status=parsed.status)
        return web.json_response({"items": items, "total": total}, status=200)
    except Exception:
        logger.exception("list_categories handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Admin"],
    summary="Создать категорию кэшбэка",
    description="Создаёт новую категорию с бюджетом и диапазоном кэшбэка (rate_min, rate_max в %). Правило (rule_id) привязывается отдельно. Требуется JWT админа. **Обязательные** поля: name, subtitle, budget_amount, rate_min, rate_max. **Опционально**: category_id.",
    security=validate.SECURITY_ADMIN_BEARER,
    responses={
        201: {"description": "Категория создана", "schema": sh.CategoryDetailSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
)
@request_schema(sh.CategoryCreateSchema)
@validate.validate(Admin_category_create, require_admin=True)
async def create_category(request: web.Request, parsed: Admin_category_create) -> web.Response:
    try:
        response = await cat_fns.create_category(
            name=parsed.name,
            subtitle=parsed.subtitle,
            budget_amount=int(parsed.budget_amount),
            rate_min=parsed.rate_min,
            rate_max=parsed.rate_max,
        )
        if response is None:
            return validate.format_500_error(request)
        entity_id = response.get("id") or response.get("category_id")
        if entity_id:
            await audit_fns.write_audit(
                "category",
                str(entity_id),
                "create",
                _admin_actor(request),
                details={"name": parsed.name},
            )
        return web.json_response(response, status=201)
    except Exception:
        logger.exception("create_category handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Admin"],
    summary="Получить категорию кэшбэка",
    description="Возвращает одну категорию целиком: метаданные, бюджет, диапазон ставок, аудиторию, правило и историю изменений. Требуется JWT админа.",
    security=validate.SECURITY_ADMIN_BEARER,
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
            "description": "Идентификатор категории (UUID). Обязательный параметр пути.",
        }
    ],
)
@validate.validate(Category_id_path, require_admin=True)
async def get_category(request: web.Request, parsed: Category_id_path) -> web.Response:
    try:
        response = await cat_fns.get_category(parsed.category_id)
        if response is None:
            return validate.format_404_error(request, message="Категория не найдена")
        return web.json_response(response, status=200)
    except Exception:
        logger.exception("get_category handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Admin"],
    summary="Загрузить иконку для категории",
    description=(
        "Загружает файл иконки для указанной категории и сохраняет относительный путь в поле icon_path. "
        "Фронтенд затем может получать эту иконку по URL `/icons/<filename>` (относительно хоста бэкенда). "
        "Требуется JWT админа. Тело запроса — multipart/form-data с полем `file`."
    ),
    security=validate.SECURITY_ADMIN_BEARER,
    responses={
        200: {"description": "Иконка загружена, категория обновлена", "schema": sh.CategoryDetailSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "path",
            "name": "category_id",
            "type": "string",
            "required": True,
            "description": "Идентификатор категории (UUID), для которой загружается иконка.",
        }
    ],
)
@validate.validate(Category_id_path, require_admin=True)
async def upload_category_icon(request: web.Request, parsed: Category_id_path) -> web.Response:
    try:
        category = await cat_fns.get_category(parsed.category_id)
        if category is None:
            return validate.format_404_error(request, message="Категория не найдена")
        if (category.get("status") or "").lower() == "archived":
            return validate.format_409_error(request, message="Нельзя изменять иконку архивной категории")

        reader = await request.multipart()
        field = await reader.next()

        if field is None or field.name not in ("file", "icon"):
            return validate.format_400_error(request, message="Ожидается файл в поле 'file' или 'icon'")

        filename = field.filename
        if not filename:
            return validate.format_400_error(request, message="Имя файла иконки не задано")

        _name, ext = os.path.splitext(filename)
        if not ext:
            ext = ".png"
        ext = ext.lower()

        chunks = []
        while True:
            chunk = await field.read_chunk()
            if not chunk:
                break
            chunks.append(chunk)
        file_content = b"".join(chunks)

        icon_rel_path = cat_fns.save_category_icon_file(parsed.category_id, file_content, ext)
        updated = await cat_fns.update_category(parsed.category_id, icon_path=icon_rel_path)
        if updated is None:
            return validate.format_404_error(request, message="Категория не найдена")
        await audit_fns.write_audit(
            "category",
            parsed.category_id,
            "icon_upload",
            _admin_actor(request),
            details={"icon_path": icon_rel_path},
        )
        return web.json_response(updated, status=200)
    except Exception:
        logger.exception("upload_category_icon handler failed")
        return validate.format_500_error(request)


class Category_rule_update(BaseModel):
    """Path: category_id. Body: опциональные поля правила."""

    model_config = {"extra": "forbid"}

    category_id: str
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    gender: Optional[str] = None
    income: Optional[int] = None

    @field_validator("gender")
    @classmethod
    def gender_allowed(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if v.strip().lower() not in GENDER_ALLOWED:
            raise ValueError(f"gender must be one of: {', '.join(GENDER_ALLOWED)}")
        return v.strip().lower()

    @field_validator("min_age", "max_age")
    @classmethod
    def age_non_negative(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("age must be non-negative")
        return v

    @field_validator("income")
    @classmethod
    def income_non_negative(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("income must be non-negative")
        return v

    @field_validator("category_id")
    @classmethod
    def category_id_uuid(cls, v: str) -> str:
        return validate.validate_uuid(v, "category_id")


@docs(
    tags=["Admin"],
    summary="Получить правило категории",
    description="Возвращает правило отбора (возраст, пол, заработок), привязанное к категории. Требуется JWT админа. 404, если у категории нет правила.",
    security=validate.SECURITY_ADMIN_BEARER,
    responses={
        200: {"description": "Правило получено", "schema": sh.RuleDetailSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {"in": "path", "name": "category_id", "type": "string", "required": True, "description": "Идентификатор категории (UUID)."},
    ],
)
@validate.validate(Category_id_path, require_admin=True)
async def get_category_rule(request: web.Request, parsed: Category_id_path) -> web.Response:
    try:
        category = await cat_fns.get_category(parsed.category_id)
        if category is None:
            return validate.format_404_error(request, message="Категория не найдена")
        rule = category.get("rule")
        if not rule or not rule.get("rule_id"):
            return validate.format_404_error(request, message="У категории нет правила")
        return web.json_response(rule, status=200)
    except Exception:
        logger.exception("get_category_rule handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Admin"],
    summary="Создать правило и привязать к категории",
    description="Создаёт правило отбора (возраст мин/макс, пол, заработок) и привязывает его к указанной категории. Требуется JWT админа. Категория должна существовать. Все поля тела **опциональны** (rule_id при отсутствии сгенерируется; min_age, max_age, gender, income можно не передавать).",
    security=validate.SECURITY_ADMIN_BEARER,
    responses={
        201: {"description": "Правило создано и привязано к категории", "schema": sh.RuleDetailSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "path",
            "name": "category_id",
            "type": "string",
            "required": True,
            "description": "Идентификатор категории (UUID). К этой категории будет привязано созданное правило.",
        }
    ],
)
@request_schema(sh.RuleCreateSchema)
@validate.validate(Category_rule_create, require_admin=True)
async def create_category_rule(request: web.Request, parsed: Category_rule_create) -> web.Response:
    try:
        category = await cat_fns.get_category(parsed.category_id)
        if category is None:
            return validate.format_404_error(request, message="Категория не найдена")
        if (category.get("status") or "").lower() == "archived":
            return validate.format_409_error(request, message="Нельзя создавать правило для архивной категории")
        rule = await rules_fns.create_rule(
            min_age=parsed.min_age,
            max_age=parsed.max_age,
            gender=parsed.gender,
            income=parsed.income,
        )
        if rule is None:
            return validate.format_500_error(request)
        updated = await cat_fns.update_category(parsed.category_id, rule_id=rule["rule_id"])
        if updated is None:
            return validate.format_500_error(request)
        await audit_fns.write_audit(
            "category",
            parsed.category_id,
            "rule_attached",
            _admin_actor(request),
            details={"rule_id": str(rule["rule_id"])},
        )
        return web.json_response(rule, status=201)
    except Exception:
        logger.exception("create_category_rule handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Admin"],
    summary="Изменить правило категории",
    description="Частично обновляет правило отбора, привязанное к категории. Требуется JWT админа. Все поля тела опциональны.",
    security=validate.SECURITY_ADMIN_BEARER,
    responses={
        200: {"description": "Правило обновлено", "schema": sh.RuleDetailSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {"in": "path", "name": "category_id", "type": "string", "required": True, "description": "Идентификатор категории (UUID)."},
    ],
)
@request_schema(sh.RuleUpdateSchema)
@validate.validate(Category_rule_update, require_admin=True)
async def update_category_rule(request: web.Request, parsed: Category_rule_update) -> web.Response:
    try:
        category_id = parsed.category_id
        category = await cat_fns.get_category(category_id)
        if category is None:
            return validate.format_404_error(request, message="Категория не найдена")
        if (category.get("status") or "").lower() == "archived":
            return validate.format_409_error(request, message="Нельзя изменять правило архивной категории")
        rule_id = (category.get("rule") or {}).get("rule_id")
        if not rule_id:
            return validate.format_404_error(request, message="У категории нет правила")
        response = await rules_fns.update_rule(
            rule_id,
            min_age=parsed.min_age,
            max_age=parsed.max_age,
            gender=parsed.gender,
            income=parsed.income,
        )
        if response is None:
            return validate.format_404_error(request, message="Правило не найдено")
        return web.json_response(response, status=200)
    except Exception:
        logger.exception("update_category_rule handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Admin"],
    summary="Удалить правило категории",
    description="Отвязывает и удаляет правило отбора у категории. Требуется JWT админа. 404, если у категории нет правила.",
    security=validate.SECURITY_ADMIN_BEARER,
    responses={
        204: {"description": "Правило удалено"},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {"in": "path", "name": "category_id", "type": "string", "required": True, "description": "Идентификатор категории (UUID)."},
    ],
)
@validate.validate(Category_id_path, require_admin=True)
async def delete_category_rule(request: web.Request, parsed: Category_id_path) -> web.Response:
    try:
        category = await cat_fns.get_category(parsed.category_id)
        if category is None:
            return validate.format_404_error(request, message="Категория не найдена")
        if (category.get("status") or "").lower() == "archived":
            return validate.format_409_error(request, message="Нельзя удалять правило архивной категории")
        rule_id = (category.get("rule") or {}).get("rule_id")
        if not rule_id:
            return validate.format_404_error(request, message="У категории нет правила")
        await rules_fns.delete_rule(rule_id)
        return web.Response(status=204)
    except Exception:
        logger.exception("delete_category_rule handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Admin"],
    summary="Изменить категорию кэшбэка",
    description="Частично обновляет категорию. Можно менять бюджет и диапазон кэшбэка (rate_min, rate_max). Правила — через POST/PATCH/DELETE .../categories/{id}/rule. Требуется JWT админа. Все поля **опциональны**: name, subtitle, budget_amount, rate_min, rate_max, status.",
    security=validate.SECURITY_ADMIN_BEARER,
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
            "description": "Идентификатор категории (UUID). Обязательный параметр пути.",
        }
    ],
)
@request_schema(sh.CategoryUpdateSchema)
@validate.validate(Admin_category_update, require_admin=True)
async def update_category(request: web.Request, parsed: Admin_category_update) -> web.Response:
    try:
        response = await cat_fns.update_category(
            parsed.category_id,
            name=parsed.name,
            subtitle=parsed.subtitle,
            icon_path=parsed.icon_path,
            budget_amount=int(parsed.budget_amount) if parsed.budget_amount is not None else None,
            rate_min=parsed.rate_min,
            rate_max=parsed.rate_max,
            status=parsed.status,
        )
        if response is None:
            return validate.format_404_error(request, message="Категория не найдена")
        details = {
            k: v for k, v in parsed.model_dump().items()
            if k != "category_id" and v is not None
        }
        await audit_fns.write_audit(
            "category",
            parsed.category_id,
            "update",
            _admin_actor(request),
            details=details if details else None,
        )
        return web.json_response(response, status=200)
    except ValueError as e:
        return validate.format_409_error(request, message=str(e))
    except Exception:
        logger.exception("update_category handler failed")
        return validate.format_500_error(request)


class Category_status_path(BaseModel):
    model_config = {"extra": "forbid"}

    category_id: str

    @field_validator("category_id")
    @classmethod
    def category_id_uuid(cls, v: str) -> str:
        return validate.validate_uuid(v, "category_id")


async def _change_category_status(
    request: web.Request,
    parsed: Category_status_path,
    new_status: str,
) -> web.Response:
    try:
        response = await cat_fns.update_category_status(parsed.category_id, new_status)
        if response is None:
            return validate.format_404_error(request, message="Категория не найдена")
        await audit_fns.write_audit(
            "category",
            parsed.category_id,
            new_status,
            _admin_actor(request),
            details={"status": new_status},
        )
        return web.json_response(response, status=200)
    except ValueError as e:
        return validate.format_409_error(request, message=str(e))
    except Exception:
        logger.exception("category status change handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Admin"],
    summary="Запустить категорию кэшбэка",
    description="Переводит категорию в статус running (запущена) и включает её в расчёты и выдачу клиенту. Требуется JWT админа.",
    security=validate.SECURITY_ADMIN_BEARER,
    responses={
        200: {"description": "Статус категории изменён на running", "schema": sh.CategoryDetailSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "path",
            "name": "category_id",
            "type": "string",
            "required": True,
            "description": "Идентификатор категории (UUID). Обязательный параметр пути.",
        }
    ],
)
@validate.validate(Category_status_path, require_admin=True)
async def run_category(request: web.Request, parsed: Category_status_path) -> web.Response:
    return await _change_category_status(request, parsed, "running")


@docs(
    tags=["Admin"],
    summary="Поставить категорию на паузу",
    description="Переводит категорию в статус paused — категория скрывается из клиентских расчётов, но остаётся в системе. Требуется JWT админа.",
    security=validate.SECURITY_ADMIN_BEARER,
    responses={
        200: {"description": "Статус категории изменён на paused", "schema": sh.CategoryDetailSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "path",
            "name": "category_id",
            "type": "string",
            "required": True,
            "description": "Идентификатор категории (UUID). Обязательный параметр пути.",
        }
    ],
)
@validate.validate(Category_status_path, require_admin=True)
async def pause_category(request: web.Request, parsed: Category_status_path) -> web.Response:
    return await _change_category_status(request, parsed, "paused")


@docs(
    tags=["Admin"],
    summary="Отправить категорию в архив",
    description="Переводит категорию в статус archived — мягкое удаление. Категория не участвует в расчётах и не отображается клиенту, но остаётся в админке. Требуется JWT админа.",
    security=validate.SECURITY_ADMIN_BEARER,
    responses={
        200: {"description": "Статус категории изменён на archived", "schema": sh.CategoryDetailSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "path",
            "name": "category_id",
            "type": "string",
            "required": True,
            "description": "Идентификатор категории (UUID). Обязательный параметр пути.",
        }
    ],
)
@validate.validate(Category_status_path, require_admin=True)
async def archive_category(request: web.Request, parsed: Category_status_path) -> web.Response:
    return await _change_category_status(request, parsed, "archived")
