"""
Интеграционные тесты для Offers/Progress API (минимальный набор)
"""

from unittest.mock import patch
import json


async def test_run_offers_success(aiohttp_client, app):
    test_user_id = 12345
    test_offers = [
        {
            "offer_id": "offer1",
            "category_id": "cat1",
            "name": "Special Offer 1",
            "benefit": {"cashback_percent": 5.0}
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
        assert "items" in data
        assert len(data["items"]) == 1


async def test_get_progress_success(aiohttp_client, app):
    client = await aiohttp_client(app)
    resp = await client.request("GET", "/api/v1/progress")

    assert resp.status == 200
    data = await resp.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 0
    assert len(data["items"]) == 0
