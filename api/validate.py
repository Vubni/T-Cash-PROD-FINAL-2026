from typing import Callable, Optional, TypeVar, Awaitable, Any
from functools import wraps
from pydantic import BaseModel, ValidationError
import json
from aiohttp import web
from pydantic import field_validator
import core
from datetime import UTC, datetime
import uuid

T = TypeVar("T", bound=BaseModel)

SECURITY_ADMIN_BEARER = [{"adminBearer": []}]
SECURITY_USER_BEARER = [{"userBearer": []}]


def generate_trace_id() -> str:
    return str(uuid.uuid4())


def get_timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def get_nested_value(data: dict[str, Any], path: tuple) -> Any:
    if not path:
        return None

    current = data
    for key in path:
        if isinstance(current, dict):
            current = current.get(key)
            if current is None:
                return None
        else:
            return None

    return current


def format_error_response(
    code: str,
    message: str,
    path: str,
    status: int,
    details: dict[str, Any] | None = None,
    field_errors: list | None = None,
) -> dict[str, Any]:
    response = {
        "code": code,
        "message": message,
        "traceId": generate_trace_id(),
        "timestamp": get_timestamp(),
        "path": path,
    }
    if details:
        response["details"] = details
    if field_errors:
        response["fieldErrors"] = field_errors
    return response


def format_http_error(
    request: web.Request,
    status: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    field_errors: list | None = None,
) -> web.Response:
    body = format_error_response(
        code=code,
        message=message,
        path=str(request.path_qs),
        status=status,
        details=details,
        field_errors=field_errors,
    )
    return web.json_response(body, status=status)


def format_400_error(
    request: web.Request,
    message: str = "Некорректный запрос",
    details: dict[str, Any] | None = None,
) -> web.Response:
    return format_http_error(request, 400, "BAD_REQUEST", message, details=details)


def format_401_error(request: web.Request, message: str = "Токен отсутствует, невалиден или истёк") -> web.Response:
    return format_http_error(request, 401, "UNAUTHORIZED", message)


def format_403_error(request: web.Request, message: str = "Недостаточно прав для выполнения операции") -> web.Response:
    return format_http_error(request, 403, "FORBIDDEN", message)


def format_404_error(
    request: web.Request,
    message: str = "Ресурс не найден",
    details: dict[str, Any] | None = None,
) -> web.Response:
    return format_http_error(request, 404, "NOT_FOUND", message, details=details)


def format_409_error(
    request: web.Request, value, message: str = "Токен отсутствует или невалиден", field="email"
) -> web.Response:
    return format_http_error(
        request,
        409,
        f"{field.upper()}_ALREADY_EXISTS",
        message,
        details={"field": field, "value": value},
    )


def format_409_conflict(request: web.Request, message: str, code: str = "CONFLICT") -> web.Response:
    return format_http_error(request, 409, code, message)


def format_422_error(
    request: web.Request,
    code: str = "VALIDATION_FAILED",
    message: str = "Некоторые поля не прошли валидацию",
    field_errors: list | None = None,
) -> web.Response:
    return format_http_error(request, 422, code, message, field_errors=field_errors)


def format_423_error(request: web.Request, message: str = "Пользователь деактивирован") -> web.Response:
    return format_http_error(request, 423, "USER_INACTIVE", message)


def format_500_error(
    request: web.Request,
    message: str = "Внутренняя ошибка сервера",
    details: dict[str, Any] | None = None,
) -> web.Response:
    return format_http_error(request, 500, "INTERNAL_ERROR", message, details=details)


def validate_uuid(value: str, field_name: str = "id") -> str:
    """Проверяет, что строка является валидным UUID. Возвращает нормализованную строку."""
    if not value or not str(value).strip():
        raise ValueError(f"{field_name} cannot be empty")
    s = str(value).strip().lower()
    try:
        uuid.UUID(s)
    except (ValueError, TypeError, AttributeError):
        raise ValueError(f"{field_name} must be a valid UUID")
    return s


