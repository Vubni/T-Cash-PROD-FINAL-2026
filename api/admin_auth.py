"""Эндпоинты для регистрации и авторизации админов."""

from aiohttp import web
from aiohttp_apispec import docs, request_schema
from pydantic import BaseModel, field_validator

import core
from api import validate
from config import logger
from docs import schems as sh
from functions import admin_users


class AdminRegisterBody(BaseModel):
    login: str
    password: str

    @field_validator("login", "password")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Поле не может быть пустым")
        return v.strip()


class AdminApproveBody(BaseModel):
    admin_id: int


class EmptyBody(BaseModel):
    model_config = {"extra": "ignore"}


@docs(
    tags=["Admin"],
    summary="Список заявок на админа",
    description="Возвращает список админов с approved = false (только для супер-админа).",
    security=validate.SECURITY_ADMIN_BEARER,
    responses={
        200: {"description": "Список заявок", "schema": sh.PendingAdminsResponseSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
)
@validate.validate(EmptyBody, require_super_admin=True)
async def list_pending(request: web.Request, parsed: EmptyBody) -> web.Response:
    try:
        items = await admin_users.list_pending_admins()
        return web.json_response({"items": items}, status=200)
    except Exception:
        logger.exception("list_pending handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Admin"],
    summary="Регистрация обычного админа (заявка)",
    description="Создаёт обычного админа с approved = false, которого потом должен одобрить главный админ.",
    responses={
        201: {"description": "Заявка создана"},
        409: {"description": "Такой login уже занят (в т.ч. логин главного админа по умолчанию — укажите другой)"},
        **sh.RESPONSES_HTTP_ERROR,
    },
)
@request_schema(sh.AdminRegisterSchema)
@validate.validate(AdminRegisterBody)
async def register_admin(request: web.Request, parsed: AdminRegisterBody) -> web.Response:
    try:
        created = await admin_users.create_admin(parsed.login, parsed.password)
        if created is None:
            raise web.HTTPConflict(text="admin with this login already exists")
        return web.json_response(
            {
                "admin_id": created["admin_id"],
                "login": created["login"],
                "approved": created["approved"],
            }, status=201)
    except web.HTTPError:
        raise
    except Exception:
        logger.exception("register_admin handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Admin"],
    summary="Логин админа",
    description="Проверяет логин/пароль. Если admin не approved — 403.",
    responses={
        200: {"description": "Успешный вход", "schema": sh.AdminAuthResponseSchema},
        401: {"description": "Неверный логин или пароль"},
        403: {"description": "Админ не одобрен главным админом"},
        **sh.RESPONSES_HTTP_ERROR,
    },
)
@request_schema(sh.AdminLoginSchema)
@validate.validate(AdminRegisterBody)
async def login_admin(request: web.Request, parsed: AdminRegisterBody) -> web.Response:
    try:
        admin = await admin_users.authenticate_admin(parsed.login, parsed.password)
        if admin is None:
            raise web.HTTPUnauthorized(text="invalid credentials")
        if not admin.get("approved"):
            raise web.HTTPForbidden(text="admin is not approved by main admin")

        payload = {
            "scope": core.ADMIN_SCOPE,
            "admin_id": admin["admin_id"],
            "main_admin": admin["main_admin"],
            "approved": admin["approved"],
        }
        token = core.create_token(payload)

        return web.json_response(
            {
                "admin_id": admin["admin_id"],
                "login": admin["login"],
                "main_admin": admin["main_admin"],
                "approved": admin["approved"],
                "token": token,
            },
            status=200,
        )
    except web.HTTPError:
        raise
    except Exception:
        logger.exception("login_admin handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Admin"],
    summary="Одобрить обычного админа",
    description="Супер-админ по Bearer-токену одобряет admin_id (ставит approved = true). Доступно только с токеном главного админа.",
    security=validate.SECURITY_ADMIN_BEARER,
    responses={
        200: {"description": "Админ одобрен", "schema": sh.AdminAuthResponseSchema},
        401: {"description": "Токен отсутствует или невалиден"},
        403: {"description": "Только супер-админ может одобрять админов"},
        404: {"description": "Админ для одобрения не найден"},
        **sh.RESPONSES_HTTP_ERROR,
    },
)
@request_schema(sh.AdminApproveSchema)
@validate.validate(AdminApproveBody, require_super_admin=True)
async def approve_admin(request: web.Request, parsed: AdminApproveBody) -> web.Response:
    try:
        updated = await admin_users.set_admin_approved(parsed.admin_id)
        if updated is None:
            raise web.HTTPNotFound(text="admin to approve not found")
        return web.json_response(
            {
                "admin_id": updated["admin_id"],
                "login": updated["login"],
                "main_admin": updated["main_admin"],
                "approved": updated["approved"],
            },
            status=200,
        )
    except web.HTTPError:
        raise
    except Exception:
        logger.exception("approve_admin handler failed")
        return validate.format_500_error(request)

