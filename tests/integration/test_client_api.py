"""
Интеграционные тесты для Client API
"""

import pytest
from unittest.mock import patch, AsyncMock
import json

# Валидные UUID для тестов selection (ровно 5 категорий по настройкам)
_SELECTION_CATEGORY_IDS = [
    "00000000-0000-0000-0000-000000000001",
    "00000000-0000-0000-0000-000000000002",
    "00000000-0000-0000-0000-000000000003",
    "00000000-0000-0000-0000-000000000004",
    "00000000-0000-0000-0000-000000000005",
]


async def test_selection_success(aiohttp_client, app):
    """Тест: успешное сохранение выбора категорий"""
    test_user_id = 12345
    selection_data = {"user_id": test_user_id, "category_ids": _SELECTION_CATEGORY_IDS.copy()}

    with patch('functions.users.user_exists', new_callable=AsyncMock) as mock_user_exists, \
         patch('functions.selection.check_categories_exist', new_callable=AsyncMock) as mock_check, \
         patch('functions.selection.get_current_category_ids', new_callable=AsyncMock) as mock_get_current, \
         patch('functions.selection.save_selection_batch', new_callable=AsyncMock) as mock_save:
        mock_user_exists.return_value = True
        mock_check.return_value = True
        mock_get_current.return_value = None  # нет текущего выбора — сохраняем новый
        mock_save.return_value = []

        client = await aiohttp_client(app)
        resp = await client.request(
            "POST",
            "/api/v1/client/selection",
            headers={"Content-Type": "application/json"},
            data=json.dumps(selection_data)
        )

        assert resp.status == 200
        data = await resp.json()
        assert "category_ids" in data


async def test_selection_user_not_found(aiohttp_client, app):
    """Тест: пользователь не найден"""
    test_user_id = 12345
    selection_data = {"user_id": test_user_id, "category_ids": _SELECTION_CATEGORY_IDS.copy()}

    with patch('functions.users.user_exists', new_callable=AsyncMock) as mock_user_exists:
        mock_user_exists.return_value = False

        client = await aiohttp_client(app)
        resp = await client.request(
            "POST",
            "/api/v1/client/selection",
            headers={"Content-Type": "application/json"},
            data=json.dumps(selection_data)
        )

        assert resp.status == 404
        data = await resp.json()
        assert data["code"] == "NOT_FOUND"


async def test_selection_not_five_categories(aiohttp_client, app):
    """Тест: неверное количество категорий"""
    test_user_id = 12345
    selection_data = {
        "user_id": test_user_id,
        "category_ids": [
            "00000000-0000-0000-0000-000000000001",
            "00000000-0000-0000-0000-000000000002",
            "00000000-0000-0000-0000-000000000003",
        ]
    }

    client = await aiohttp_client(app)
    resp = await client.request(
        "POST",
        "/api/v1/client/selection",
        headers={"Content-Type": "application/json"},
        data=json.dumps(selection_data)
    )

    assert resp.status == 422
    data = await resp.json()
    assert data["code"] == "VALIDATION_FAILED"


async def test_selection_duplicate_categories(aiohttp_client, app):
    """Тест: дубликаты категорий"""
    test_user_id = 12345
    selection_data = {
        "user_id": test_user_id,
        "category_ids": [
            "00000000-0000-0000-0000-000000000001",
            "00000000-0000-0000-0000-000000000001",
            "00000000-0000-0000-0000-000000000002",
            "00000000-0000-0000-0000-000000000003",
            "00000000-0000-0000-0000-000000000004",
        ]
    }

    client = await aiohttp_client(app)
    resp = await client.request(
        "POST",
        "/api/v1/client/selection",
        headers={"Content-Type": "application/json"},
        data=json.dumps(selection_data)
    )

    assert resp.status == 422
    data = await resp.json()
    assert data["code"] == "VALIDATION_FAILED"


async def test_selection_invalid_user_uuid(aiohttp_client, app):
    """Тест: невалидный UUID пользователя"""
    selection_data = {
        "user_id": "invalid-uuid",
        "category_ids": ["cat1", "cat2", "cat3", "cat4", "cat5"]
    }

    client = await aiohttp_client(app)
    resp = await client.request(
        "POST",
        "/api/v1/client/selection",
        headers={"Content-Type": "application/json"},
        data=json.dumps(selection_data)
    )

    assert resp.status == 422
    data = await resp.json()
    assert data["code"] == "VALIDATION_FAILED"


async def test_selection_invalid_category_uuid(aiohttp_client, app):
    """Тест: невалидный UUID категории"""
    test_user_id = 12345
    selection_data = {
        "user_id": test_user_id,
        "category_ids": [
            "00000000-0000-0000-0000-000000000001",
            "invalid-uuid",
            "00000000-0000-0000-0000-000000000003",
            "00000000-0000-0000-0000-000000000004",
            "00000000-0000-0000-0000-000000000005",
        ]
    }

    client = await aiohttp_client(app)
    resp = await client.request(
        "POST",
        "/api/v1/client/selection",
        headers={"Content-Type": "application/json"},
        data=json.dumps(selection_data)
    )

    assert resp.status == 422
    data = await resp.json()
    assert data["code"] == "VALIDATION_FAILED"


async def test_selection_missing_user_id(aiohttp_client, app):
    """Тест: отсутствует user_id"""
    selection_data = {"category_ids": _SELECTION_CATEGORY_IDS.copy()}

    client = await aiohttp_client(app)
    resp = await client.request(
        "POST",
        "/api/v1/client/selection",
        headers={"Content-Type": "application/json"},
        data=json.dumps(selection_data)
    )

    assert resp.status == 422
    data = await resp.json()
    assert data["code"] == "VALIDATION_FAILED"


async def test_selection_missing_category_ids(aiohttp_client, app):
    """Тест: отсутствует category_ids"""
    test_user_id = 12345
    selection_data = {"user_id": test_user_id}

    client = await aiohttp_client(app)
    resp = await client.request(
        "POST",
        "/api/v1/client/selection",
        headers={"Content-Type": "application/json"},
        data=json.dumps(selection_data)
    )

    assert resp.status == 422
    data = await resp.json()
    assert data["code"] == "VALIDATION_FAILED"


def test_future_user_id_integer():
    """Тест для будущего изменения: user_id как integer в client API"""
    pytest.skip("user_id будет integer в будущем")
