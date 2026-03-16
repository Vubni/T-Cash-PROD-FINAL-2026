from aiohttp import web
from aiohttp_apispec import docs, request_schema
from pydantic import BaseModel, field_validator

from api import validate
from config import logger
from docs import schemas as sh
from functions import users as users_fns
from functions import wordly as wordly_fns


class Wordly_start(BaseModel):
    model_config = {"extra": "forbid"}


class Wordly_guess(BaseModel):
    model_config = {"extra": "forbid"}

    game_id: str
    guess: str

    @field_validator("game_id")
    @classmethod
    def game_id_not_empty(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("game_id cannot be empty")
        return v.strip()

    @field_validator("guess")
    @classmethod
    def guess_not_empty(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("guess cannot be empty")
        return v.strip()


class Wordly_state(BaseModel):
    model_config = {"extra": "forbid"}

    game_id: str

    @field_validator("game_id")
    @classmethod
    def game_id_not_empty(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("game_id cannot be empty")
        return v.strip()


class Wordly_status(BaseModel):
    model_config = {"extra": "forbid"}


@docs(
    tags=["T-Word"],
    summary="Начать новую игру T-Word",
    description="Создаёт новую игру и возвращает идентификатор, длину слова и количество попыток.",
    security=validate.SECURITY_USER_BEARER,
    responses={
        200: {"description": "Игра создана", "schema": sh.WordlyStartResponseSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
)
@validate.validate(Wordly_start, require_auth=True)
async def start_game(request: web.Request, _: Wordly_start) -> web.Response:
    try:
        payload = request.get("user_payload") or {}
        user_id = payload.get("user_id")
        if user_id is None:
            return validate.format_401_error(request, "Токен пользователя отсутствует или не содержит user_id")
        if not await users_fns.user_exists(user_id):
            return validate.format_404_error(request, message="Пользователь не найден")

        state = await wordly_fns.start_game(user_id=user_id)
        return web.json_response(state, status=200)
    except Exception:
        logger.exception("wordly start_game handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["T-Word"],
    summary="Сделать попытку в игре T-Word",
    description=(
        "Принимает угадываемое слово и возвращает результат по каждой букве: "
        "correct (буква на своём месте), present (есть в слове, но в другой позиции), "
        "absent (буквы нет в слове)."
    ),
    security=validate.SECURITY_USER_BEARER,
    responses={
        200: {"description": "Результат попытки", "schema": sh.WordlyGuessResponseSchema},
        400: {"description": "Некорректная попытка", "schema": sh.HttpErrorSchema},
        404: {"description": "Игра не найдена", "schema": sh.HttpErrorSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
)
@request_schema(sh.WordlyGuessRequestSchema)
@validate.validate(Wordly_guess, require_auth=True)
async def make_guess(request: web.Request, parsed: Wordly_guess) -> web.Response:
    try:
        payload = request.get("user_payload") or {}
        user_id = payload.get("user_id")
        if user_id is None:
            return validate.format_401_error(request, "Токен пользователя отсутствует или не содержит user_id")
        if not await users_fns.user_exists(user_id):
            return validate.format_404_error(request, message="Пользователь не найден")

        result = await wordly_fns.make_guess(parsed.game_id, parsed.guess, user_id=user_id)
        return web.json_response(result, status=200)
    except wordly_fns.GameNotFoundError:
        return validate.format_404_error(request, message="Игра не найдена")
    except wordly_fns.GameFinishedError as exc:
        return validate.format_400_error(request, str(exc))
    except wordly_fns.InvalidGuessError as exc:
        return validate.format_400_error(request, str(exc))
    except Exception:
        logger.exception("wordly make_guess handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["T-Word"],
    summary="Получить текущее состояние игры T-Word",
    description="Возвращает статус игры, число попыток и историю ходов.",
    security=validate.SECURITY_USER_BEARER,
    responses={
        200: {"description": "Состояние игры", "schema": sh.WordlyStateResponseSchema},
        404: {"description": "Игра не найдена", "schema": sh.HttpErrorSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "query",
            "name": "game_id",
            "type": "string",
            "required": True,
            "description": "Идентификатор игры, полученный из /api/v1/wordly/start.",
        }
    ],
)
@validate.validate(Wordly_state, require_auth=True)
async def get_state(request: web.Request, parsed: Wordly_state) -> web.Response:
    try:
        payload = request.get("user_payload") or {}
        user_id = payload.get("user_id")
        if user_id is None:
            return validate.format_401_error(request, "Токен пользователя отсутствует или не содержит user_id")
        if not await users_fns.user_exists(user_id):
            return validate.format_404_error(request, message="Пользователь не найден")

        state = await wordly_fns.get_state(parsed.game_id, user_id=user_id)
        return web.json_response(state, status=200)
    except wordly_fns.GameNotFoundError:
        return validate.format_404_error(request, message="Игра не найдена")
    except Exception:
        logger.exception("wordly get_state handler failed")
        return validate.format_500_error(request)


@docs(
    tags=["T-Word"],
    summary="Получить статус участия пользователя в игре T-Word",
    description=(
        "Возвращает, играл ли пользователь в T-Word и выигрывал ли он когда-либо (по данным user_winners)."
    ),
    security=validate.SECURITY_USER_BEARER,
    responses={
        200: {"description": "Статус участия пользователя", "schema": sh.WordlyUserStatusResponseSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
)
@validate.validate(Wordly_status, require_auth=True)
async def get_user_status(request: web.Request, _: Wordly_status) -> web.Response:
    try:
        payload = request.get("user_payload") or {}
        user_id = payload.get("user_id")
        if user_id is None:
            return validate.format_401_error(request, "Токен пользователя отсутствует или не содержит user_id")
        if not await users_fns.user_exists(user_id):
            return validate.format_404_error(request, message="Пользователь не найден")

        status = await wordly_fns.get_user_status(user_id=user_id)
        return web.json_response(status, status=200)
    except Exception:
        logger.exception("wordly get_user_status handler failed")
        return validate.format_500_error(request)

