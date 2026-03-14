"""Эндпоинты пользователей: список, получение по id (только id и name для фронта)."""

from aiohttp import web
from aiohttp_apispec import docs
from pydantic import BaseModel, field_validator

from api import validate
from config import logger
from docs import schems as sh
from functions import users as users_fns


def _user_to_response(row: dict) -> dict:
    """В ответ на фронт только id и name."""
    return {"id": str(row["user_id"]), "name": row["name"]}


class User_id_path(BaseModel):
    model_config = {"extra": "forbid"}

    user_id: str

    @field_validator("user_id")
    @classmethod
    def user_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("user_id не может быть пустым")
        return v


@docs(
    tags=["Users"],
    summary="Список пользователей",
    description="Возвращает всех пользователей (id, name) для выбора на фронте.",
    responses={
        200: {"description": "Список пользователей", "schema": sh.UserListResponseSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
)
async def list_users(request: web.Request) -> web.Response:
    try:
        items = await users_fns.list_users()
        out = [_user_to_response(r) for r in items]
        return web.json_response({"items": out, "total": len(out)}, status=200)
    except Exception:
        logger.exception("list_users handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["Users"],
    summary="Получить пользователя по id",
    description="Возвращает одного пользователя (id, name). 404 если не найден.",
    responses={
        200: {"description": "Пользователь найден", "schema": sh.UserSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "path",
            "name": "user_id",
            "schema": {"type": "string", "format": "uuid"},
            "required": True,
            "description": "UUID пользователя",
        },
    ],
)
@validate.validate(User_id_path)
async def get_user(request: web.Request, parsed: User_id_path) -> web.Response:
    try:
        user = await users_fns.get_user(parsed.user_id)
        if user is None:
            raise web.HTTPNotFound()
        return web.json_response(_user_to_response(user), status=200)
    except web.HTTPNotFound:
        raise
    except Exception:
        logger.exception("get_user handler failed")
        return validate.format_500_error(request)
