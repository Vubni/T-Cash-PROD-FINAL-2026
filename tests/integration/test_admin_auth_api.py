"""
Интеграционные тесты для Admin Auth API
"""

import pytest
from aiohttp.test import AioHTTPTestCase, unittest_run_loop
from unittest.mock import patch
import json


class TestAdminAuthAPI(AioHTTPTestCase):
    
    async def get_application(self):
        from server import create_app
        return await create_app()
    
    @unittest_run_loop
    async def test_register_admin_success(self):
        admin_data = {
            "login": "newadmin",
            "password": "password123"
        }
        
        with patch('functions.admin_auth.register_admin') as mock_register:
            mock_register.return_value = 5
            
            resp = await self.client.request(
                "POST",
                "/api/v1/admin/auth/register",
                headers={"Content-Type": "application/json"},
                data=json.dumps(admin_data)
            )
            
            assert resp.status == 201
            data = await resp.json()
            assert data["admin_id"] == 5
    
    @unittest_run_loop
    async def test_login_admin_success(self):
        login_data = {
            "login": "admin",
            "password": "password123"
        }
        
        with patch('functions.admin_auth.verify_admin') as mock_verify:
            mock_verify.return_value = {
                "admin_id": 1,
                "login": "admin",
                "approved": True
            }
            
            resp = await self.client.request(
                "POST",
                "/api/v1/admin/auth/login",
                headers={"Content-Type": "application/json"},
                data=json.dumps(login_data)
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert data["admin_id"] == 1
    
    @unittest_run_loop
    async def test_approve_admin_success(self):
        approve_data = {"admin_id": 2}
        
        with patch('functions.admin_auth.approve_admin') as mock_approve:
            mock_approve.return_value = True
            
            resp = await self.client.request(
                "POST",
                "/api/v1/admin/auth/approve",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer main_token"
                },
                data=json.dumps(approve_data)
            )
            
            assert resp.status == 200
