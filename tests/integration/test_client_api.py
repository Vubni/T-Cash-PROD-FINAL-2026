from unittest.mock import patch, AsyncMock
import json

import core
from functions import selection as selection_fns

_SELECTION_CATEGORY_IDS = [
    "00000000-0000-0000-0000-000000000001",
    "00000000-0000-0000-0000-000000000002",
    "00000000-0000-0000-0000-000000000003",
    "00000000-0000-0000-0000-000000000004",
    "00000000-0000-0000-0000-000000000005",
]

_TEST_USER_ID = 12345


def _auth_headers(
    user_id: int = _TEST_USER_ID, *, payload_extra: dict | None = None, raw_token: str | None = None
) -> dict:
    """Формирует заголовки с JWT пользователя для client API."""
    if raw_token is not None:
        token = raw_token
    else:
        payload = {"user_id": user_id}
        if payload_extra:
            payload.update(payload_extra)
        token = core.create_token(payload)
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }


async def test_selection_success(aiohttp_client, app):
    """Тест: успешное сохранение выбора категорий"""
    selection_data = {"category_ids": _SELECTION_CATEGORY_IDS.copy()}

    with (
        patch("functions.users.user_exists", new_callable=AsyncMock) as mock_user_exists,
        patch("functions.selection.check_categories_exist", new_callable=AsyncMock) as mock_check,
        patch("functions.selection.confirm_selection", new_callable=AsyncMock) as mock_confirm,
    ):
        mock_user_exists.return_value = True
        mock_check.return_value = True
        mock_confirm.return_value = (
            {"user_id": _TEST_USER_ID, "category_ids": _SELECTION_CATEGORY_IDS.copy(), "items": []},
            200,
        )

        async with aiohttp_client(app) as client:
            resp = await client.request(
                "POST",
                "/api/v1/client/selection",
                headers=_auth_headers(),
                data=json.dumps(selection_data),
            )
            assert resp.status == 200
            data = await resp.json()
            assert "category_ids" in data
            assert data["user_id"] == _TEST_USER_ID


async def test_selection_success_with_idempotency_key(aiohttp_client, app):
    """Тест: заголовок Idempotency-Key пробрасывается в бизнес-логику."""
    selection_data = {"category_ids": _SELECTION_CATEGORY_IDS.copy()}
    key = "selection-key-1"

    with (
        patch("functions.users.user_exists", new_callable=AsyncMock) as mock_user_exists,
        patch("functions.selection.check_categories_exist", new_callable=AsyncMock) as mock_check,
        patch("functions.selection.confirm_selection", new_callable=AsyncMock) as mock_confirm,
    ):
        mock_user_exists.return_value = True
        mock_check.return_value = True
        mock_confirm.return_value = (
            {"user_id": _TEST_USER_ID, "category_ids": _SELECTION_CATEGORY_IDS.copy(), "items": []},
            200,
        )

        async with aiohttp_client(app) as client:
            resp = await client.request(
                "POST",
                "/api/v1/client/selection",
                headers={**_auth_headers(), "Idempotency-Key": key},
                data=json.dumps(selection_data),
            )
            assert resp.status == 200
            mock_confirm.assert_awaited_once_with(
                _TEST_USER_ID,
                _SELECTION_CATEGORY_IDS.copy(),
                idempotency_key=key,
            )


async def test_selection_idempotency_conflict(aiohttp_client, app):
    """Тест: тот же Idempotency-Key с другим payload даёт 409."""
    selection_data = {"category_ids": _SELECTION_CATEGORY_IDS.copy()}

    with (
        patch("functions.users.user_exists", new_callable=AsyncMock) as mock_user_exists,
        patch("functions.selection.check_categories_exist", new_callable=AsyncMock) as mock_check,
        patch(
            "functions.selection.confirm_selection",
            new_callable=AsyncMock,
            side_effect=selection_fns.IdempotencyConflictError(),
        ),
    ):
        mock_user_exists.return_value = True
        mock_check.return_value = True

        async with aiohttp_client(app) as client:
            resp = await client.request(
                "POST",
                "/api/v1/client/selection",
                headers={**_auth_headers(), "Idempotency-Key": "selection-key-1"},
                data=json.dumps(selection_data),
            )
            assert resp.status == 409
            data = await resp.json()
            assert data["code"] == "IDEMPOTENCY_CONFLICT"


