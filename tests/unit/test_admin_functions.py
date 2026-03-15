"""
Юнит-тесты для функций администрирования
"""

import pytest
from unittest.mock import patch, AsyncMock
from functions import admin_users as auth_fns
from functions import audit as audit_fns


class TestAdminAuthFunctions:
    @pytest.mark.asyncio
    async def test_create_admin_success(self):
        test_admin = {"login": "newadmin", "password": "password123"}

        with patch.object(
            auth_fns,
            "get_admin_by_login",
            new=AsyncMock(return_value={"admin_id": 5, "login": "newadmin", "approved": False}),
        ):
            with patch.object(auth_fns, "Database") as MockDB:
                mock_conn = AsyncMock()
                mock_conn.execute = AsyncMock(return_value=None)
                MockDB.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
                MockDB.return_value.__aexit__ = AsyncMock(return_value=None)

                result = await auth_fns.create_admin(test_admin["login"], test_admin["password"])
                assert result is not None
                assert result["admin_id"] == 5

    @pytest.mark.asyncio
    async def test_authenticate_admin_success(self):
        with patch.object(auth_fns, "Database") as MockDB:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock(
                return_value={
                    "admin_id": 1,
                    "login": "admin",
                    "approved": True,
                    "main_admin": False,
                }
            )
            MockDB.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            MockDB.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await auth_fns.authenticate_admin("admin", "password123")
            assert result["admin_id"] == 1

    @pytest.mark.asyncio
    async def test_set_admin_approved_success(self):
        with patch.object(
            auth_fns,
            "get_admin_by_id",
            new=AsyncMock(
                return_value={
                    "admin_id": 2,
                    "login": "admin2",
                    "main_admin": False,
                    "approved": True,
                }
            ),
        ):
            with patch.object(auth_fns, "Database") as MockDB:
                mock_conn = AsyncMock()
                mock_conn.execute = AsyncMock(return_value=None)
                MockDB.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
                MockDB.return_value.__aexit__ = AsyncMock(return_value=None)

                result = await auth_fns.set_admin_approved(2)
                assert result is not None
                assert result["approved"] is True


class TestAuditFunctions:
    @pytest.mark.asyncio
    async def test_write_audit_success(self):
        with patch.object(audit_fns, "Database") as MockDB:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock(return_value=None)
            MockDB.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            MockDB.return_value.__aexit__ = AsyncMock(return_value=None)

            await audit_fns.write_audit(
                entity_type="category",
                entity_id="cat123",
                action="create",
                actor="admin",
                details={"name": "Test Category"},
            )
            mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_audit_success(self):
        test_rows = [
            {
                "id": 1,
                "entity_type": "category",
                "entity_id": "cat123",
                "action": "create",
                "actor": "admin",
                "created_at": "2024-01-01T10:00:00Z",
            }
        ]

        with patch.object(audit_fns, "Database") as MockDB:
            mock_conn = AsyncMock()
            mock_conn.execute_all = AsyncMock(return_value=test_rows)
            MockDB.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            MockDB.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await audit_fns.list_audit(
                entity_type=None,
                entity_id=None,
                action=None,
                limit=10,
            )
            assert len(result) == 1
            assert result[0]["action"] == "create"
