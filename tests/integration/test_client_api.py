"""
Интеграционные тесты для Client API
"""

import pytest
from unittest.mock import patch
import json


async def test_calculate_success(aiohttp_client, app):
    """Тест: успешный расчет категорий для пользователя"""
    test_user_id = 12345
    test_categories = [
        {
            "category_id": "cat1",
            "name": "Category 1",
            "subtitle": "Subtitle 1",
            "rate": {"min": 1.0, "max": 5.0},
            "expected_benefit_amount": None,
            "availability_status": "available",
            "availability_reason": None,
        }
    ]

    with patch('functions.users.user_exists') as mock_user_exists, \
         patch('functions.calculate.get_calculate_items') as mock_calculate:
        mock_user_exists.return_value = True
        mock_calculate.return_value = test_categories

        client = await aiohttp_client(app)
        resp = await client.request(
            "POST",
            "/api/v1/client/calculate",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"user_id": test_user_id})
        )

        assert resp.status == 200
        data = await resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["category_id"] == "cat1"


async def test_calculate_user_not_found(aiohttp_client, app):
    """Тест: пользователь не найден"""
    test_user_id = 12345

    with patch('functions.users.user_exists') as mock_user_exists:
        mock_user_exists.return_value = False

        client = await aiohttp_client(app)
        resp = await client.request(
            "POST",
            "/api/v1/client/calculate",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"user_id": test_user_id})
        )

        assert resp.status == 404
        data = await resp.json()
        assert data["code"] == "NOT_FOUND"


async def test_calculate_invalid_uuid(aiohttp_client, app):
    """Тест: невалидный UUID пользователя"""
    client = await aiohttp_client(app)
    resp = await client.request(
        "POST",
        "/api/v1/client/calculate",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"user_id": "invalid-uuid"})
    )

    assert resp.status == 422
    data = await resp.json()
    assert data["code"] == "VALIDATION_FAILED"


async def test_calculate_missing_user_id(aiohttp_client, app):
    """Тест: отсутствует user_id"""
    client = await aiohttp_client(app)
    resp = await client.request(
        "POST",
        "/api/v1/client/calculate",
        headers={"Content-Type": "application/json"},
        data=json.dumps({})
    )

    assert resp.status == 422
    data = await resp.json()
    assert data["code"] == "VALIDATION_FAILED"


async def test_selection_success(aiohttp_client, app):
    """Тест: успешное сохранение выбора категорий"""
    test_user_id = 12345
    selection_data = {
        "user_id": test_user_id,
        "category_ids": [
            "cat1", "cat2", "cat3", "cat4", "cat5"
        ]
    }

    with patch('functions.users.user_exists') as mock_user_exists, \
         patch('functions.selection.confirm_selection') as mock_selection:
        mock_user_exists.return_value = True
        mock_selection.return_value = None

        client = await aiohttp_client(app)
        resp = await client.request(
            "POST",
            "/api/v1/client/selection",
            headers={"Content-Type": "application/json"},
            data=json.dumps(selection_data)
        )

        assert resp.status == 200
        data = await resp.json()
        assert "message" in data


async def test_selection_user_not_found(aiohttp_client, app):
    """Тест: пользователь не найден"""
    test_user_id = 12345
    selection_data = {
        "user_id": test_user_id,
        "category_ids": ["cat1", "cat2", "cat3", "cat4", "cat5"]
    }

    with patch('functions.users.user_exists') as mock_user_exists:
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
    """Тест: не 5 категорий"""
    test_user_id = 12345
    selection_data = {
        "user_id": test_user_id,
        "category_ids": ["cat1", "cat2", "cat3"]
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
            "cat1", "cat1", "cat2", "cat3", "cat4"
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
            "cat1", "invalid-uuid", "cat3", "cat4", "cat5"
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
    selection_data = {
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


async def test_selection_missing_category_ids(aiohttp_client, app):
    """Тест: отсутствует category_ids"""
    test_user_id = 12345
    selection_data = {
        "user_id": test_user_id
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


def test_future_user_id_integer():
    """Тест для будущего изменения: user_id как integer в client API"""
    pytest.skip("user_id будет integer в будущем")
