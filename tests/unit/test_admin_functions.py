"""
Юнит-тесты для функций администрирования
"""

import pytest
from unittest.mock import patch
from functions import admin_auth as auth_fns
from functions import audit as audit_fns


class TestAdminAuthFunctions:
    
    @pytest.mark.asyncio
    async def test_register_admin_success(self):
        test_admin = {
            "login": "newadmin",
            "password": "password123"
        }
        
        with patch('functions.admin_auth.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetchval.return_value = 5
            result = await auth_fns.register_admin(test_admin["login"], test_admin["password"])
            assert result == 5
    
    @pytest.mark.asyncio
    async def test_verify_admin_success(self):
        test_password = "password123"
        hashed_password = "$2b$12$hash"
        
        with patch('functions.admin_auth.get_connection') as mock_conn, \
             patch('functions.admin_auth.check_password_hash') as mock_check:
            
            mock_conn.return_value.__aenter__.return_value.fetchrow.return_value = {
                "admin_id": 1,
                "login": "admin",
                "password_hash": hashed_password,
                "approved": True
            }
            mock_check.return_value = True
            
            result = await auth_fns.verify_admin("admin", test_password)
            assert result["admin_id"] == 1
    
    @pytest.mark.asyncio
    async def test_approve_admin_success(self):
        with patch('functions.admin_auth.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetchval.return_value = 1
            result = await auth_fns.approve_admin(2)
            assert result is True


class TestAuditFunctions:
    
    @pytest.mark.asyncio
    async def test_create_audit_record_success(self):
        audit_data = {
            "admin_id": 1,
            "entity_type": "category",
            "entity_id": "cat123",
            "action": "create",
            "old_values": None,
            "new_values": {"name": "Test Category"}
        }
        
        with patch('functions.audit.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetchval.return_value = "audit123"
            result = await audit_fns.create_audit_record(
                audit_data["admin_id"],
                audit_data["entity_type"],
                audit_data["entity_id"],
                audit_data["action"],
                audit_data["old_values"],
                audit_data["new_values"]
            )
            assert result == "audit123"
    
    @pytest.mark.asyncio
    async def test_get_audit_records_success(self):
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
        
        with patch('functions.audit.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetch.return_value = test_records
            result = await audit_fns.get_audit_records(limit=10, offset=0)
            assert len(result) == 1
            assert result[0]["action"] == "create"
