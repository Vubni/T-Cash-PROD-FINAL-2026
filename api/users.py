"""Эндпоинт пользователей: авторизовать пользователя по user_id и выдать JWT-токен."""

from aiohttp import web
from aiohttp_apispec import docs
from pydantic import BaseModel, field_validator

from api import validate
from config import logger
from docs import schems as sh
from functions import users as users_fns
import core


class UserAuthPath(BaseModel):
    model_config = {"extra": "forbid"}

    user_id: int

    @field_validator("user_id", mode="before")
    @classmethod
    def user_id_bigint(cls, v: str | int) -> int:
        n = validate.validate_user_id(v, "user_id")
        if n < 1:
            raise ValueError("user_id must be a positive integer")
        return n


@docs(
    tags=["Users"],
    summary="Авторизовать пользователя и выдать JWT-токен",
    description=(
        "По переданному user_id (BIGINT) авторизует пользователя и возвращает JWT-токен для клиентских запросов "
        "(offers/run, client/selection) в заголовке Authorization: Bearer <token>. "
        "Если пользователь не найден, возвращает 404 NOT_FOUND."
    ),
    responses={
        200: {"description": "Пользователь авторизован, токен выдан", "schema": sh.UserAuthResponseSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "path",
            "name": "user_id",
            "type": "integer",
            "format": "int64",
            "required": True,
            "description": "ID пользователя (BIGINT). Обязательный параметр пути.",
        },
    ],
)
@validate.validate(UserAuthPath)
async def user_auth(request: web.Request, parsed: UserAuthPath) -> web.Response:
    try:
        exists = await users_fns.user_exists(parsed.user_id)
        if not exists:
            return validate.format_404_error(request, message="Пользователь не найден")

        payload = {
            "scope": core.USER_SCOPE,
            "user_id": parsed.user_id,
        }
        token = core.create_token(payload)

        return web.json_response(
            {
                "user_id": parsed.user_id,
                "token": token,
            },
            status=200,
        )
    except Exception:
        logger.exception("user_auth handler failed")
        return validate.format_500_error(request)
