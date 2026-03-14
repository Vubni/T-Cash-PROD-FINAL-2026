"""
Интеграционные тесты для Client API
"""

import pytest
from aiohttp import web
from aiohttp.test import AioHTTPTestCase, unittest_run_loop
from unittest.mock import patch
import json


class TestClientAPI(AioHTTPTestCase):
    """Интеграционные тесты для Client API"""
    
    async def get_application(self):
        """Создание тестового приложения"""
        from server import create_app
        return await create_app()
    
    @unittest_run_loop
    async def test_calculate_success(self):
        """Тест: успешный расчет категорий для пользователя"""
        test_user_id = 12345  # Integer
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
            
            resp = await self.client.request(
                "POST",
                "/api/v1/client/calculate",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"user_id": test_user_id})
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert len(data["items"]) == 1
            assert data["items"][0]["category_id"] == "cat1"
    
    @unittest_run_loop
    async def test_calculate_user_not_found(self):
        """Тест: пользователь не найден"""
        test_user_id = 12345
        
        with patch('functions.users.user_exists') as mock_user_exists:
            mock_user_exists.return_value = False
            
            resp = await self.client.request(
                "POST",
                "/api/v1/client/calculate",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"user_id": test_user_id})
            )
            
            assert resp.status == 404
            data = await resp.json()
            assert data["code"] == "NOT_FOUND"
    
    @unittest_run_loop
    async def test_calculate_invalid_uuid(self):
        """Тест: невалидный UUID пользователя"""
        resp = await self.client.request(
            "POST",
            "/api/v1/client/calculate",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"user_id": "invalid-uuid"})
        )
        
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"
    
    @unittest_run_loop
    async def test_calculate_missing_user_id(self):
        """Тест: отсутствует user_id"""
        resp = await self.client.request(
            "POST",
            "/api/v1/client/calculate",
            headers={"Content-Type": "application/json"},
            data=json.dumps({})
        )
        
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"
    
    @unittest_run_loop
    async def test_selection_success(self):
        """Тест: успешное сохранение выбора категорий"""
        test_user_id = 12345  # UUID
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
            
            resp = await self.client.request(
                "POST",
                "/api/v1/client/selection",
                headers={"Content-Type": "application/json"},
                data=json.dumps(selection_data)
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert "message" in data
    
    @unittest_run_loop
    async def test_selection_user_not_found(self):
        """Тест: пользователь не найден"""
        test_user_id = 12345
        selection_data = {
            "user_id": test_user_id,
            "category_ids": ["cat1", "cat2", "cat3", "cat4", "cat5"]
        }
        
        with patch('functions.users.user_exists') as mock_user_exists:
            mock_user_exists.return_value = False
            
            resp = await self.client.request(
                "POST",
                "/api/v1/client/selection",
                headers={"Content-Type": "application/json"},
                data=json.dumps(selection_data)
            )
            
            assert resp.status == 404
            data = await resp.json()
            assert data["code"] == "NOT_FOUND"
    
    @unittest_run_loop
    async def test_selection_not_five_categories(self):
        """Тест: не 5 категорий"""
        test_user_id = 12345
        selection_data = {
            "user_id": test_user_id,
            "category_ids": ["cat1", "cat2", "cat3"]  # Только 3 категории
        }
        
        resp = await self.client.request(
            "POST",
            "/api/v1/client/selection",
            headers={"Content-Type": "application/json"},
            data=json.dumps(selection_data)
        )
        
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"
    
    @unittest_run_loop
    async def test_selection_duplicate_categories(self):
        """Тест: дубликаты категорий"""
        test_user_id = 12345
        selection_data = {
            "user_id": test_user_id,
            "category_ids": [
                "cat1", "cat1", "cat2", "cat3", "cat4"  # cat1 дублируется
            ]
        }
        
        resp = await self.client.request(
            "POST",
            "/api/v1/client/selection",
            headers={"Content-Type": "application/json"},
            data=json.dumps(selection_data)
        )
        
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"
    
    @unittest_run_loop
    async def test_selection_invalid_user_uuid(self):
        """Тест: невалидный UUID пользователя"""
        selection_data = {
            "user_id": "invalid-uuid",
            "category_ids": ["cat1", "cat2", "cat3", "cat4", "cat5"]
        }
        
        resp = await self.client.request(
            "POST",
            "/api/v1/client/selection",
            headers={"Content-Type": "application/json"},
            data=json.dumps(selection_data)
        )
        
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"
    
    @unittest_run_loop
    async def test_selection_invalid_category_uuid(self):
        """Тест: невалидный UUID категории"""
        test_user_id = 12345
        selection_data = {
            "user_id": test_user_id,
            "category_ids": [
                "cat1", "invalid-uuid", "cat3", "cat4", "cat5"
            ]
        }
        
        resp = await self.client.request(
            "POST",
            "/api/v1/client/selection",
            headers={"Content-Type": "application/json"},
            data=json.dumps(selection_data)
        )
        
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"
    
    @unittest_run_loop
    async def test_selection_missing_user_id(self):
        """Тест: отсутствует user_id"""
        selection_data = {
            "category_ids": ["cat1", "cat2", "cat3", "cat4", "cat5"]
        }
        
        resp = await self.client.request(
            "POST",
            "/api/v1/client/selection",
            headers={"Content-Type": "application/json"},
            data=json.dumps(selection_data)
        )
        
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"
    
    @unittest_run_loop
    async def test_selection_missing_category_ids(self):
        """Тест: отсутствует category_ids"""
        test_user_id = 12345
        selection_data = {
            "user_id": test_user_id
        }
        
        resp = await self.client.request(
            "POST",
            "/api/v1/client/selection",
            headers={"Content-Type": "application/json"},
            data=json.dumps(selection_data)
        )
        
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"


@pytest.mark.asyncio
async def test_future_user_id_integer():
    """Тест для будущего изменения: user_id как integer в client API"""
    # Этот тест будет актуален после перевода user_id на integer
    # Пока пропускаем
    pytest.skip("user_id будет integer в будущем")
