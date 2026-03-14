import pytest
from aiohttp import web
from aiohttp.test import AioHTTPTestCase, unittest_run_loop
from unittest.mock import patch
import json


class TestCategoriesAPI(AioHTTPTestCase):
    async def get_application(self):
        """Создание тестового приложения"""
        from server import create_app
        return await create_app()
    
    @unittest_run_loop
    async def test_get_categories_success(self):
        """Тест: успешное получение списка категорий"""
        test_categories = [
            {
                "category_id": "cat1",
                "name": "Category 1",
                "subtitle": "Subtitle 1",
                "budget_amount": 100000,
                "status": "active"
            },
            {
                "category_id": "cat2", 
                "name": "Category 2",
                "subtitle": "Subtitle 2",
                "budget_amount": 200000,
                "status": "active"
            }
        ]
        
        with patch('functions.categories.get_categories') as mock_get:
            mock_get.return_value = test_categories
            
            resp = await self.client.request(
                "GET",
                "/api/v1/admin/categories"
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert len(data["items"]) == 2
            assert data["total"] == 2
    
    @unittest_run_loop
    async def test_get_categories_with_pagination(self):
        """Тест: получение категорий с пагинацией"""
        with patch('functions.categories.get_categories') as mock_get:
            mock_get.return_value = []
            
            resp = await self.client.request(
                "GET",
                "/api/v1/admin/categories?limit=5&offset=10"
            )
            
            assert resp.status == 200
            mock_get.assert_called_once_with(limit=5, offset=10)
    
    @unittest_run_loop
    async def test_get_categories_invalid_limit(self):
        """Тест: невалидный параметр limit"""
        resp = await self.client.request(
            "GET",
            "/api/v1/admin/categories?limit=501"
        )
        
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"
    
    @unittest_run_loop
    async def test_get_categories_negative_offset(self):
        """Тест: отрицательный offset"""
        resp = await self.client.request(
            "GET",
            "/api/v1/admin/categories?offset=-1"
        )
        
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"
    
    @unittest_run_loop
    async def test_create_category_success(self):
        """Тест: успешное создание категории"""
        category_data = {
            "name": "Test Category",
            "subtitle": "Test subtitle", 
            "icon_key": "test",
            "budget_amount": 100000,
            "audience_segments": ["mass"],
            "rule_id": "rule1"
        }
        
        with patch('functions.categories.create_category') as mock_create:
            mock_create.return_value = "cat123"
            
            resp = await self.client.request(
                "POST",
                "/api/v1/admin/categories",
                headers={"Content-Type": "application/json"},
                data=json.dumps(category_data)
            )
            
            assert resp.status == 201
            data = await resp.json()
            assert data["category_id"] == "cat123"
    
    @unittest_run_loop
    async def test_create_category_missing_fields(self):
        """Тест: создание категории с отсутствующими полями"""
        category_data = {"name": "Test Category"}  # Недостаточно данных
        
        resp = await self.client.request(
            "POST",
            "/api/v1/admin/categories",
            headers={"Content-Type": "application/json"},
            data=json.dumps(category_data)
        )
        
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"
    
    @unittest_run_loop
    async def test_create_category_negative_budget(self):
        """Тест: создание категории с отрицательным бюджетом"""
        category_data = {
            "name": "Test Category",
            "subtitle": "Test subtitle",
            "icon_key": "test", 
            "budget_amount": -1000,
            "audience_segments": ["mass"],
            "rule_id": "rule1"
        }
        
        resp = await self.client.request(
            "POST",
            "/api/v1/admin/categories",
            headers={"Content-Type": "application/json"},
            data=json.dumps(category_data)
        )
        
        assert resp.status == 422
    
    @unittest_run_loop
    async def test_get_category_success(self):
        """Тест: успешное получение категории"""
        test_category = {
            "category_id": "cat1",
            "name": "Category 1",
            "subtitle": "Subtitle 1",
            "budget_amount": 100000,
            "status": "active"
        }
        
        with patch('functions.categories.get_category') as mock_get:
            mock_get.return_value = test_category
            
            resp = await self.client.request(
                "GET",
                "/api/v1/admin/categories/cat1"
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert data["category_id"] == "cat1"
            assert data["name"] == "Category 1"
    
    @unittest_run_loop
    async def test_get_category_not_found(self):
        """Тест: категория не найдена"""
        with patch('functions.categories.get_category') as mock_get:
            mock_get.return_value = None
            
            resp = await self.client.request(
                "GET",
                "/api/v1/admin/categories/nonexistent"
            )
            
            assert resp.status == 404
            data = await resp.json()
            assert data["code"] == "NOT_FOUND"
    
    @unittest_run_loop
    async def test_get_category_invalid_uuid(self):
        """Тест: невалидный UUID категории"""
        resp = await self.client.request(
            "GET",
            "/api/v1/admin/categories/invalid-uuid"
        )
        
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"
    
    @unittest_run_loop
    async def test_update_category_success(self):
        """Тест: успешное обновление категории"""
        update_data = {
            "name": "Updated Category",
            "budget_amount": 150000
        }
        
        with patch('functions.categories.update_category') as mock_update:
            mock_update.return_value = True
            
            resp = await self.client.request(
                "PATCH",
                "/api/v1/admin/categories/cat1",
                headers={"Content-Type": "application/json"},
                data=json.dumps(update_data)
            )
            
            assert resp.status == 200
    
    @unittest_run_loop
    async def test_update_category_not_found(self):
        """Тест: категория для обновления не найдена"""
        update_data = {"name": "Updated Category"}
        
        with patch('functions.categories.update_category') as mock_update:
            mock_update.return_value = False
            
            resp = await self.client.request(
                "PATCH",
                "/api/v1/admin/categories/nonexistent",
                headers={"Content-Type": "application/json"},
                data=json.dumps(update_data)
            )
            
            assert resp.status == 404
    
    @unittest_run_loop
    async def test_create_category_rule_success(self):
        """Тест: успешное создание правила для категории"""
        rule_data = {
            "min_age": 18,
            "max_age": 65,
            "gender": "any",
            "income": 50000
        }
        
        with patch('functions.rules.create_rule') as mock_create:
            mock_create.return_value = "rule123"
            
            resp = await self.client.request(
                "POST",
                "/api/v1/admin/categories/cat1/rule",
                headers={"Content-Type": "application/json"},
                data=json.dumps(rule_data)
            )
            
            assert resp.status == 201
            data = await resp.json()
            assert data["rule_id"] == "rule123"
