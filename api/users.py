"""Эндпоинт пользователей: проверить, существует ли пользователь по user_id."""

from aiohttp import web
from aiohttp_apispec import docs
from pydantic import BaseModel, field_validator

from api import validate
from config import logger
from docs import schems as sh
from functions import users as users_fns


class UserExistsPath(BaseModel):
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
    summary="Проверить, существует ли пользователь",
    description="Возвращает флаг exists по user_id.",
    responses={
        200: {"description": "Результат проверки", "schema": sh.UserExistsResponseSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "path",
            "name": "user_id",
            "type": "string",
            "format": "uuid",
            "required": True,
            "description": "UUID пользователя",
        },
    ],
)
@validate.validate(UserExistsPath)
async def user_exists(request: web.Request, parsed: UserExistsPath) -> web.Response:
    try:
        exists = await users_fns.user_exists(parsed.user_id)
        return web.json_response({"user_id": parsed.user_id, "exists": exists}, status=200)
    except Exception:
        logger.exception("user_exists handler failed")
        return validate.format_500_error(request)

