from unittest.mock import patch


async def test_get_audit_success(aiohttp_client, app):
    """✅ ПОЗИТИВНЫЙ: успешное получение аудита"""
    test_records = [
        {
            "id": 1,
            "admin_id": 1,
            "entity_type": "category",
            "entity_id": "cat123",
            "action": "create",
            "actor": "admin",
            "created_at": "2024-01-01T10:00:00Z",
        },
        {
            "id": 2,
            "entity_type": "category",
            "entity_id": "cat456",
            "action": "update",
            "actor": "admin",
            "created_at": "2024-01-01T11:00:00Z",
        },
    ]

    with patch("functions.audit.list_audit") as mock_audit:
        mock_audit.return_value = test_records

        client = await aiohttp_client(app)
        resp = await client.request("GET", "/api/v1/admin/audit", headers={"Authorization": "Bearer admin_token"})

        assert resp.status == 200
        data = await resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2
        assert data["items"][0]["action"] == "create"
        assert data["items"][1]["action"] == "update"


async def test_get_audit_with_filters(aiohttp_client, app):
    """✅ ПОЗИТИВНЫЙ: получение аудита с фильтрами"""
    test_records = [
        {
            "id": 1,
            "entity_type": "category",
            "entity_id": "cat123",
            "action": "create",
            "actor": "admin",
            "created_at": "2024-01-01T10:00:00Z",
        }
    ]

    with patch("functions.audit.list_audit") as mock_audit:
        mock_audit.return_value = test_records

        client = await aiohttp_client(app)
        resp = await client.request(
            "GET", "/api/v1/admin/audit?entity_type=category&limit=5", headers={"Authorization": "Bearer admin_token"}
        )

        assert resp.status == 200
        data = await resp.json()
        assert len(data["items"]) == 1
        mock_audit.assert_called_once()
        call_args = mock_audit.call_args[0]
        assert call_args[0] == "category"  # entity_type
        assert call_args[3] == 5  # limit


async def test_get_audit_empty(aiohttp_client, app):
    """✅ ПОЗИТИВНЫЙ: пустой список аудита"""
    with patch("functions.audit.list_audit") as mock_audit:
        mock_audit.return_value = []

        client = await aiohttp_client(app)
        resp = await client.request("GET", "/api/v1/admin/audit", headers={"Authorization": "Bearer admin_token"})

        assert resp.status == 200
        data = await resp.json()
        assert len(data["items"]) == 0
        assert data["total"] == 0


async def test_get_audit_unauthorized(aiohttp_client, app):
    """❌ НЕГАТИВНЫЙ: нет токена авторизации"""
    client = await aiohttp_client(app)
    resp = await client.request("GET", "/api/v1/admin/audit")

    assert resp.status == 401
    data = await resp.json()
    assert data["code"] == "UNAUTHORIZED"


async def test_get_audit_invalid_token(aiohttp_client, app):
    """❌ НЕГАТИВНЫЙ: невалидный токен"""
    client = await aiohttp_client(app)
    resp = await client.request("GET", "/api/v1/admin/audit", headers={"Authorization": "Bearer invalid_token"})

    assert resp.status == 401
    data = await resp.json()
    assert data["code"] == "UNAUTHORIZED"


async def test_get_audit_invalid_limit(aiohttp_client, app):
    """❌ НЕГАТИВНЫЙ: невалидный параметр limit"""
    client = await aiohttp_client(app)
    resp = await client.request("GET", "/api/v1/admin/audit?limit=501", headers={"Authorization": "Bearer admin_token"})

    assert resp.status == 422
    data = await resp.json()
    assert data["code"] == "VALIDATION_FAILED"


async def test_get_audit_negative_offset(aiohttp_client, app):
    """❌ НЕГАТИВНЫЙ: отрицательный offset — в API нет offset, проверяем что limit проверяется"""
    client = await aiohttp_client(app)
    resp = await client.request("GET", "/api/v1/admin/audit?limit=0", headers={"Authorization": "Bearer admin_token"})

    assert resp.status == 422
    data = await resp.json()
    assert data["code"] == "VALIDATION_FAILED"


async def test_get_audit_database_error(aiohttp_client, app):
    """❌ НЕГАТИВНЫЙ: ошибка базы данных"""
    with patch("functions.audit.list_audit") as mock_audit:
        mock_audit.side_effect = Exception("Database connection failed")

        client = await aiohttp_client(app)
        resp = await client.request("GET", "/api/v1/admin/audit", headers={"Authorization": "Bearer admin_token"})

        assert resp.status == 500


async def test_audit_pagination_edge_cases(aiohttp_client, app):
    """⚠️ ГРАНИЧНЫЙ: пагинация edge cases"""
    with patch("functions.audit.list_audit") as mock_audit:
        mock_audit.return_value = []

        client = await aiohttp_client(app)
        resp = await client.get("/api/v1/admin/audit?limit=0", headers={"Authorization": "Bearer admin_token"})
        assert resp.status == 422
