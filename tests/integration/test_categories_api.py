import pytest
from unittest.mock import patch
import json


async def test_get_categories_success(aiohttp_client, app):
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

    with patch('functions.categories.list_categories') as mock_get:
        mock_get.return_value = (test_categories, 2)

        client = await aiohttp_client(app)
        resp = await client.request(
            "GET",
            "/api/v1/admin/categories",
            headers={"Authorization": "Bearer admin_token"}
        )

        assert resp.status == 200
        data = await resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2


async def test_get_categories_with_pagination(aiohttp_client, app):
    """Тест: получение категорий с пагинацией"""
    with patch('functions.categories.list_categories') as mock_get:
        mock_get.return_value = ([], 0)

        client = await aiohttp_client(app)
        resp = await client.request(
            "GET",
            "/api/v1/admin/categories?limit=5&offset=10",
            headers={"Authorization": "Bearer admin_token"}
        )

        assert resp.status == 200
        mock_get.assert_called_once_with(10, 5)  # offset, limit


async def test_get_categories_invalid_limit(aiohttp_client, app):
    """Тест: невалидный параметр limit"""
    client = await aiohttp_client(app)
    resp = await client.request(
        "GET",
        "/api/v1/admin/categories?limit=501",
        headers={"Authorization": "Bearer admin_token"}
    )

    assert resp.status == 422
    data = await resp.json()
    assert data["code"] == "VALIDATION_FAILED"


async def test_get_categories_negative_offset(aiohttp_client, app):
    """Тест: отрицательный offset"""
    client = await aiohttp_client(app)
    resp = await client.request(
        "GET",
        "/api/v1/admin/categories?offset=-1",
        headers={"Authorization": "Bearer admin_token"}
    )

    assert resp.status == 422
    data = await resp.json()
    assert data["code"] == "VALIDATION_FAILED"


async def test_create_category_success(aiohttp_client, app):
    """Тест: успешное создание категории"""
    category_data = {
        "name": "Test Category",
        "subtitle": "Test subtitle",
        "budget_amount": 100000,
        "rate_min": 0,
        "rate_max": 100
    }

    with patch('functions.categories.create_category') as mock_create:
        mock_create.return_value = {"category_id": "cat123", "name": "Test Category"}

        client = await aiohttp_client(app)
        resp = await client.request(
            "POST",
            "/api/v1/admin/categories",
            headers={"Content-Type": "application/json", "Authorization": "Bearer admin_token"},
            data=json.dumps(category_data)
        )

        assert resp.status == 201
        data = await resp.json()
        assert data["category_id"] == "cat123"


async def test_create_category_missing_fields(aiohttp_client, app):
    """Тест: создание категории с отсутствующими полями"""
    category_data = {"name": "Test Category"}

    client = await aiohttp_client(app)
    resp = await client.request(
        "POST",
        "/api/v1/admin/categories",
        headers={"Content-Type": "application/json"},
        data=json.dumps(category_data)
    )

    assert resp.status == 422
    data = await resp.json()
    assert data["code"] == "VALIDATION_FAILED"


async def test_create_category_negative_budget(aiohttp_client, app):
    """Тест: создание категории с отрицательным бюджетом"""
    category_data = {
        "name": "Test Category",
        "subtitle": "Test subtitle",
        "budget_amount": -1000,
        "rate_min": 0,
        "rate_max": 100
    }

    client = await aiohttp_client(app)
    resp = await client.request(
        "POST",
        "/api/v1/admin/categories",
        headers={"Content-Type": "application/json"},
        data=json.dumps(category_data)
    )

    assert resp.status == 422


async def test_get_category_success(aiohttp_client, app):
    """Тест: успешное получение категории по id"""
    test_category = {
        "category_id": "cat1",
        "name": "Category 1",
        "subtitle": "Subtitle 1",
        "budget_amount": 100000,
        "status": "active"
    }

    with patch('functions.categories.get_category') as mock_get:
        mock_get.return_value = test_category

        client = await aiohttp_client(app)
        resp = await client.request(
            "GET",
            "/api/v1/admin/categories/cat1",
            headers={"Authorization": "Bearer admin_token"}
        )

        assert resp.status == 200
        data = await resp.json()
        assert data["category_id"] == "cat1"
        assert data["name"] == "Category 1"


async def test_get_category_not_found(aiohttp_client, app):
    """Тест: категория не найдена"""
    with patch('functions.categories.get_category') as mock_get:
        mock_get.return_value = None

        client = await aiohttp_client(app)
        resp = await client.request(
            "GET",
            "/api/v1/admin/categories/nonexistent",
            headers={"Authorization": "Bearer admin_token"}
        )

        assert resp.status == 404
        data = await resp.json()
        assert data["code"] == "NOT_FOUND"


async def test_get_category_invalid_uuid(aiohttp_client, app):
    """Тест: невалидный UUID категории"""
    client = await aiohttp_client(app)
    resp = await client.request(
        "GET",
        "/api/v1/admin/categories/invalid-uuid",
        headers={"Authorization": "Bearer admin_token"}
    )

    assert resp.status == 422
    data = await resp.json()
    assert data["code"] == "VALIDATION_FAILED"


async def test_update_category_success(aiohttp_client, app):
    """Тест: успешное обновление категории"""
    update_data = {
        "category_id": "cat1",
        "name": "Updated Category",
        "budget_amount": 150000
    }

    with patch('functions.categories.update_category') as mock_update:
        mock_update.return_value = True

        client = await aiohttp_client(app)
        resp = await client.request(
            "PATCH",
            "/api/v1/admin/categories/cat1",
            headers={"Content-Type": "application/json", "Authorization": "Bearer admin_token"},
            data=json.dumps(update_data)
        )

        assert resp.status == 200


async def test_update_category_not_found(aiohttp_client, app):
    """Тест: категория для обновления не найдена"""
    update_data = {"category_id": "nonexistent", "name": "Updated Category"}

    with patch('functions.categories.update_category') as mock_update:
        mock_update.return_value = False

        client = await aiohttp_client(app)
        resp = await client.request(
            "PATCH",
            "/api/v1/admin/categories/nonexistent",
            headers={"Content-Type": "application/json", "Authorization": "Bearer admin_token"},
            data=json.dumps(update_data)
        )

        assert resp.status == 404


async def test_create_category_rule_success(aiohttp_client, app):
    """Тест: успешное создание правила для категории"""
    rule_data = {
        "category_id": "cat1",
        "min_age": 18,
        "max_age": 65,
        "gender": "other",
        "income": 50000
    }

    with patch('functions.categories.get_category') as mock_get_cat, \
         patch('functions.rules.create_rule') as mock_create, \
         patch('functions.categories.update_category') as mock_update:
        mock_get_cat.return_value = {"category_id": "cat1"}
        mock_create.return_value = {"rule_id": "rule123"}
        mock_update.return_value = {"category_id": "cat1", "rule_id": "rule123"}

        client = await aiohttp_client(app)
        resp = await client.request(
            "POST",
            "/api/v1/admin/categories/cat1/rule",
            headers={"Content-Type": "application/json", "Authorization": "Bearer admin_token"},
            data=json.dumps(rule_data)
        )

        assert resp.status == 201
        data = await resp.json()
        assert data["rule_id"] == "rule123"
