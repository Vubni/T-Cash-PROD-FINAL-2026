from unittest.mock import patch

import core


_CATEGORY_ID = "00000000-0000-0000-0000-000000000001"


def _admin_headers(token: str | None = None) -> dict[str, str]:
    """Заголовок Authorization с JWT админа (или переданным токеном)."""
    if token is None:
        payload = {"admin_id": 1, "scope": core.ADMIN_SCOPE}
        token = core.create_token(payload)
    return {"Authorization": f"Bearer {token}"}


async def test_get_audit_success(aiohttp_client, app):
    """✅ Позитивный: успешное получение аудита по категории."""
    test_records = [
        {
            "id": 1,
            "entity_type": "category",
            "entity_id": _CATEGORY_ID,
            "action": "create",
            "actor": "admin",
            "created_at": "2024-01-01T10:00:00Z",
        }
    ]

    with patch("functions.audit.list_audit") as mock_audit:
        mock_audit.return_value = test_records

        client = await aiohttp_client(app)
        resp = await client.get(
            f"/api/v1/admin/categories/{_CATEGORY_ID}/audit",
            headers=_admin_headers(),
        )

        assert resp.status == 200
        data = await resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["action"] == "create"

        mock_audit.assert_called_once()
        _, kwargs = mock_audit.call_args
        assert kwargs["entity_type"] == "category"
        assert kwargs["entity_id"] == _CATEGORY_ID
        assert kwargs["limit"] == 50  # лимит по умолчанию


async def test_get_audit_with_limit(aiohttp_client, app):
    """✅ Позитивный: аудит по категории с кастомным limit."""
    test_records = []

    with patch("functions.audit.list_audit") as mock_audit:
        mock_audit.return_value = test_records

        client = await aiohttp_client(app)
        resp = await client.get(
            f"/api/v1/admin/categories/{_CATEGORY_ID}/audit?limit=5",
            headers=_admin_headers(),
        )

        assert resp.status == 200
        data = await resp.json()
        assert data["total"] == 0
        mock_audit.assert_called_once()
        _, kwargs = mock_audit.call_args
        assert kwargs["entity_type"] == "category"
        assert kwargs["entity_id"] == _CATEGORY_ID
        assert kwargs["limit"] == 5  # limit передан внутрь функции


async def test_get_audit_invalid_limit(aiohttp_client, app):
    """❌ Негативный: limit=0 и limit>MAX дают 422 VALIDATION_FAILED."""
    client = await aiohttp_client(app)

    resp = await client.get(
        f"/api/v1/admin/categories/{_CATEGORY_ID}/audit?limit=0",
        headers=_admin_headers(),
    )
    assert resp.status == 422
    body = await resp.json()
    assert body["code"] == "VALIDATION_FAILED"

    resp = await client.get(
        f"/api/v1/admin/categories/{_CATEGORY_ID}/audit?limit=501",
        headers=_admin_headers(),
    )
    assert resp.status == 422
    body = await resp.json()
    assert body["code"] == "VALIDATION_FAILED"


async def test_get_audit_unauthorized(aiohttp_client, app):
    """❌ Негативный: без токена возвращается 401 UNAUTHORIZED."""
    client = await aiohttp_client(app)
    resp = await client.get(f"/api/v1/admin/categories/{_CATEGORY_ID}/audit")
    assert resp.status == 401
    body = await resp.json()
    assert body["code"] == "UNAUTHORIZED"


async def test_get_audit_invalid_token(aiohttp_client, app):
    """❌ Негативный: невалидный токен возвращает 401 UNAUTHORIZED."""
    client = await aiohttp_client(app)
    resp = await client.get(
        f"/api/v1/admin/categories/{_CATEGORY_ID}/audit",
        headers=_admin_headers(token="invalid_token"),
    )
    assert resp.status == 401
    body = await resp.json()
    assert body["code"] == "UNAUTHORIZED"


async def test_get_audit_database_error(aiohttp_client, app):
    """❌ Негативный: ошибка базы данных даёт 500 INTERNAL_ERROR."""
    with patch("functions.audit.list_audit") as mock_audit:
        mock_audit.side_effect = Exception("Database connection failed")

        client = await aiohttp_client(app)
        resp = await client.get(
            f"/api/v1/admin/categories/{_CATEGORY_ID}/audit",
            headers=_admin_headers(),
        )

        assert resp.status == 500
        body = await resp.json()
        assert body["code"] == "INTERNAL_ERROR"