BIGINT_MIN = -(2**63)
BIGINT_MAX = 2**63 - 1


def validate_user_id(value: int | str, field_name: str = "user_id") -> int:
    """Проверяет, что значение целое число в диапазоне BIGINT. Возвращает int."""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"{field_name} cannot be empty")
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    try:
        n = int(value)
    except (ValueError, TypeError):
        raise ValueError(f"{field_name} must be a valid integer")
    if n < BIGINT_MIN or n > BIGINT_MAX:
        raise ValueError(f"{field_name} must be within BIGINT range ({BIGINT_MIN}..{BIGINT_MAX})")
    return n


class EmailError(Exception):
    def __init__(self, message="Ошибка проверки email", errors=None):
        self.message = message
        self.errors = errors or []
        super().__init__(self.message)


async def _check_ordinary_admin(request: web.Request) -> web.Response | None:
    """Проверка: авторизованный обычный (не супер) админ. Возвращает None при успехе, иначе response с ошибкой."""
    payload = await core.check_admin_authorization(request)
    if not payload:
        return format_401_error(request, "Токен админа отсутствует или невалиден")
    from functions import admin_users

    admin = await admin_users.get_admin_by_id(payload.get("admin_id"))
    if not admin or not admin.get("approved"):
        return format_401_error(request, "Админ не найден или не одобрен")
    request["admin_payload"] = payload
    return None


async def _check_super_admin(request: web.Request) -> web.Response | None:
    """Проверка: авторизованный супер-админ. Возвращает None при успехе, иначе response с ошибкой."""
    payload = await core.check_admin_authorization(request)
    if not payload:
        return format_401_error(request, "Токен админа отсутствует или невалиден")
    from functions import admin_users

    admin = await admin_users.get_admin_by_id(payload.get("admin_id"))
    if not admin or not admin.get("main_admin"):
        return format_403_error(request, "Только супер-админ может одобрять новых админов")
    request["admin_payload"] = payload
    return None


def require_ordinary_admin(
    handler: Callable[[web.Request], Awaitable[web.Response]],
) -> Callable[[web.Request], Awaitable[web.Response]]:
    """Декоратор для эндпоинтов, доступных только обычному (одобренному, не супер) админу."""

    @wraps(handler)
    async def wrapper(request: web.Request) -> web.Response:
        err = await _check_ordinary_admin(request)
        if err is not None:
            return err
        return await handler(request)

    return wrapper


