import json
import os
import secrets
import string
import asyncio
import re
import threading
import time
from aiohttp import web
from functools import wraps
import jwt
import uuid
from decimal import Decimal
from config import (
    SECRET,
    logger,
    CATEGORIES_CONFIG_PATH,
    ALL_CATEGORIES_DEFAULT,
    DEFAULT_MAX_SELECTION_COUNT,
)
from datetime import UTC, date, datetime
from datetime import time as time_type

ADMIN_SCOPE = "admin"
USER_SCOPE = "user"


def serialize_json(obj):
    if hasattr(obj, "model_dump"):
        obj = obj.model_dump()
    elif hasattr(obj, "dict"):
        obj = obj.dict()

    if isinstance(obj, datetime):
        if obj.tzinfo is None:
            return obj.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            return obj.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    elif isinstance(obj, date) and not isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%dT00:00:00Z")
    elif isinstance(obj, time_type):
        return datetime.combine(date(1970, 1, 1), obj).strftime("%Y-%m-%dT%H:%M:%SZ")
    elif isinstance(obj, dict):
        return {key: serialize_json(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        result = [serialize_json(item) for item in obj]
        return tuple(result) if isinstance(obj, tuple) else result
    elif isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj


async def check_authorization(request: web.Request):
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
        logger.error("check_authorization error: ", e)
        return None


async def check_admin_authorization(request: web.Request) -> dict | None:
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


def generate_unique_code(length: int = 32):
    """Генерация рандомного кода из символов латиницы, цифры и _

    Args:
        length (int, optional): Длина кода. Defaults to 32.

    Returns:
        str: Сгенерированный код
    """
    characters = string.ascii_letters + string.digits + "_"
    return "".join(secrets.choice(characters) for _ in range(length))


def is_domain_valid(domain):
    """Проверяет, соответствует ли домен стандартам (RFC 1035)."""
    segments = domain.split(".")
    for segment in segments:
        if not segment:
            return False
        if segment[0] == "-" or segment[-1] == "-":
            return False
        if not re.match(r"^[a-zA-Z0-9-]+$", segment):
            return False
    return True


def is_valid_email(email: str) -> bool:
    """Проверка реальности почты"""
    regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(regex, email):
        return False

    local_part, domain_part = email.split("@")

    if len(local_part) > 64:
        return False
    if local_part.startswith(".") or local_part.endswith("."):
        return False
    if ".." in local_part:
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


ML_CATEGORY_NAMES = [
    "Автоуслуги",
    "Аптеки",
    "Ж/д билеты",
    "Животные",
    "Заправки",
    "Искусство",
    "Каршеринг",
    "Книги и канцтовары",
    "Красота",
    "Музыка",
    "Образование",
    "Одежда и обувь",
    "Подарки и творчество",
    "Развлечения",
    "Ремонт и мебель",
    "Рестораны",
    "Спорттовары",
    "Супермаркеты",
    "Такси",
    "Фастфуд",
    "Цветы",
]


def load_categories_config() -> dict:
    """Читает конфиг выбора категорий из файла (all_categories, max_selection_count)."""
    try:
        with open(CATEGORIES_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
        if not isinstance(data, dict):
            return {}
        return data
    except Exception:
        return {}


def save_categories_config(cfg: dict) -> None:
    """Сохраняет конфиг выбора категорий в файл."""
    os.makedirs(os.path.dirname(CATEGORIES_CONFIG_PATH), exist_ok=True)
    with open(CATEGORIES_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get_all_categories() -> int:
    """Текущее значение all_categories (0 или 1)."""
    data = load_categories_config()
    try:
        return int(data.get("all_categories", ALL_CATEGORIES_DEFAULT) or 0)
    except (TypeError, ValueError):
        return ALL_CATEGORIES_DEFAULT


def get_max_selection_count() -> int:
    """Текущее значение max_selection_count (сколько категорий выбирает пользователь)."""
    data = load_categories_config()
    try:
        value = int(data.get("max_selection_count", DEFAULT_MAX_SELECTION_COUNT))
        if value < 1:
            return DEFAULT_MAX_SELECTION_COUNT
        return value
    except (TypeError, ValueError):
        return DEFAULT_MAX_SELECTION_COUNT
