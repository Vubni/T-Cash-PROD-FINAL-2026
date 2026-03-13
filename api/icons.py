import os
from aiohttp import web
from aiohttp_apispec import docs

from config import logger
from api import validate
from docs import schems as sh


ALLOWED_EXTENSIONS = {".svg", ".png", ".jpg", ".jpeg", ".webp"}


def _get_extension(filename: str) -> str:
    _, ext = os.path.splitext(filename or "")
    return ext.lower()


def _build_icons_dir() -> str:
    base_dir = os.path.join(os.getcwd(), "static", "icons")
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


@docs(
    tags=["Cashback Admin"],
    summary="Загрузить иконку категории",
    description=(
        "Загружает файл иконки и сохраняет его на сервере в каталоге static/icons. "
        "Имя файла формируется из icon_key и расширения исходного файла. "
        "Возвращает URL, по которому фронтенд может забирать иконку."
    ),
    responses={
        201: {
            "description": "Иконка успешно загружена",
            "schema": sh.SelectionConfirmResponseSchema,  # будет переопределено ниже на корректную схему
        },
        **sh.RESPONSES_HTTP_ERROR,
    },
    parameters=[
        {
            "in": "path",
            "name": "icon_key",
            "schema": {"type": "string"},
            "required": True,
            "description": "Ключ иконки, который используется в сущностях (например restaurants)",
        },
        {
            "in": "formData",
            "name": "file",
            "type": "file",
            "required": True,
            "description": "Файл иконки (svg, png, jpg, jpeg, webp)",
        },
    ],
)
async def upload_icon(request: web.Request) -> web.Response:
    try:
        icon_key = request.match_info.get("icon_key")
        if not icon_key:
            return validate.format_400_error(request, "icon_key is required")

        data = await request.post()
        file_field = data.get("file")

        if file_field is None:
            return validate.format_400_error(request, "File field 'file' is required")

        filename = getattr(file_field, "filename", None)
        ext = _get_extension(filename)
        if ext not in ALLOWED_EXTENSIONS:
            return validate.format_400_error(
                request,
                "Unsupported file type",
                details={"allowed": sorted(ALLOWED_EXTENSIONS)},
            )

        icons_dir = _build_icons_dir()
        target_filename = f"{icon_key}{ext}"
        target_path = os.path.join(icons_dir, target_filename)

        file_bytes = file_field.file.read()
        with open(target_path, "wb") as f:
            f.write(file_bytes)

        icon_url = f"/icons/{target_filename}"
        body = {
            "icon_key": icon_key,
            "icon_url": icon_url,
            "filename": target_filename,
        }
        return web.json_response(body, status=201)
    except Exception as e:
        logger.error("upload_icon error: %s", e)
        return validate.format_500_error(request)

