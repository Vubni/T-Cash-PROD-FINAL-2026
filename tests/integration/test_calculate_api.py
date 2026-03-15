"""Интеграционные тесты для POST /api/v1/offers/run. get_calculate_items мокается."""

from unittest.mock import patch, AsyncMock

import core


_TEST_USER_ID = 12345


def _auth_headers():
    """Заголовки с JWT пользователя для offers/run."""
    token = core.create_token({"user_id": _TEST_USER_ID})
    return {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}


async def test_offers_run_success(aiohttp_client, app):
    """POST /offers/run возвращает 200 и список items при успешном расчёте."""
    mock_result = {
        "items": [
            {"category_id": "cat-1", "name": "Cat1", "subtitle": "Sub1", "cashback": 5, "reasons": []}
        ],
        "already_selected_categories": False,
    }

    with patch("functions.calculate.get_calculate_items", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_result

        async with aiohttp_client(app) as client:
            resp = await client.post(
                "/api/v1/offers/run",
                headers=_auth_headers(),
                json={},
            )
            assert resp.status == 200
            data = await resp.json()
            assert data["user_id"] == _TEST_USER_ID
            assert "items" in data
            assert data["already_selected_categories"] is False
            assert len(data["items"]) == 1
            item = data["items"][0]
            assert item["name"] == "Cat1"
            assert item["category_id"] == "cat-1"
            assert item["cashback"] == 5
            assert "reasons" in item
            mock_get.assert_called_once_with(_TEST_USER_ID)


async def test_offers_run_already_selected(aiohttp_client, app):
    """POST /offers/run с already_selected_categories=True возвращает 200 и items."""
    mock_result = {
        "items": [{"category_id": "c1", "name": "A", "subtitle": "", "cashback": 10, "reasons": []}],
        "already_selected_categories": True,
    }

    with patch("functions.calculate.get_calculate_items", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_result

        async with aiohttp_client(app) as client:
            resp = await client.post("/api/v1/offers/run", headers=_auth_headers(), json={})
            assert resp.status == 200
            data = await resp.json()
            assert data["already_selected_categories"] is True
            assert len(data["items"]) == 1


async def test_offers_run_unauthorized(aiohttp_client, app):
    """POST /offers/run без токена возвращает 401."""
    with patch("functions.calculate.get_calculate_items", new_callable=AsyncMock):
        async with aiohttp_client(app) as client:
            resp = await client.post(
                "/api/v1/offers/run",
                headers={"Content-Type": "application/json"},
                json={},
            )
            assert resp.status == 401
            data = await resp.json()
            assert data.get("code") == "UNAUTHORIZED"


async def test_offers_run_empty_items(aiohttp_client, app):
    """POST /offers/run с пустым списком items возвращает 200 и already_selected_categories=False."""
    with patch("functions.calculate.get_calculate_items", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"items": [], "already_selected_categories": False}

        async with aiohttp_client(app) as client:
            resp = await client.post("/api/v1/offers/run", headers=_auth_headers(), json={})
            assert resp.status == 200
            data = await resp.json()
            assert data["items"] == []
            assert data["already_selected_categories"] is False
            mock_get.assert_called_once_with(_TEST_USER_ID)


async def test_offers_run_calc_error_returns_500(aiohttp_client, app):
    """При ошибке get_calculate_items возвращается 500."""
    with patch("functions.calculate.get_calculate_items", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Calc service unreachable")

        async with aiohttp_client(app) as client:
            resp = await client.post("/api/v1/offers/run", headers=_auth_headers(), json={})
            assert resp.status == 500
            data = await resp.json()
            assert data.get("code") == "INTERNAL_ERROR"
