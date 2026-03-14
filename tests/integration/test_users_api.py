"""
Интеграционные тесты для API пользователей
"""

from unittest.mock import patch


async def test_user_exists_success(aiohttp_client, app):
    with patch('functions.users.user_exists') as mock_user_exists:
        mock_user_exists.return_value = True

        client = await aiohttp_client(app)
        resp = await client.request("GET", "/api/v1/users/12345/exists")

        assert resp.status == 200
        data = await resp.json()
        assert data["exists"] is True
        assert data["user_id"] == 12345


async def test_user_exists_not_found(aiohttp_client, app):
    with patch('functions.users.user_exists') as mock_user_exists:
        mock_user_exists.return_value = False

        client = await aiohttp_client(app)
        resp = await client.request("GET", "/api/v1/users/99999/exists")

        assert resp.status == 200
        data = await resp.json()
        assert data["exists"] is False
        assert data["user_id"] == 99999


async def test_user_exists_invalid_id(aiohttp_client, app):
    client = await aiohttp_client(app)
    resp = await client.request("GET", "/api/v1/users/invalid-id/exists")
    assert resp.status == 422


async def test_user_exists_negative_id(aiohttp_client, app):
    client = await aiohttp_client(app)
    resp = await client.request("GET", "/api/v1/users/-1/exists")
    assert resp.status == 422


async def test_user_exists_zero_id(aiohttp_client, app):
    client = await aiohttp_client(app)
    resp = await client.request("GET", "/api/v1/users/0/exists")
    assert resp.status == 422


async def test_user_exists_database_error(aiohttp_client, app):
    with patch('functions.users.user_exists') as mock_user_exists:
        mock_user_exists.side_effect = Exception("Database connection failed")

        client = await aiohttp_client(app)
        resp = await client.get("/api/v1/users/12345/exists")
        assert resp.status == 500
