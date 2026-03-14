"""
Интеграционные тесты для Audit API
"""

import pytest
from aiohttp import web
from aiohttp.test import AioHTTPTestCase, unittest_run_loop
from unittest.mock import patch
import json


class TestAuditAPI(AioHTTPTestCase):
    """Интеграционные тесты для Audit API"""
    
    async def get_application(self):
        """Создание тестового приложения"""
        from server import create_app
        return await create_app()
    
    @unittest_run_loop
    async def test_get_audit_success(self):
        """✅ ПОЗИТИВНЫЙ: успешное получение аудита"""
        test_records = [
            {
                "audit_id": "audit1",
                "admin_id": 1,
                "entity_type": "category",
                "entity_id": "cat123",
                "action": "create",
                "old_values": None,
                "new_values": {"name": "Test Category"},
                "created_at": "2024-01-01T10:00:00Z"
            },
            {
                "audit_id": "audit2",
                "admin_id": 1,
                "entity_type": "category",
                "entity_id": "cat456",
                "action": "update",
                "old_values": {"name": "Old Name"},
                "new_values": {"name": "New Name"},
                "created_at": "2024-01-01T11:00:00Z"
            }
        ]
        
        with patch('functions.audit.get_audit_records') as mock_audit:
            mock_audit.return_value = test_records
            
            resp = await self.client.request(
                "GET",
                "/api/v1/admin/audit",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert len(data["items"]) == 2
            assert data["total"] == 2
            assert data["items"][0]["action"] == "create"
            assert data["items"][1]["action"] == "update"
    
    @unittest_run_loop
    async def test_get_audit_with_filters(self):
        """✅ ПОЗИТИВНЫЙ: получение аудита с фильтрами"""
        test_records = [
            {
                "audit_id": "audit1",
                "admin_id": 1,
                "entity_type": "category",
                "entity_id": "cat123",
                "action": "create",
                "created_at": "2024-01-01T10:00:00Z"
            }
        ]
        
        with patch('functions.audit.get_audit_records') as mock_audit:
            mock_audit.return_value = test_records
            
            resp = await self.client.request(
                "GET",
                "/api/v1/admin/audit?entity_type=category&limit=5&offset=10",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert len(data["items"]) == 1
            mock_audit.assert_called_once_with(limit=5, offset=10, entity_type="category")
    
    @unittest_run_loop
    async def test_get_audit_empty(self):
        """✅ ПОЗИТИВНЫЙ: пустой список аудита"""
        with patch('functions.audit.get_audit_records') as mock_audit:
            mock_audit.return_value = []
            
            resp = await self.client.request(
                "GET",
                "/api/v1/admin/audit",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert len(data["items"]) == 0
            assert data["total"] == 0
    
    @unittest_run_loop
    async def test_get_audit_unauthorized(self):
        """❌ НЕГАТИВНЫЙ: нет токена авторизации"""
        resp = await self.client.request("GET", "/api/v1/admin/audit")
        
        assert resp.status == 401
        data = await resp.json()
        assert data["code"] == "UNAUTHORIZED"
    
    @unittest_run_loop
    async def test_get_audit_invalid_token(self):
        """❌ НЕГАТИВНЫЙ: невалидный токен"""
        resp = await self.client.request(
            "GET",
            "/api/v1/admin/audit",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert resp.status == 401
        data = await resp.json()
        assert data["code"] == "UNAUTHORIZED"
    
    @unittest_run_loop
    async def test_get_audit_invalid_limit(self):
        """❌ НЕГАТИВНЫЙ: невалидный параметр limit"""
        resp = await self.client.request(
            "GET",
            "/api/v1/admin/audit?limit=501",
            headers={"Authorization": "Bearer admin_token"}
        )
        
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"
    
    @unittest_run_loop
    async def test_get_audit_negative_offset(self):
        """❌ НЕГАТИВНЫЙ: отрицательный offset"""
        resp = await self.client.request(
            "GET",
            "/api/v1/admin/audit?offset=-1",
            headers={"Authorization": "Bearer admin_token"}
        )
        
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"
    
    @unittest_run_loop
    async def test_get_audit_invalid_entity_type(self):
        """❌ НЕГАТИВНЫЙ: невалидный entity_type"""
        resp = await self.client.request(
            "GET",
            "/api/v1/admin/audit?entity_type=invalid_entity",
            headers={"Authorization": "Bearer admin_token"}
        )
        
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"
    
    @unittest_run_loop
    async def test_get_audit_with_admin_id_filter(self):
        """✅ ПОЗИТИВНЫЙ: фильтрация по admin_id"""
        test_records = [
            {
                "audit_id": "audit1",
                "admin_id": 1,
                "entity_type": "category",
                "action": "create",
                "created_at": "2024-01-01T10:00:00Z"
            }
        ]
        
        with patch('functions.audit.get_audit_records') as mock_audit:
            mock_audit.return_value = test_records
            
            resp = await self.client.request(
                "GET",
                "/api/v1/admin/audit?admin_id=1",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert len(data["items"]) == 1
            assert data["items"][0]["admin_id"] == 1
    
    @unittest_run_loop
    async def test_get_audit_with_date_filter(self):
        """✅ ПОЗИТИВНЫЙ: фильтрация по дате"""
        test_records = [
            {
                "audit_id": "audit1",
                "admin_id": 1,
                "entity_type": "category",
                "action": "create",
                "created_at": "2024-01-01T10:00:00Z"
            }
        ]
        
        with patch('functions.audit.get_audit_records') as mock_audit:
            mock_audit.return_value = test_records
            
            resp = await self.client.request(
                "GET",
                "/api/v1/admin/audit?date_from=2024-01-01&date_to=2024-01-31",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert len(data["items"]) == 1
    
    @unittest_run_loop
    async def test_get_audit_with_action_filter(self):
        """✅ ПОЗИТИВНЫЙ: фильтрация по действию"""
        test_records = [
            {
                "audit_id": "audit1",
                "admin_id": 1,
                "entity_type": "category",
                "entity_id": "cat123",
                "action": "create",
                "created_at": "2024-01-01T10:00:00Z"
            }
        ]
        
        with patch('functions.audit.get_audit_records') as mock_audit:
            mock_audit.return_value = test_records
            
            resp = await self.client.request(
                "GET",
                "/api/v1/admin/audit?action=create",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert len(data["items"]) == 1
            assert data["items"][0]["action"] == "create"
    
    @unittest_run_loop
    async def test_get_audit_multiple_filters(self):
        """✅ ПОЗИТИВНЫЙ: множественные фильтры"""
        test_records = [
            {
                "audit_id": "audit1",
                "admin_id": 1,
                "entity_type": "category",
                "entity_id": "cat123",
                "action": "create",
                "created_at": "2024-01-01T10:00:00Z"
            }
        ]
        
        with patch('functions.audit.get_audit_records') as mock_audit:
            mock_audit.return_value = test_records
            
            resp = await self.client.request(
                "GET",
                "/api/v1/admin/audit?entity_type=category&action=create&admin_id=1",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert len(data["items"]) == 1
    
    @unittest_run_loop
    async def test_get_audit_database_error(self):
        """❌ НЕГАТИВНЫЙ: ошибка базы данных"""
        with patch('functions.audit.get_audit_records') as mock_audit:
            mock_audit.side_effect = Exception("Database connection failed")
            
            resp = await self.client.request(
                "GET",
                "/api/v1/admin/audit",
                headers={"Authorization": "Bearer admin_token"}
            )
            
            assert resp.status == 500


@pytest.mark.asyncio
async def test_audit_pagination_edge_cases():
    """⚠️ ГРАНИЧНЫЙ: пагинация edge cases"""
    from server import create_app
    
    app = await create_app()
    
    with patch('functions.audit.get_audit_records') as mock_audit:
        mock_audit.return_value = []
        
        async with app.test_client() as client:
            # Тест с limit = 0
            resp = await client.get(
                "/api/v1/admin/audit?limit=0",
                headers={"Authorization": "Bearer admin_token"}
            )
            assert resp.status == 422
            
            # Тест с очень большим offset
            resp = await client.get(
                "/api/v1/admin/audit?offset=999999",
                headers={"Authorization": "Bearer admin_token"}
            )
            assert resp.status == 200  # Должен вернуть пустой результат


@pytest.mark.asyncio
async def test_audit_filter_validation():
    """⚠️ ГРАНИЧНЫЙ: валидация фильтров"""
    from server import create_app
    
    app = await create_app()
    
    async with app.test_client() as client:
        # Невалидная дата
        resp = await client.get(
            "/api/v1/admin/audit?date_from=invalid-date",
            headers={"Authorization": "Bearer admin_token"}
        )
        assert resp.status == 422
        
        # Невалидный admin_id (не число)
        resp = await client.get(
            "/api/v1/admin/audit?admin_id=not-a-number",
            headers={"Authorization": "Bearer admin_token"}
        )
        assert resp.status == 422
