import asyncio
import re
import secrets
import string
import threading
import time
import uuid

from aiohttp import web
from functools import wraps
import jwt
from config import SECRET, logger

ADMIN_SCOPE = "admin"


async def check_authorization(request: web.Request):
    """Проверка Bearer-токена клиента (не админа)."""
    try:
        auth_header = request.headers.get("Authorization")

        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                result = check_token(parts[1])
                if isinstance(result, dict) and result.get("scope") == ADMIN_SCOPE:
                    return None
                return result
        return None
    except Exception as e:
        logger.error("check_authorization error: ", e)
        return None


async def check_admin_authorization(request: web.Request) -> dict | None:
    """
    Проверка Bearer-токена админа. Возвращает payload с admin_id, main_admin, approved
    или None при отсутствии/невалидном токене.
    Принимает заголовок "Authorization: Bearer <token>" или "Authorization: <token>"
    (для совместимости со Swagger UI, который может не добавлять префикс Bearer).
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


def validate_uuid(v: str) -> str:
    try:
        return str(uuid.UUID(v))
    except (ValueError, TypeError):
        return None


def create_token(payload) -> str:
    token = jwt.encode(payload, SECRET, algorithm="HS256")

    return token


def parse_uuid(value: str) -> str | None:
    try:
        return str(uuid.UUID(value))
    except (ValueError, TypeError):
        return None


def check_token(token):
    try:
        decoded = jwt.decode(token, SECRET, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    

def generate_unique_code(length:int=32):
    """Генерация рандомного кода из символов латиницы, цифры и _

    Args:
        length (int, optional): Длина кода. Defaults to 32.

    Returns:
        str: Сгенерированный код
    """
    characters = string.ascii_letters + string.digits + '_'
    return ''.join(secrets.choice(characters) for _ in range(length))


def is_domain_valid(domain):
    """Проверяет, соответствует ли домен стандартам (RFC 1035)."""
    segments = domain.split('.')
    for segment in segments:
        if not segment:
            return False
        if segment[0] == '-' or segment[-1] == '-':
            return False
        if not re.match(r'^[a-zA-Z0-9-]+$', segment):
            return False
    return True

def is_valid_email(email:str) -> bool:
    """Проверка реальности почты"""
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(regex, email):
        return False

    local_part, domain_part = email.split('@')

    if len(local_part) > 64:
        return False
    if local_part.startswith('.') or local_part.endswith('.'):
        return False
    if '..' in local_part:
        return False

    if not is_domain_valid(domain_part):
        return False
    if len(domain_part) > 255:
        return False

    return True
    

def is_hashable(obj):
    """Проверяет, является ли объект хешируемым."""
    try:
        hash(obj)
        return True
    except TypeError:
        return False

def cache_with_expiration(expiration_seconds: int):
    def decorator(func):
        cache = {}
        async_lock = None
        sync_lock = threading.Lock()

        def get_cache_key(*args, **kwargs):
            filtered_args = [arg for arg in args if is_hashable(arg)]
            filtered_kwargs = {k: v for k, v in kwargs.items() if is_hashable(v)}
            return (tuple(filtered_args), frozenset(filtered_kwargs.items()))

        @wraps(func)
        async def async_wrapped(*args, **kwargs):
            nonlocal async_lock
            if async_lock is None:
                async_lock = asyncio.Lock()
            async with async_lock:
                now = time.time()
                key = get_cache_key(*args, **kwargs)
                if key in cache:
                    result, timestamp = cache[key]
                    if now - timestamp < expiration_seconds:
                        return result
                result = await func(*args, **kwargs)
                cache[key] = (result, now)
                return result

        @wraps(func)
        def sync_wrapped(*args, **kwargs):
            with sync_lock:
                now = time.time()
                key = get_cache_key(*args, **kwargs)
                if key in cache:
                    result, timestamp = cache[key]
                    if now - timestamp < expiration_seconds:
                        return result
                result = func(*args, **kwargs)
                cache[key] = (result, now)
                return result

        return async_wrapped if asyncio.iscoroutinefunction(func) else sync_wrapped

    return decorator