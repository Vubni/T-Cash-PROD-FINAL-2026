import asyncio
import json
import os
import re
import threading
import time
import uuid
from datetime import UTC, date, datetime, time as time_type
from decimal import Decimal
from functools import wraps
from typing import Any, Callable, TypeVar


from config import (
    ALL_CATEGORIES_DEFAULT,
    CATEGORIES_CONFIG_PATH,
    DEFAULT_MAX_SELECTION_COUNT,
    logger,
)


def serialize_json(obj: Any) -> Any:
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


def validate_uuid(v: str) -> str | None:
    try:
        return str(uuid.UUID(v))
    except (ValueError, TypeError):
        return None


def parse_uuid(value: str) -> str | None:
    try:
        return str(uuid.UUID(value))
    except (ValueError, TypeError):
        return None


def is_domain_valid(domain: str) -> bool:
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


def is_hashable(obj: Any) -> bool:
    try:
        hash(obj)
        return True
    except TypeError:
        return False


T = TypeVar("T")


def cache_with_expiration(expiration_seconds: int) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache: dict[Any, tuple[T, float]] = {}
        async_lock: asyncio.Lock | None = None
        sync_lock = threading.Lock()

        def get_cache_key(*args: Any, **kwargs: Any) -> Any:
            filtered_args = [arg for arg in args if is_hashable(arg)]
            filtered_kwargs = {k: v for k, v in kwargs.items() if is_hashable(v)}
            return (tuple(filtered_args), frozenset(filtered_kwargs.items()))

        @wraps(func)
        async def async_wrapped(*args: Any, **kwargs: Any) -> T:
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
        def sync_wrapped(*args: Any, **kwargs: Any) -> T:
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
    if not os.path.exists(CATEGORIES_CONFIG_PATH):
        return {
            "all_categories": ALL_CATEGORIES_DEFAULT,
            "max_selection_count": DEFAULT_MAX_SELECTION_COUNT,
        }
    try:
        with open(CATEGORIES_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Config must be a JSON object")
            data.setdefault("all_categories", ALL_CATEGORIES_DEFAULT)
            data.setdefault("max_selection_count", DEFAULT_MAX_SELECTION_COUNT)
            return data
    except (OSError, json.JSONDecodeError) as e:
        logger.error("Failed to read categories config %s: %s", CATEGORIES_CONFIG_PATH, e)
        return {
            "all_categories": ALL_CATEGORIES_DEFAULT,
            "max_selection_count": DEFAULT_MAX_SELECTION_COUNT,
        }


def save_categories_config(config: dict) -> None:
    """Сохраняет конфиг выбора категорий в JSON-файл."""
    data = {
        "all_categories": int(config.get("all_categories", ALL_CATEGORIES_DEFAULT)),
        "max_selection_count": int(config.get("max_selection_count", DEFAULT_MAX_SELECTION_COUNT)),
    }
    os.makedirs(os.path.dirname(CATEGORIES_CONFIG_PATH), exist_ok=True)
    tmp_path = f"{CATEGORIES_CONFIG_PATH}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, CATEGORIES_CONFIG_PATH)


def get_all_categories() -> int:
    config = load_categories_config()
    return int(config.get("all_categories", ALL_CATEGORIES_DEFAULT))


def get_max_selection_count() -> int:
    config = load_categories_config()
    return int(config.get("max_selection_count", DEFAULT_MAX_SELECTION_COUNT))