def validate(
    model: type[T],
    require_auth: bool = False,
    require_admin: bool = False,
    require_super_admin: bool = False,
) -> Callable:
    def decorator(handler: Callable[[web.Request, Any], Awaitable[web.Response]]):
        @wraps(handler)
        async def wrapper(request: web.Request) -> web.Response:
            if require_super_admin:
                err = await _check_super_admin(request)
                if err is not None:
                    return err
            elif require_admin:
                err = await _check_ordinary_admin(request)
                if err is not None:
                    return err

            if require_auth:
                payload = await core.check_authorization(request)
                if not isinstance(payload, dict):
                    if payload is not None and isinstance(payload, web.Response):
                        return payload
                    return format_401_error(request)
                request["user_payload"] = payload

            if request.method in ("POST", "PUT", "PATCH"):
                content_length = request.headers.get("Content-Length")
                if not content_length or content_length == "0":
                    data = {}
                else:
                    try:
                        size = int(content_length)
                        if size > 10 * 1024 * 1024:
                            return format_400_error(
                                request,
                                "Слишком большой payload",
                                details={"hint": "Максимальный размер запроса: 10MB"},
                            )
                    except ValueError:
                        pass

                    content_type = request.headers.get("Content-Type", "")
                    if not content_type.startswith("application/json"):
                        return format_400_error(
                            request,
                            "Неподдерживаемый Content-Type",
                            details={"hint": "Используйте Content-Type: application/json"},
                        )

                    try:
                        data = await request.json()
                    except json.JSONDecodeError:
                        return format_400_error(
                            request,
                            "Невалидный JSON",
                            details={"hint": "Проверьте запятые/кавычки"},
                        )
                    except Exception:
                        return format_400_error(
                            request,
                            "Ошибка обработки запроса",
                            details={"hint": "Проверьте формат и размер запроса"},
                        )
            elif request.method == "GET":
                data = dict(request.query)
            else:
                data = {}

            all_data = dict(request.match_info)
            all_data.update(dict(request.query))
            all_data.update(data)

            MAX_REQUEST_FIELDS = 128
            if len(all_data) > MAX_REQUEST_FIELDS:
                return format_400_error(
                    request,
                    "Слишком много полей в запросе",
                    details={"max_fields": MAX_REQUEST_FIELDS},
                )
            for key, value in all_data.items():
                if key == "user_id":
                    if isinstance(value, str) and value.strip() and value.lstrip("-").isdigit():
                        try:
                            all_data[key] = int(value)
                        except (ValueError, TypeError):
                            pass
                    continue
                if isinstance(value, str):
                    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
                        try:
                            all_data[key] = int(value)
                        except (ValueError, TypeError):
                            pass
                    elif "." in value:
                        try:
                            all_data[key] = float(value)
                        except (ValueError, TypeError):
                            pass
                    elif value.lower() == "true":
                        all_data[key] = True
                    elif value.lower() == "false":
                        all_data[key] = False

            try:
                parsed = model(**all_data)
            except ValidationError as e:
                field_errors = [
                    {
                        "field": ".".join(str(loc) for loc in error["loc"]) if error["loc"] else "general",
                        "issue": error["msg"],
                        "rejectedValue": get_nested_value(all_data, tuple(error["loc"])) if error["loc"] else None,
                    }
                    for error in e.errors()
                ]
                return format_422_error(
                    request,
                    code="VALIDATION_FAILED",
                    message="Некоторые поля не прошли валидацию",
                    field_errors=field_errors,
                )
            except EmailError as e:
                field_errors = [{"field": "email", "issue": e.message, "rejectedValue": all_data.get("email")}]
                return format_422_error(
                    request,
                    code="VALIDATION_FAILED",
                    message="Некоторые поля не прошли валидацию",
                    field_errors=field_errors,
                )

            return await handler(request, parsed)

        return wrapper

    return decorator


class Auth(BaseModel):
    model_config = {"extra": "forbid"}

    identifier: str
    password: str

    @field_validator("identifier")
    @classmethod
    def check_identifier(cls, v):
        if not v or not str(v).strip():
            raise ValueError("identifier cannot be empty")
        if len(v) > 256:
            raise ValueError("identifier cannot exceed 256 characters")
        return v.strip()

    @field_validator("password")
    @classmethod
    def check_password(cls, v):
        if not v or not str(v).strip():
            raise ValueError("password cannot be empty")
        return v


class Auth_telegram(BaseModel):
    model_config = {"extra": "forbid"}
    token: str


class Login_patch(BaseModel):
    model_config = {"extra": "forbid"}
    login: str

    @field_validator("login")
    @classmethod
    def check_login(cls, v):
        if not v or not str(v).strip():
            raise ValueError("login cannot be empty")
        if len(v) > 20:
            raise ValueError("login cannot exceed 20 characters")
        return v.strip()


class Email_patch(BaseModel):
    model_config = {"extra": "forbid"}
    email: str

    @field_validator("email")
    @classmethod
    def check_email(cls, v):
        if not v or not str(v).strip():
            raise ValueError("email cannot be empty")
        if len(v) > 256:
            raise ValueError("email cannot exceed 256 characters")
        if not core.is_valid_email(v):
            raise EmailError("Email does not comply with email standards or dns mail servers are not found")
        return v


class Password_patch(BaseModel):
    model_config = {"extra": "forbid"}
    current_password: str
    new_password: str

    @field_validator("current_password", "new_password")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("password cannot be empty")
        return v


class Schedule_get(BaseModel):
    model_config = {"extra": "forbid"}
    date: str


