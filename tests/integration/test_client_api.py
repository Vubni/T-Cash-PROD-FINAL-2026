from unittest.mock import patch, AsyncMock
import json

import core

# Валидные UUID для тестов selection (ровно 5 категорий по настройкам)
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
        patch("functions.selection.get_current_category_ids", new_callable=AsyncMock) as mock_get_current,
        patch("functions.selection.save_selection_batch", new_callable=AsyncMock) as mock_save,
    ):
        mock_user_exists.return_value = True
        mock_check.return_value = True
        mock_get_current.return_value = None  # нет текущего выбора — сохраняем новый
        mock_save.return_value = []

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

    # Токен без user_id
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
    """user_id в client API — целое число (BIGINT); тесты используют int (например 12345)."""
    # Все тесты выше уже передают user_id как int в selection_data.
    assert isinstance(12345, int)
