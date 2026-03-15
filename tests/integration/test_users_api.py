"""
Интеграционные тесты для API пользователей
"""

from unittest.mock import patch


async def test_user_auth_success(aiohttp_client, app):
    with patch("functions.users.user_exists") as mock_user_exists:
        mock_user_exists.return_value = True

        async with aiohttp_client(app) as client:
            resp = await client.request("GET", "/api/v1/users/12345/auth")
            assert resp.status == 200
            data = await resp.json()
            assert data["user_id"] == 12345
            assert isinstance(data.get("token"), str)
            assert data["token"]


async def test_user_auth_not_found(aiohttp_client, app):
    with patch("functions.users.user_exists") as mock_user_exists:
        mock_user_exists.return_value = False

        async with aiohttp_client(app) as client:
            resp = await client.request("GET", "/api/v1/users/99999/auth")
            assert resp.status == 404
            data = await resp.json()
            assert data.get("code") == "NOT_FOUND"


async def test_user_auth_invalid_id(aiohttp_client, app):
    async with aiohttp_client(app) as client:
        resp = await client.request("GET", "/api/v1/users/invalid-id/auth")
        assert resp.status == 422


async def test_user_auth_negative_id(aiohttp_client, app):
    """user_id=-1 должен возвращать 422 (невалидный user_id)."""
    async with aiohttp_client(app) as client:
        resp = await client.request("GET", "/api/v1/users/-1/auth")
        assert resp.status == 422
        data = await resp.json()
        assert data.get("code") == "VALIDATION_FAILED"


async def test_user_auth_zero_id(aiohttp_client, app):
    """user_id=0 должен возвращать 422 (невалидный user_id)."""
    async with aiohttp_client(app) as client:
        resp = await client.request("GET", "/api/v1/users/0/auth")
        assert resp.status == 422
        data = await resp.json()
        assert data.get("code") == "VALIDATION_FAILED"


async def test_user_auth_database_error(aiohttp_client, app):
    with patch("functions.users.user_exists") as mock_user_exists:
        mock_user_exists.side_effect = Exception("Database connection failed")

        async with aiohttp_client(app) as client:
            resp = await client.get("/api/v1/users/12345/auth")
            assert resp.status == 500
