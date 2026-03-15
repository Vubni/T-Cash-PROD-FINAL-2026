import secrets
import string
from typing import Any

import jwt
from aiohttp import web

from config import SECRET, logger

ADMIN_SCOPE = "admin"
USER_SCOPE = "user"


def create_token(payload: dict[str, Any]) -> str:
    """Создаёт JWT-токен по переданному payload."""
    return jwt.encode(payload, SECRET, algorithm="HS256")


def check_token(token: str) -> dict[str, Any] | None:
    """Декодирует и валидирует JWT, возвращает payload или None."""
    try:
        decoded = jwt.decode(token, SECRET, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def check_authorization(request: web.Request) -> dict[str, Any] | None:
    """
    Проверка токена клиента (не админа).
    Принимает заголовок:
    - "Authorization: Bearer <token>"
    - "Authorization: <token>" (как шлёт Swagger UI).
    Возвращает payload или None.
    """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        auth_header = auth_header.strip()
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
        else:
            token = auth_header

        if not token:
            return None

        result = check_token(token)
        if isinstance(result, dict) and result.get("scope") == ADMIN_SCOPE:
            return None
        return result
    except Exception as e:
        logger.error("check_authorization error: %s", e)
        return None


async def check_admin_authorization(request: web.Request) -> dict[str, Any] | None:
    """
    Проверка Bearer-токена админа.
    Возвращает payload с admin_id, main_admin, approved или None.
    Принимает заголовок:
    - \"Authorization: Bearer <token>\"
    - \"Authorization: <token>\" (для Swagger UI).
    """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        auth_header = auth_header.strip()
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
        else:
            token = auth_header
        if not token:
            return None
        decoded = check_token(token)
        if not isinstance(decoded, dict) or decoded.get("scope") != ADMIN_SCOPE:
            return None
        return decoded
    except Exception as e:
        logger.error("check_admin_authorization error: %s", e)
        return None


def generate_unique_code(length: int = 32) -> str:
    """Генерация рандомного кода (латиница, цифры, символ '_')."""
    characters = string.ascii_letters + string.digits + "_"
    return "".join(secrets.choice(characters) for _ in range(length))
