import os
from aiohttp import web
from aiohttp_apispec import (
    setup_aiohttp_apispec,
    validation_middleware
)
import aiohttp_cors
from config import logger
import asyncio
from api import (categories, audit, selection, rules, users, admin_auth, calculate)

from database.functions import (
    init_db,
    ensure_users_from_csv,
    ensure_selections_user_id_column,
    ensure_categories_from_csv,
)
from functions import admin_users as admin_users_fns


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
    static_dir = "static"
    path = request.match_info['path']
    
    safe_path = os.path.normpath(path).lstrip('/')
    full_path = os.path.join(static_dir, safe_path)
    abs_static = os.path.abspath(static_dir)
    abs_target = os.path.abspath(full_path)
    
    if not abs_target.startswith(abs_static):
        return web.HTTPNotFound()
    
    if os.path.isfile(abs_target):
        return web.FileResponse(abs_target)
    
    last_part = safe_path.split('/')[-1] if safe_path else ""
    if '.' in last_part:
        return web.HTTPNotFound()
    
    index_path = os.path.join(static_dir, "index.html")
    if os.path.isfile(index_path):
        return web.FileResponse(index_path)
    
    return web.HTTPNotFound()


def create_app() -> web.Application:
    """Создаёт и возвращает aiohttp Application (для запуска и для тестов)."""
    app = web.Application()

    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods=["GET", "POST", "OPTIONS", "PATCH", "DELETE"]
        )
    })

    prefix = "/api/v1"
    api_routes = [
        web.get(prefix + '/admin/categories', categories.list_categories),
        web.post(prefix + '/admin/categories', categories.create_category),
        web.get(prefix + '/admin/categories/{category_id}', categories.get_category),
        web.post(prefix + '/admin/categories/{category_id}/rule', categories.create_category_rule),
        web.patch(prefix + '/admin/categories/{category_id}', categories.update_category),
        web.get(prefix + '/admin/audit', audit.list_audit),
        web.post(prefix + '/admin/categories/settings', selection.update_selection_settings),

        web.get(prefix + '/users/{user_id}/exists', users.user_exists),

        web.post(prefix + '/admin/auth/register', admin_auth.register_admin),
        web.post(prefix + '/admin/auth/login', admin_auth.login_admin),
        web.get(prefix + '/admin/auth/pending', admin_auth.list_pending),
        web.post(prefix + '/admin/auth/approve', admin_auth.approve_admin),
        web.post(prefix + '/admin/auth/decline', admin_auth.decline_admin),

        web.post(prefix + '/offers/run', calculate.calculate),
        web.post(prefix + '/client/selection', selection.confirm_selection),
    ]
    for route in api_routes:
        cors.add(app.router.add_route(route.method, route.path, route.handler))

    setup_aiohttp_apispec(
        app,
        title="Cashback API",
        version="v1",
        url="/swagger.json",
        swagger_path="/",
        in_place=True,
    )
    admin_bearer_scheme = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT токен админа (получить через POST /api/v1/admin/auth/login). В поле ниже введите токен — можно с префиксом «Bearer » или без него.",
    }
    swagger_dict = app["swagger_dict"]
    if "components" in swagger_dict:
        swagger_dict.setdefault("components", {}).setdefault("securitySchemes", {})["adminBearer"] = admin_bearer_scheme
    else:
        swagger_dict.setdefault("securityDefinitions", {})["adminBearer"] = {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": admin_bearer_scheme.get("description", ""),
        }

    cors.add(app.router.add_route("GET", "/{path:.*}", handle_get_file))

    app.middlewares.append(request_logging_middleware)
    app.middlewares.append(validation_middleware)

    return app


if __name__ == "__main__":
    async def startup():
        await init_db()
        main_login = os.environ.get("MAIN_ADMIN_LOGIN", "admin")
        main_password = os.environ.get("MAIN_ADMIN_PASSWORD", "admin")
        await admin_users_fns.ensure_main_admin(main_login, main_password)
        logger.info("Главный админ создан.")
        await ensure_users_from_csv()
        await ensure_categories_from_csv()
        await ensure_selections_user_id_column()

    asyncio.run(startup())

    app = create_app()
    logger.info("Запуск сервера. . .")
    web.run_app(
        app,
        host=os.environ.get('INSTANCE_HOST', '0.0.0.0'),
        port=int(os.environ.get('PORT', 8080))
    )