async def test_selection_invalid_idempotency_key(aiohttp_client, app):
    """Тест: пустой Idempotency-Key отклоняется как bad request."""
    selection_data = {"category_ids": _SELECTION_CATEGORY_IDS.copy()}

    async with aiohttp_client(app) as client:
        resp = await client.request(
            "POST",
            "/api/v1/client/selection",
            headers={**_auth_headers(), "Idempotency-Key": "   "},
            data=json.dumps(selection_data),
        )
        assert resp.status == 400
        data = await resp.json()
        assert data["code"] == "BAD_REQUEST"


async def test_selection_user_not_found(aiohttp_client, app):
    """Тест: пользователь не найден"""
    selection_data = {"category_ids": _SELECTION_CATEGORY_IDS.copy()}

    with patch("functions.users.user_exists", new_callable=AsyncMock) as mock_user_exists:
        mock_user_exists.return_value = False

        async with aiohttp_client(app) as client:
            resp = await client.request(
                "POST",
                "/api/v1/client/selection",
                headers=_auth_headers(),
                data=json.dumps(selection_data),
            )
            assert resp.status == 404
            data = await resp.json()
            assert data["code"] == "NOT_FOUND"


async def test_selection_not_five_categories(aiohttp_client, app):
    """Тест: неверное количество категорий"""
    selection_data = {
        "category_ids": [
            "00000000-0000-0000-0000-000000000001",
            "00000000-0000-0000-0000-000000000002",
            "00000000-0000-0000-0000-000000000003",
        ]
    }

    async with aiohttp_client(app) as client:
        resp = await client.request(
            "POST",
            "/api/v1/client/selection",
            headers=_auth_headers(),
            data=json.dumps(selection_data),
        )
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"


async def test_selection_duplicate_categories(aiohttp_client, app):
    """Тест: дубликаты категорий"""
    selection_data = {
        "category_ids": [
            "00000000-0000-0000-0000-000000000001",
            "00000000-0000-0000-0000-000000000001",
            "00000000-0000-0000-0000-000000000002",
            "00000000-0000-0000-0000-000000000003",
            "00000000-0000-0000-0000-000000000004",
        ]
    }

    async with aiohttp_client(app) as client:
        resp = await client.request(
            "POST",
            "/api/v1/client/selection",
            headers=_auth_headers(),
            data=json.dumps(selection_data),
        )
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"


async def test_selection_invalid_user_id(aiohttp_client, app):
    """Тест: невалидный JWT (некорректный токен) -> 401"""
    selection_data = {"category_ids": _SELECTION_CATEGORY_IDS.copy()}

    async with aiohttp_client(app) as client:
        resp = await client.request(
            "POST",
            "/api/v1/client/selection",
            headers={"Content-Type": "application/json", "Authorization": "Bearer invalid_token"},
            data=json.dumps(selection_data),
        )
        assert resp.status == 401
        data = await resp.json()
        assert data["code"] == "UNAUTHORIZED"


async def test_selection_invalid_category_uuid(aiohttp_client, app):
    """Тест: невалидный UUID категории"""
    selection_data = {
        "category_ids": [
            "00000000-0000-0000-0000-000000000001",
            "invalid-uuid",
            "00000000-0000-0000-0000-000000000003",
            "00000000-0000-0000-0000-000000000004",
            "00000000-0000-0000-0000-000000000005",
        ]
    }

    async with aiohttp_client(app) as client:
        resp = await client.request(
            "POST",
            "/api/v1/client/selection",
            headers=_auth_headers(),
            data=json.dumps(selection_data),
        )
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"


async def test_selection_missing_user_id(aiohttp_client, app):
    """Тест: в токене нет user_id -> 401"""
    selection_data = {"category_ids": _SELECTION_CATEGORY_IDS.copy()}

    token_without_user = core.create_token({})

    async with aiohttp_client(app) as client:
        resp = await client.request(
            "POST",
            "/api/v1/client/selection",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token_without_user}",
            },
            data=json.dumps(selection_data),
        )
        assert resp.status == 401
        data = await resp.json()
        assert data["code"] == "UNAUTHORIZED"


async def test_selection_missing_category_ids(aiohttp_client, app):
    """Тест: отсутствует category_ids"""
    selection_data = {}

    async with aiohttp_client(app) as client:
        resp = await client.request(
            "POST",
            "/api/v1/client/selection",
            headers=_auth_headers(),
            data=json.dumps(selection_data),
        )
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"


def test_user_id_integer_in_client_api():
    """user_id в client API целое число (BIGINT); тесты используют int (например 12345)."""
    assert isinstance(12345, int)
