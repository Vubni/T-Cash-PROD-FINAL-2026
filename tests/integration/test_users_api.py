"""
Интеграционные тесты для API пользователей
"""

import pytest
from aiohttp.test import AioHTTPTestCase, unittest_run_loop
from unittest.mock import patch
import json


class TestUsersAPI(AioHTTPTestCase):
    
    async def get_application(self):
        from server import create_app
        return await create_app()
    
    @unittest_run_loop
    async def test_user_exists_success(self):
        with patch('functions.users.user_exists') as mock_user_exists:
            mock_user_exists.return_value = True
            
            resp = await self.client.request("GET", "/api/v1/users/12345/exists")
            
            assert resp.status == 200
            data = await resp.json()
            assert data["exists"] is True
            assert data["user_id"] == 12345
    
    @unittest_run_loop
    async def test_user_exists_not_found(self):
        with patch('functions.users.user_exists') as mock_user_exists:
            mock_user_exists.return_value = False
            
            resp = await self.client.request("GET", "/api/v1/users/99999/exists")
            
            assert resp.status == 200
            data = await resp.json()
            assert data["exists"] is False
            assert data["user_id"] == 99999
    
    @unittest_run_loop
    async def test_user_exists_invalid_id(self):
        resp = await self.client.request("GET", "/api/v1/users/invalid-id/exists")
        assert resp.status == 422
    
    @unittest_run_loop
    async def test_user_exists_negative_id(self):
        resp = await self.client.request("GET", "/api/v1/users/-1/exists")
        assert resp.status == 422
    
    @unittest_run_loop
    async def test_user_exists_zero_id(self):
        resp = await self.client.request("GET", "/api/v1/users/0/exists")
        assert resp.status == 422


@pytest.mark.asyncio
async def test_user_exists_database_error():
    from server import create_app
    
    app = await create_app()
    
    with patch('functions.users.user_exists') as mock_user_exists:
        mock_user_exists.side_effect = Exception("Database connection failed")
        
        async with app.test_client() as client:
            resp = await client.get("/api/v1/users/12345/exists")
            assert resp.status == 500
