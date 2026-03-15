from aiohttp import web
from aiohttp.client_exceptions import ClientConnectorError
from aiohttp_apispec import docs
from pydantic import BaseModel

from api import validate
from config import logger
from docs import schemas as sh
from functions import calculate as calc_fns

class Client_calculate(BaseModel):
    model_config = {"extra": "forbid"}


@docs(
    tags=["Offers"],
    summary="Запуск офферов (расчёт категорий для клиента)",
    description=(
        "POST /api/v1/offers/run. Возвращает категории/выборы для текущего авторизованного пользователя. "
        "user_id берётся из JWT-токена пользователя (заголовок Authorization: Bearer <token>, полученный через "
        "GET /api/v1/users/{user_id}/auth). Тело запроса пустое."
    ),
    security=validate.SECURITY_USER_BEARER,
    responses={
        200: {"description": "Список категорий рассчитан", "schema": sh.CalculateResponseSchema},
        404: {"description": "Пользователь не найден", "schema": sh.HttpErrorSchema},
        **sh.RESPONSES_HTTP_ERROR,
    },
)
@validate.validate(Client_calculate, require_auth=True)
async def calculate(request: web.Request, _: Client_calculate) -> web.Response:
    try:
        payload = request.get("user_payload")
        if not isinstance(payload, dict):
            return validate.format_401_error(request, "Токен пользователя отсутствует или невалиден")

        user_id = payload.get("user_id")
        if not user_id or not isinstance(user_id, int):
            return validate.format_401_error(request, "Токен пользователя отсутствует или не содержит user_id")

        result = await calc_fns.get_calculate_items(user_id)
        return web.json_response(
            {
                "user_id": user_id,
                "items": result["items"],
                "already_selected_categories": result["already_selected_categories"],
            },
            status=200,
        )
    except (ClientConnectorError, ConnectionRefusedError, OSError) as e:
        logger.warning("calculate: external service unreachable: %s", e)
        return validate.format_500_error(request)
    except Exception:
        logger.exception("calculate handler failed")
        return validate.format_500_error(request)
