"""
Интеграционные тесты для Offers/Progress API
"""

import pytest
from unittest.mock import patch
import json


async def test_run_offers_success(aiohttp_client, app):
    """✅ ПОЗИТИВНЫЙ: успешный запуск офферов"""
    test_user_id = 12345
    test_offers = [
        {
            "category_id": "cat1",
            "name": "Special Offer 1",
        },
        {
            "category_id": "cat2",
            "name": "Special Offer 2",
        }
    ]

    with patch('functions.calculate.get_calculate_items') as mock_calc, \
         patch('functions.users.user_exists') as mock_exists:
        mock_exists.return_value = True
        mock_calc.return_value = test_offers

        client = await aiohttp_client(app)
        resp = await client.request(
            "POST",
            "/api/v1/offers/run",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"user_id": test_user_id})
        )

        assert resp.status == 200
        data = await resp.json()
        assert len(data["items"]) == 2
        assert data["items"][0]["category_id"] == "cat1"


async def test_run_offers_user_not_found(aiohttp_client, app):
    """❌ НЕГАТИВНЫЙ: пользователь не найден"""
    test_user_id = 99999

    with patch('functions.users.user_exists') as mock_exists:
        mock_exists.return_value = False

        client = await aiohttp_client(app)
        resp = await client.request(
            "POST",
            "/api/v1/offers/run",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"user_id": test_user_id})
        )

        assert resp.status == 404
        data = await resp.json()
        assert data["code"] == "NOT_FOUND"


async def test_run_offers_missing_user_id(aiohttp_client, app):
    """❌ НЕГАТИВНЫЙ: отсутствует user_id в теле"""
    client = await aiohttp_client(app)
    resp = await client.request(
        "POST",
        "/api/v1/offers/run",
        headers={"Content-Type": "application/json"},
        data=json.dumps({})
    )

    assert resp.status == 422
    data = await resp.json()
    assert data["code"] == "VALIDATION_FAILED"


async def test_run_offers_invalid_user_id(aiohttp_client, app):
    """❌ НЕГАТИВНЫЙ: невалидный user_id"""
    client = await aiohttp_client(app)
    resp = await client.request(
        "POST",
        "/api/v1/offers/run",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"user_id": "invalid-id"})
    )

    assert resp.status == 422
    data = await resp.json()
    assert data["code"] == "VALIDATION_FAILED"


async def test_get_progress_success(aiohttp_client, app):
    """✅ ПОЗИТИВНЫЙ: успешное получение прогресса (текущий API возвращает пустой список)"""
    client = await aiohttp_client(app)
    resp = await client.request("GET", "/api/v1/progress")

    assert resp.status == 200
    data = await resp.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 0
    assert len(data["items"]) == 0


async def test_offers_progress_database_error(aiohttp_client, app):
    """❌ НЕГАТИВНЫЙ: ошибка при расчёте офферов"""
    with patch('functions.calculate.get_calculate_items') as mock_calc, \
         patch('functions.users.user_exists') as mock_exists:
        mock_exists.return_value = True
        mock_calc.side_effect = Exception("Database connection failed")

        client = await aiohttp_client(app)
        resp = await client.post(
            "/api/v1/offers/run",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"user_id": 12345})
        )

        assert resp.status == 500