class Clubs_list(BaseModel):
    model_config = {"extra": "forbid"}
    type: str = "my"
    offset: int = 0
    limit: int = 100


class Club_info(BaseModel):
    model_config = {"extra": "forbid"}
    club_id: int


class Club_new(BaseModel):
    model_config = {"extra": "forbid"}
    title: str
    description: str
    administration: int
    max_members_counts: Optional[int] = 0
    class_limit_min: Optional[int] = 1
    class_limit_max: Optional[int] = 11
    telegram_url: Optional[str] = None

    @field_validator("class_limit_max")
    @classmethod
    def validate_class_limit_max(cls, v):
        if v is None:
            return v
        if 1 <= v <= 11:
            return v
        raise ValueError("class_limit_max in 1-11")

    @field_validator("class_limit_min")
    @classmethod
    def validate_class_limit_min(cls, v):
        if v is None:
            return v
        if 1 <= v <= 11:
            return v
        raise ValueError("class_limit_min in 1-11")

    @field_validator("max_members_counts")
    @classmethod
    def validate_max_members_counts(cls, v):
        if v is None:
            return v
        if 0 < v < 4:
            return v
        raise ValueError("max_members_counts is 4+ or 0")

    @field_validator("telegram_url")
    @classmethod
    def validate_telegram_url(cls, v):
        if v is None:
            return v
        valid_prefixes = ("https://t.me/", "http://t.me/", "https://telegram.me/", "http://telegram.me/")

        if not any(v.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError(
                "Telegram URL must start with: https://t.me/, http://t.me/, https://telegram.me/ or http://telegram.me/"
            )

        if len(v) < 15:
            raise ValueError("Telegram URL is too short")
        return v


class Check_title(BaseModel):
    model_config = {"extra": "forbid"}
    title: str

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title cannot be empty")
        return v.strip()


class Club_join(BaseModel):
    model_config = {"extra": "forbid"}
    club_id: int


class Club_delete(BaseModel):
    model_config = {"extra": "forbid"}
    club_id: int


class Achievements_local(BaseModel):
    model_config = {"extra": "forbid"}
    club_id: int


class Club_edit(BaseModel):
    model_config = {"extra": "forbid"}
    club_id: int
    title: Optional[str] = None
    description: Optional[str] = None
    max_members_counts: Optional[int] = None
    class_limit_min: Optional[int] = None
    class_limit_max: Optional[int] = None
    telegram_url: Optional[str] = None

    @field_validator("class_limit_max")
    @classmethod
    def validate_class_limit_max(cls, v):
        if v is None:
            return v
        if 1 <= v <= 11:
            return v
        raise ValueError("class_limit_max in 1-11")

    @field_validator("class_limit_min")
    @classmethod
    def validate_class_limit_min(cls, v):
        if v is None:
            return v
        if 1 <= v <= 11:
            return v
        raise ValueError("class_limit_min in 1-11")

    @field_validator("max_members_counts")
    @classmethod
    def validate_max_members_counts(cls, v):
        if v is None:
            return v
        if 0 < v < 4:
            return v
        raise ValueError("max_members_counts is 4+ or 0")

    @field_validator("telegram_url")
    @classmethod
    def validate_telegram_url(cls, v):
        if v is None:
            return v
        valid_prefixes = (
            "https://t.me/",
            "http://t.me/",
            "https://telegram.me/",
            "http://telegram.me/",
        )
        if not any(v.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError(
                "Telegram URL must start with: https://t.me/, http://t.me/, https://telegram.me/ or http://telegram.me/"
            )
        if len(v) < 15:
            raise ValueError("Telegram URL is too short")
        return v


class Forgot_password(BaseModel):
    model_config = {"extra": "forbid"}
    identifier: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("new_password cannot be empty")
        return v


class Forgot_password_confirm(BaseModel):
    model_config = {"extra": "forbid"}
    confirm: int


class Email_verify_confirm(BaseModel):
    model_config = {"extra": "forbid"}
    token: str

    @field_validator("token")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("token cannot be empty")
        return v
