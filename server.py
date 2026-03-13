import os
from aiohttp import web
from aiohttp_apispec import (
    setup_aiohttp_apispec,
    validation_middleware
)
import aiohttp_cors
from config import logger
import asyncio
from api import (categories, audit, calculate, selection, icons)

from database.functions import init_db


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
    asyncio.run(init_db())
    
    app = web.Application()

    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods=["GET", "POST", "OPTIONS", "PATCH", "DELETE"]
        )
    })
    
    setup_aiohttp_apispec(
        app,
        title="Cashback API",
        version="v1",
        url="/swagger.json",
        swagger_path="/",
        security_definitions={
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "Bearer token authorization"
            }
        }
    )

    prefix = "/"
    routes = [
        web.get(prefix + 'api/v1/admin/categories', categories.list_categories),
        web.post(prefix + 'api/v1/admin/categories', categories.create_category),
        web.get(prefix + 'api/v1/admin/categories/{category_id}', categories.get_category),
        web.patch(prefix + 'api/v1/admin/categories/{category_id}', categories.update_category),
        web.post(prefix + 'api/v1/admin/icons/{icon_key}', icons.upload_icon),
        web.get(prefix + 'api/v1/admin/audit', audit.list_audit),

        web.post(prefix + 'api/v1/client/calculate', calculate.calculate),
        web.get(prefix + 'api/v1/client/selection/{selection_id}', selection.get_selection),
        web.post(prefix + 'api/v1/client/selection/{selection_id}', selection.confirm_selection),

        web.get('/{path:.*}', handle_get_file)
    ]
    
    for route in routes:
        cors.add(app.router.add_route(route.method, route.path, route.handler))

    app.middlewares.append(validation_middleware)
    
    logger.info("Запуск сервера. . .")
    web.run_app(
        app,
        host=os.environ.get('INSTANCE_HOST', '0.0.0.0'),
        port=int(os.environ.get('PORT', 8080))
    )
