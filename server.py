import asyncio
import os

import aiohttp_cors
from aiohttp import web
from aiohttp_apispec import docs, setup_aiohttp_apispec, validation_middleware

from api import audit, categories, selection, users, admin_auth, calculate
from config import logger
from docs import schemas as sh
from startup import run_startup


API_PREFIX = "/api/v1"
STATIC_DIR = "static"
SWAGGER_JSON_URL = "/docs/swagger.json"
SWAGGER_UI_PATH = "/docs"
SWAGGER_TITLE = "Cashback API"
SWAGGER_VERSION = "v1"


@docs(
    tags=["Health"],
    summary="Health",
    description="Проверка, что сервис жив. Всегда 200 при рабочем приложении.",
    responses={200: {"description": "Сервис запущен", "schema": sh.HealthLivenessResponseSchema}},
)
async def health(_request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"}, status=200)


@web.middleware
async def request_logging_middleware(request: web.Request, handler):
    logger.info(
        "HTTP %s %s from %s",
        request.method,
        request.path_qs,
        request.remote,
    )
    try:
        response = await handler(request)
    except web.HTTPException as ex:
        logger.info(
            "HTTP %s %s -> %s",
            request.method,
            request.path_qs,
            ex.status,
        )
        raise

    logger.info(
        "HTTP %s %s -> %s",
        request.method,
        request.path_qs,
        response.status,
    )
    return response


async def handle_get_file(request: web.Request) -> web.Response:
    path = request.match_info["path"]

    safe_path = os.path.normpath(path).lstrip("/")
    full_path = os.path.join(STATIC_DIR, safe_path)
    abs_static = os.path.abspath(STATIC_DIR)
    abs_target = os.path.abspath(full_path)

    if not abs_target.startswith(abs_static):
        return web.HTTPNotFound()

    if os.path.isfile(abs_target):
        return web.FileResponse(abs_target)

    last_part = safe_path.split("/")[-1] if safe_path else ""
    if "." in last_part:
        return web.HTTPNotFound()

    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_path):
        return web.FileResponse(index_path)

    return web.HTTPNotFound()


def setup_cors(app: web.Application) -> aiohttp_cors.CorsConfig:
    return aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods=["GET", "POST", "OPTIONS", "PATCH", "DELETE"],
            )
        },
    )


def register_routes(app: web.Application, cors: aiohttp_cors.CorsConfig) -> None:
    prefix = API_PREFIX

    api_routes = [
        web.get("/health", health),
        web.get(prefix + "/admin/categories", categories.list_categories),
        web.post(prefix + "/admin/categories", categories.create_category),
        web.get(prefix + "/admin/categories/{category_id}", categories.get_category),
        web.post(prefix + "/admin/categories/{category_id}/icon", categories.upload_category_icon),
        web.get(prefix + "/admin/categories/{category_id}/rule", categories.get_category_rule),
        web.post(prefix + "/admin/categories/{category_id}/rule", categories.create_category_rule),
        web.patch(prefix + "/admin/categories/{category_id}/rule", categories.update_category_rule),
        web.delete(prefix + "/admin/categories/{category_id}/rule", categories.delete_category_rule),
        web.patch(prefix + "/admin/categories/{category_id}", categories.update_category),
        web.post(prefix + "/admin/categories/{category_id}/run", categories.run_category),
        web.post(prefix + "/admin/categories/{category_id}/pause", categories.pause_category),
        web.delete(prefix + "/admin/categories/{category_id}/archive", categories.archive_category),
        web.get(prefix + "/admin/categories/{category_id}/audit", audit.list_audit),
        
        web.get(prefix + "/admin/categories/settings", selection.get_selection_settings),
        web.post(prefix + "/admin/categories/settings", selection.update_selection_settings),

        web.get(prefix + "/users/{user_id}/auth", users.user_auth),
        web.post(prefix + "/admin/auth/register", admin_auth.register_admin),
        web.post(prefix + "/admin/auth/login", admin_auth.login_admin),
        web.get(prefix + "/admin/auth/pending", admin_auth.list_pending),
        web.post(prefix + "/admin/auth/approve", admin_auth.approve_admin),
        web.post(prefix + "/admin/auth/decline", admin_auth.decline_admin),

        web.post(prefix + "/offers/run", calculate.calculate),

        web.post(prefix + "/client/selection", selection.confirm_selection),
    ]

    for route in api_routes:
        cors.add(app.router.add_route(route.method, route.path, route.handler))

    cors.add(app.router.add_route("GET", "/{path:.*}", handle_get_file))


def configure_swagger(app: web.Application) -> None:
    setup_aiohttp_apispec(
        app,
        title=SWAGGER_TITLE,
        version=SWAGGER_VERSION,
        url=SWAGGER_JSON_URL,
        swagger_path=SWAGGER_UI_PATH,
        in_place=True,
    )

    admin_bearer_scheme = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": (
            "JWT токен админа (получить через POST /api/v1/admin/auth/login). "
            "В поле ниже введите токен — можно с префиксом «Bearer » или без него."
        ),
    }
    user_bearer_scheme = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": (
            "JWT токен пользователя (получить через GET /api/v1/users/{user_id}/auth). "
            "В поле ниже введите токен — можно с префиксом «Bearer » или без него."
        ),
    }
    swagger_dict = app["swagger_dict"]
    if "info" not in swagger_dict:
        swagger_dict["info"] = {}
    swagger_dict["info"].setdefault(
        "description",
        (
            "API кэшбэка: админка категорий и правил отбора, расчёт офферов для клиента, "
            "подтверждение выбора категорий. Авторизация: JWT админа (adminBearer) или JWT "
            "пользователя (userBearer). Спецификация: /swagger.json."
        ),
    )
    if "components" in swagger_dict:
        components = swagger_dict.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})
        security_schemes["adminBearer"] = admin_bearer_scheme
        security_schemes["userBearer"] = user_bearer_scheme
    else:
        security_definitions = swagger_dict.setdefault("securityDefinitions", {})
        security_definitions["adminBearer"] = {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": admin_bearer_scheme.get("description", ""),
        }
        security_definitions["userBearer"] = {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": user_bearer_scheme.get("description", ""),
        }


def setup_middlewares(app: web.Application) -> None:
    app.middlewares.append(request_logging_middleware)
    app.middlewares.append(validation_middleware)


def create_app() -> web.Application:
    app = web.Application()
    cors = setup_cors(app)
    register_routes(app, cors)
    configure_swagger(app)
    setup_middlewares(app)
    return app


def main() -> None:
    asyncio.run(run_startup())

    app = create_app()
    logger.info("Запуск сервера. . .")
    web.run_app(app, host=os.environ.get("INSTANCE_HOST", "0.0.0.0"), port=int(os.environ.get("PORT", 8080)))


if __name__ == "__main__":
    main()
