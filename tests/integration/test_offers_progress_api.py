"""
Интеграционные тесты для Offers/Progress API
"""

import pytest
from aiohttp import web
from aiohttp.test import AioHTTPTestCase, unittest_run_loop
from unittest.mock import patch
import json


class TestOffersAPI(AioHTTPTestCase):
    """Интеграционные тесты для Offers API"""
    
    async def get_application(self):
        """Создание тестового приложения"""
        from server import create_app
        return await create_app()
    
    @unittest_run_loop
    async def test_run_offers_success(self):
        """✅ ПОЗИТИВНЫЙ: успешный запуск офферов"""
        test_user_id = 12345
        offers_data = {
            "categories": ["cat1", "cat2", "cat3"],
            "preferences": {"min_rate": 1.0}
        }
        
        test_offers = [
            {
                "offer_id": "offer1",
                "category_id": "cat1",
                "name": "Special Offer 1",
                "conditions": {"min_age": 18, "min_rate": 1.0},
                "benefit": {"cashback_percent": 5.0}
            },
            {
                "offer_id": "offer2",
                "category_id": "cat2",
                "name": "Special Offer 2",
                "conditions": {"min_age": 18, "min_rate": 2.0},
                "benefit": {"cashback_percent": 7.0}
            }
        ]
        
        with patch('functions.offers.run_offers') as mock_offers:
            mock_offers.return_value = test_offers
            
            resp = await self.client.request(
                "POST",
                "/api/v1/offers/run",
                headers={
                    "Content-Type": "application/json",
                    "X-User-ID": str(test_user_id)
                },
                data=json.dumps(offers_data)
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert len(data["offers"]) == 2
            assert data["offers"][0]["offer_id"] == "offer1"
    
    @unittest_run_loop
    async def test_run_offers_user_not_found(self):
        """❌ НЕГАТИВНЫЙ: пользователь не найден"""
        test_user_id = 99999
        offers_data = {"categories": ["cat1"]}
        
        with patch('functions.offers.run_offers') as mock_offers:
            mock_offers.return_value = []
            
            resp = await self.client.request(
                "POST",
                "/api/v1/offers/run",
                headers={
                    "Content-Type": "application/json",
                    "X-User-ID": str(test_user_id)
                },
                data=json.dumps(offers_data)
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert len(data["offers"]) == 0
    
    @unittest_run_loop
    async def test_run_offers_missing_user_id_header(self):
        """❌ НЕГАТИВНЫЙ: отсутствует заголовок X-User-ID"""
        offers_data = {"categories": ["cat1"]}
        
        resp = await self.client.request(
            "POST",
            "/api/v1/offers/run",
            headers={"Content-Type": "application/json"},
            data=json.dumps(offers_data)
        )
        
        assert resp.status == 400
        data = await resp.json()
        assert data["code"] == "BAD_REQUEST"
    
    @unittest_run_loop
    async def test_run_offers_invalid_user_id(self):
        """❌ НЕГАТИВНЫЙ: невалидный user_id"""
        offers_data = {"categories": ["cat1"]}
        
        resp = await self.client.request(
            "POST",
            "/api/v1/offers/run",
            headers={
                "Content-Type": "application/json",
                "X-User-ID": "invalid-id"
            },
            data=json.dumps(offers_data)
        )
        
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"
    
    @unittest_run_loop
    async def test_run_offers_empty_categories(self):
        """❌ НЕГАТИВНЫЙ: пустой список категорий"""
        test_user_id = 12345
        offers_data = {"categories": []}
        
        resp = await self.client.request(
            "POST",
            "/api/v1/offers/run",
            headers={
                "Content-Type": "application/json",
                "X-User-ID": str(test_user_id)
            },
            data=json.dumps(offers_data)
        )
        
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"
    
    @unittest_run_loop
    async def test_run_offers_invalid_categories(self):
        """❌ НЕГАТИВНЫЙ: невалидные категории"""
        test_user_id = 12345
        offers_data = {"categories": ["invalid_cat"]}
        
        with patch('functions.offers.run_offers') as mock_offers:
            mock_offers.return_value = []
            
            resp = await self.client.request(
                "POST",
                "/api/v1/offers/run",
                headers={
                    "Content-Type": "application/json",
                    "X-User-ID": str(test_user_id)
                },
                data=json.dumps(offers_data)
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert len(data["offers"]) == 0
    
    @unittest_run_loop
    async def test_get_available_offers_success(self):
        """✅ ПОЗИТИВНЫЙ: получение доступных офферов"""
        test_user_id = 12345
        test_offers = [
            {
                "offer_id": "offer1",
                "category_id": "cat1",
                "name": "Available Offer 1",
                "conditions": {"min_age": 18},
                "benefit": {"cashback_percent": 5.0}
            }
        ]
        
        with patch('functions.offers.get_available_offers') as mock_offers:
            mock_offers.return_value = test_offers
            
            resp = await self.client.request(
                "GET",
                "/api/v1/offers/available",
                headers={"X-User-ID": str(test_user_id)}
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert len(data["offers"]) == 1
            assert data["offers"][0]["offer_id"] == "offer1"
    
    @unittest_run_loop
    async def test_get_available_offers_empty(self):
        """✅ ПОЗИТИВНЫЙ: нет доступных офферов"""
        test_user_id = 12345
        
        with patch('functions.offers.get_available_offers') as mock_offers:
            mock_offers.return_value = []
            
            resp = await self.client.request(
                "GET",
                "/api/v1/offers/available",
                headers={"X-User-ID": str(test_user_id)}
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert len(data["offers"]) == 0


class TestProgressAPI(AioHTTPTestCase):
    """Интеграционные тесты для Progress API"""
    
    async def get_application(self):
        """Создание тестового приложения"""
        from server import create_app
        return await create_app()
    
    @unittest_run_loop
    async def test_get_progress_success(self):
        """✅ ПОЗИТИВНЫЙ: успешное получение прогресса"""
        test_user_id = 12345
        test_progress = [
            {
                "category_id": "cat1",
                "category_name": "Category 1",
                "progress": 0.5,
                "target_amount": 1000,
                "current_amount": 500,
                "status": "active",
                "benefit_earned": 25.0
            },
            {
                "category_id": "cat2",
                "category_name": "Category 2",
                "progress": 0.8,
                "target_amount": 2000,
                "current_amount": 1600,
                "status": "active",
                "benefit_earned": 80.0
            }
        ]
        
        with patch('functions.progress.get_user_progress') as mock_progress:
            mock_progress.return_value = test_progress
            
            resp = await self.client.request(
                "GET",
                "/api/v1/progress",
                headers={"X-User-ID": str(test_user_id)}
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert len(data["items"]) == 2
            assert data["total"] == 2
            assert data["items"][0]["progress"] == 0.5
            assert data["items"][1]["category_id"] == "cat2"
    
    @unittest_run_loop
    async def test_get_progress_empty(self):
        """✅ ПОЗИТИВНЫЙ: у пользователя нет прогресса"""
        test_user_id = 12345
        
        with patch('functions.progress.get_user_progress') as mock_progress:
            mock_progress.return_value = []
            
            resp = await self.client.request(
                "GET",
                "/api/v1/progress",
                headers={"X-User-ID": str(test_user_id)}
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert len(data["items"]) == 0
            assert data["total"] == 0
    
    @unittest_run_loop
    async def test_get_progress_missing_user_id_header(self):
        """❌ НЕГАТИВНЫЙ: отсутствует заголовок X-User-ID"""
        resp = await self.client.request("GET", "/api/v1/progress")
        
        assert resp.status == 400
        data = await resp.json()
        assert data["code"] == "BAD_REQUEST"
    
    @unittest_run_loop
    async def test_get_progress_invalid_user_id(self):
        """❌ НЕГАТИВНЫЙ: невалидный user_id"""
        resp = await self.client.request(
            "GET",
            "/api/v1/progress",
            headers={"X-User-ID": "invalid-id"}
        )
        
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"
    
    @unittest_run_loop
    async def test_get_progress_user_not_found(self):
        """❌ НЕГАТИВНЫЙ: пользователь не найден"""
        test_user_id = 99999
        
        with patch('functions.progress.get_user_progress') as mock_progress:
            mock_progress.return_value = []
            
            resp = await self.client.request(
                "GET",
                "/api/v1/progress",
                headers={"X-User-ID": str(test_user_id)}
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert len(data["items"]) == 0
    
    @unittest_run_loop
    async def test_get_progress_with_category_filter(self):
        """✅ ПОЗИТИВНЫЙ: фильтрация по категории"""
        test_user_id = 12345
        test_progress = [
            {
                "category_id": "cat1",
                "category_name": "Category 1",
                "progress": 0.5,
                "status": "active"
            }
        ]
        
        with patch('functions.progress.get_user_progress') as mock_progress:
            mock_progress.return_value = test_progress
            
            resp = await self.client.request(
                "GET",
                "/api/v1/progress?category_id=cat1",
                headers={"X-User-ID": str(test_user_id)}
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert len(data["items"]) == 1
            assert data["items"][0]["category_id"] == "cat1"
    
    @unittest_run_loop
    async def test_get_progress_summary_success(self):
        """✅ ПОЗИТИВНЫЙ: успешное получение сводки прогресса"""
        test_user_id = 12345
        test_summary = {
            "total_categories": 5,
            "active_categories": 3,
            "completed_categories": 1,
            "overall_progress": 0.6,
            "total_benefit": 150.0,
            "next_milestone": {"category": "cat2", "progress_needed": 0.2}
        }
        
        with patch('functions.progress.get_progress_summary') as mock_summary:
            mock_summary.return_value = test_summary
            
            resp = await self.client.request(
                "GET",
                "/api/v1/progress/summary",
                headers={"X-User-ID": str(test_user_id)}
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert data["total_categories"] == 5
            assert data["overall_progress"] == 0.6
            assert data["total_benefit"] == 150.0
    
    @unittest_run_loop
    async def test_get_progress_summary_empty(self):
        """✅ ПОЗИТИВНЫЙ: пустая сводка прогресса"""
        test_user_id = 12345
        
        with patch('functions.progress.get_progress_summary') as mock_summary:
            mock_summary.return_value = None
            
            resp = await self.client.request(
                "GET",
                "/api/v1/progress/summary",
                headers={"X-User-ID": str(test_user_id)}
            )
            
            assert resp.status == 404
            data = await resp.json()
            assert data["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_offers_progress_database_error():
    """❌ НЕГАТИВНЫЙ: ошибка базы данных"""
    from server import create_app
    
    app = await create_app()
    
    with patch('functions.offers.run_offers') as mock_offers:
        mock_offers.side_effect = Exception("Database connection failed")
        
        async with app.test_client() as client:
            resp = await client.post(
                "/api/v1/offers/run",
                headers={
                    "Content-Type": "application/json",
                    "X-User-ID": "12345"
                },
                data=json.dumps({"categories": ["cat1"]})
            )
            
            assert resp.status == 500


@pytest.mark.asyncio
async def test_progress_edge_cases():
    """⚠️ ГРАНИЧНЫЙ: edge cases для прогресса"""
    from server import create_app
    
    app = await create_app()
    
    async with app.test_client() as client:
        # Тест с user_id = 0
        resp = await client.get(
            "/api/v1/progress",
            headers={"X-User-ID": "0"}
        )
        assert resp.status == 422
        
        # Тест с отрицательным user_id
        resp = await client.get(
            "/api/v1/progress",
            headers={"X-User-ID": "-1"}
        )
        assert resp.status == 422
