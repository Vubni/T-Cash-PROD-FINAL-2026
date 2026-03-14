import os
from aiohttp import web
from aiohttp_apispec import (
    setup_aiohttp_apispec,
    validation_middleware
)
import aiohttp_cors
from config import logger
import asyncio
from api import (categories, audit, calculate, selection, icons, rules, offers, progress, users, admin_auth)

from database.functions import init_db
from functions import admin_users as admin_users_fns


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


if __name__ == "__main__":
    async def startup():
        await init_db()
        main_login = os.environ.get("MAIN_ADMIN_LOGIN", "admin")
        main_password = os.environ.get("MAIN_ADMIN_PASSWORD", "admin")
        await admin_users_fns.ensure_main_admin(main_login, main_password)
        logger.info("Главный админ создан.")

    asyncio.run(startup())

    app = web.Application()

    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods=["GET", "POST", "OPTIONS", "PATCH", "DELETE"]
        )
    })

    prefix = "/"
    api_routes = [
        web.get(prefix + 'api/v1/admin/categories', categories.list_categories),
        web.post(prefix + 'api/v1/admin/categories', categories.create_category),
        web.get(prefix + 'api/v1/admin/categories/{category_id}', categories.get_category),
        web.patch(prefix + 'api/v1/admin/categories/{category_id}', categories.update_category),
        web.post(prefix + 'api/v1/admin/icons/{icon_key}', icons.upload_icon),
        web.get(prefix + 'api/v1/admin/audit', audit.list_audit),

        web.get(prefix + 'api/v1/users/{user_id}/exists', users.user_exists),

        web.post(prefix + 'api/v1/admin/auth/register', admin_auth.register_admin),
        web.post(prefix + 'api/v1/admin/auth/login', admin_auth.login_admin),
        web.post(prefix + 'api/v1/admin/auth/approve', admin_auth.approve_admin),

        web.post(prefix + 'api/v1/client/calculate', calculate.calculate),
        web.post(prefix + 'api/v1/client/selection', selection.confirm_selection),
    ]
    for route in api_routes:
        cors.add(app.router.add_route(route.method, route.path, route.handler))

    apispec_instance = setup_aiohttp_apispec(
        app,
        title="Cashback API",
        version="v1",
        url="/swagger.json",
        swagger_path="/",
        in_place=True,
    )

    cors.add(app.router.add_route("GET", "/{path:.*}", handle_get_file))

    app.middlewares.append(validation_middleware)
    
    logger.info("Запуск сервера. . .")
    web.run_app(
        app,
        host=os.environ.get('INSTANCE_HOST', '0.0.0.0'),
        port=int(os.environ.get('PORT', 8080))
    )
