"""API правил отбора: возраст (мин/макс), пол, заработок."""

from typing import Optional

from aiohttp import web
from aiohttp_apispec import docs, request_schema
from pydantic import BaseModel, field_validator

from api import validate
from api.validate import validate_uuid
from config import logger
from docs import schems as sh
from functions import rules as rules_fns


LIMIT_MAX = 500
STRING_FIELD_MAX = 500


class Rules_list(BaseModel):
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


class Rule_create(BaseModel):
    model_config = {"extra": "forbid"}

    rule_id: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    gender: Optional[str] = None
    income: Optional[int] = None

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

    @field_validator("rule_id")
    @classmethod
    def rule_id_uuid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_uuid(v, "rule_id")


class Rule_update(BaseModel):
    model_config = {"extra": "forbid"}

    min_age: Optional[int] = None
    max_age: Optional[int] = None
    gender: Optional[str] = None
    income: Optional[int] = None

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


class Rule_id_path(BaseModel):
    model_config = {"extra": "forbid"}
    rule_id: str

    @field_validator("rule_id")
    @classmethod
    def rule_id_uuid(cls, v: str) -> str:
        return validate_uuid(v, "rule_id")


@docs(
    tags=["Admin"],
    summary="Список правил",
    description="Возвращает список правил отбора (возраст, пол, заработок). Требуется JWT админа.",
    security=validate.SECURITY_ADMIN_BEARER,
    responses={
        200: {"description": "Список правил", "schema": sh.RuleListResponseSchema},
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
            "description": "Максимальное количество элементов. Опционально, по умолчанию 50.",
            "default": 50,
        },
    ],
)
@validate.validate(Rules_list, require_admin=True)
async def list_rules(request: web.Request, parsed: Rules_list) -> web.Response:
    try:
        items, total = await rules_fns.list_rules(parsed.offset, parsed.limit)
        return web.json_response({"items": items, "total": total}, status=200)
    except Exception:
        logger.exception("list_rules handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Admin"],
    summary="Получить правило",
    description="Возвращает одно правило по rule_id. Требуется JWT админа. В пути: **обязательный** — rule_id (UUID).",
    security=validate.SECURITY_ADMIN_BEARER,
    responses={
        200: {"description": "Правило получено", "schema": sh.RuleDetailSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "path",
            "name": "rule_id",
            "type": "string",
            "required": True,
            "description": "Идентификатор правила (UUID). Обязательный параметр пути.",
        }
    ],
)
@validate.validate(Rule_id_path, require_admin=True)
async def get_rule(request: web.Request, parsed: Rule_id_path) -> web.Response:
    try:
        response = await rules_fns.get_rule(parsed.rule_id)
        if response is None:
            raise web.HTTPNotFound()
        return web.json_response(response, status=200)
    except web.HTTPNotFound:
        raise
    except Exception:
        logger.exception("get_rule handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Admin"],
    summary="Создать правило",
    description="Создаёт правило отбора: возраст мин/макс, пол, заработок. Требуется JWT админа. Все поля тела **опциональны** (rule_id при отсутствии сгенерируется; min_age, max_age, gender, income можно не передавать).",
    security=validate.SECURITY_ADMIN_BEARER,
    responses={
        201: {"description": "Правило создано", "schema": sh.RuleDetailSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
)
@request_schema(sh.RuleCreateSchema)
@validate.validate(Rule_create, require_admin=True)
async def create_rule(request: web.Request, parsed: Rule_create) -> web.Response:
    try:
        response = await rules_fns.create_rule(
            rule_id=parsed.rule_id,
            min_age=parsed.min_age,
            max_age=parsed.max_age,
            gender=parsed.gender,
            income=parsed.income,
        )
        if response is None:
            return validate.format_500_error(request)
        return web.json_response(response, status=201)
    except Exception:
        logger.exception("create_rule handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Admin"],
    summary="Изменить правило",
    description="Частично обновляет правило. Требуется JWT админа. В пути: **обязательный** — rule_id. Все поля тела **опциональны** (передайте только те, что нужно изменить: min_age, max_age, gender, income).",
    security=validate.SECURITY_ADMIN_BEARER,
    responses={
        200: {"description": "Правило обновлено", "schema": sh.RuleDetailSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "path",
            "name": "rule_id",
            "type": "string",
            "required": True,
            "description": "Идентификатор правила (UUID). Обязательный параметр пути.",
        }
    ],
)
@request_schema(sh.RuleUpdateSchema)
@validate.validate(Rule_update, require_admin=True)
async def update_rule(request: web.Request, parsed: Rule_update) -> web.Response:
    try:
        path = Rule_id_path(rule_id=request.match_info["rule_id"])
        rule_id = path.rule_id
        response = await rules_fns.update_rule(
            rule_id,
            min_age=parsed.min_age,
            max_age=parsed.max_age,
            gender=parsed.gender,
            income=parsed.income,
        )
        if response is None:
            raise web.HTTPNotFound()
        return web.json_response(response, status=200)
    except web.HTTPNotFound:
        raise
    except Exception:
        logger.exception("update_rule handler failed")
        return validate.format_500_error(request)
