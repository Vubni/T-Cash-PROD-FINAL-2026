"""Эндпоинты для регистрации и авторизации админов."""

from aiohttp import web
from aiohttp_apispec import docs, request_schema
from pydantic import BaseModel, field_validator

from api import validate
from config import logger
from docs import schems as sh
from functions import admin_users


class AdminRegisterBody(BaseModel):
    model_config = {"extra": "forbid"}

    login: str
    password: str

    @field_validator("login", "password")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Поле не может быть пустым")
        return v


class AdminApproveBody(BaseModel):
    model_config = {"extra": "forbid"}

    main_login: str
    main_password: str
    admin_id: int

    @field_validator("main_login", "main_password")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Поле не может быть пустым")
        return v


@docs(
    tags=["Admin"],
    summary="Регистрация обычного админа (заявка)",
    description="Создаёт обычного админа с approved = false, которого потом должен одобрить главный админ.",
    responses={
        201: {"description": "Заявка создана"},
        409: {"description": "Такой login уже существует"},
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
                "main_admin": created["main_admin"],
                "approved": created["approved"],
            },
            status=201,
        )
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

        return web.json_response(
            {
                "admin_id": admin["admin_id"],
                "login": admin["login"],
                "main_admin": admin["main_admin"],
                "approved": admin["approved"],
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
    description="Главный админ по своим логину/паролю одобряет admin_id (ставит approved = true).",
    responses={
        200: {"description": "Админ одобрен", "schema": sh.AdminAuthResponseSchema},
        401: {"description": "Неверные данные главного админа"},
        404: {"description": "Админ для одобрения не найден"},
        **sh.RESPONSES_HTTP_ERROR,
    },
)
@request_schema(sh.AdminApproveSchema)
@validate.validate(AdminApproveBody)
async def approve_admin(request: web.Request, parsed: AdminApproveBody) -> web.Response:
    try:
        updated = await admin_users.approve_admin(parsed.main_login, parsed.main_password, parsed.admin_id)
        if updated is None:
            raise web.HTTPUnauthorized(text="invalid main admin credentials or not main_admin")
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

