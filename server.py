import os
from aiohttp import web
from aiohttp_apispec import (
    setup_aiohttp_apispec,
    validation_middleware
)
import aiohttp_cors
from config import logger
import asyncio
from api import (auth, profile)

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
        title="API doc",
        version="v1",
        url="/swagger.json",
        swagger_path="/doc",
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
        # web.post(prefix + 'reg', auth.register),
        web.post(prefix + 'auth', auth.auth),
        web.get(prefix + 'auth/telegram/url', auth.telegram_url),
        web.post(prefix + 'auth/telegram', auth.telegram),
        web.post(prefix + 'email', auth.email_verify),
        web.get(prefix + 'verify-email', auth.email_verify_confirm),
        web.post(prefix + 'auth/forgot_password', auth.forgot_password),
        web.get(prefix + 'auth/forgot_password/confirm', auth.forgot_password_confirm),
        
        web.get(prefix + 'settings/info', profile.info),
        web.post(prefix + 'settings/login/set', profile.set_login),
        web.post(prefix + 'settings/password/change', profile.set_password),
        web.post(prefix + 'settings/email/set', profile.set_email),
        web.get(prefix + 'settings/telegram/connect', profile.telegram_connect),
        web.delete(prefix + 'settings/telegram/out', profile.telegram_out),

        web.get('/{path:.*}', handle_get_file)
    ]
    
    for route in routes:
        cors.add(app.router.add_route(route.method, route.path, route.handler))

    app.middlewares.append(validation_middleware)
    
    logger.info("Запуск сервера. . .")
    web.run_app(
        app,
        host=os.environ.get('INSTANCE_HOST', 'localhost'),
        port=int(os.environ.get('PORT', 8080))
    )