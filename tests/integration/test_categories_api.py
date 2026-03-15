from unittest.mock import patch
import json

# Валидные UUID для путей (API валидирует category_id как UUID)
CAT_ID = "11111111-1111-1111-1111-111111111111"
NOT_FOUND_CAT_ID = "00000000-0000-0000-0000-000000000000"


async def test_get_categories_success(aiohttp_client, app):
    """Тест: успешное получение списка категорий"""
    test_categories = [
        {
            "category_id": "cat1",
            "name": "Category 1",
            "subtitle": "Subtitle 1",
            "budget_amount": 100000,
            "status": "active",
        },
        {
            "category_id": "cat2",
            "name": "Category 2",
            "subtitle": "Subtitle 2",
            "budget_amount": 200000,
            "status": "active",
        },
    ]

    with patch("functions.categories.list_categories") as mock_get:
        mock_get.return_value = (test_categories, 2)

        async with aiohttp_client(app) as client:
            resp = await client.request("GET", "/api/v1/admin/categories", headers={"Authorization": "Bearer admin_token"})
            assert resp.status == 200
            data = await resp.json()
            assert len(data["items"]) == 2
            assert data["total"] == 2


async def test_get_categories_with_pagination(aiohttp_client, app):
    """Тест: получение категорий с пагинацией"""
    with patch("functions.categories.list_categories") as mock_get:
        mock_get.return_value = ([], 0)

        async with aiohttp_client(app) as client:
            resp = await client.request(
                "GET", "/api/v1/admin/categories?limit=5&offset=10", headers={"Authorization": "Bearer admin_token"}
            )
            assert resp.status == 200
        mock_get.assert_called_once_with(10, 5)  # offset, limit


async def test_get_categories_invalid_limit(aiohttp_client, app):
    """Тест: невалидный параметр limit"""
    async with aiohttp_client(app) as client:
        resp = await client.request(
            "GET", "/api/v1/admin/categories?limit=501", headers={"Authorization": "Bearer admin_token"}
        )
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"


async def test_get_categories_negative_offset(aiohttp_client, app):
    """Тест: отрицательный offset"""
    async with aiohttp_client(app) as client:
        resp = await client.request(
            "GET", "/api/v1/admin/categories?offset=-1", headers={"Authorization": "Bearer admin_token"}
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
        "rate_max": 100,
    }

    with patch("functions.categories.create_category") as mock_create:
        mock_create.return_value = {"category_id": "cat123", "name": "Test Category"}

        async with aiohttp_client(app) as client:
            resp = await client.request(
                "POST",
                "/api/v1/admin/categories",
                headers={"Content-Type": "application/json", "Authorization": "Bearer admin_token"},
                data=json.dumps(category_data),
            )
            assert resp.status == 201
            data = await resp.json()
            assert data["category_id"] == "cat123"


async def test_create_category_missing_fields(aiohttp_client, app):
    """Тест: создание категории с отсутствующими полями"""
    category_data = {"name": "Test Category"}

    async with aiohttp_client(app) as client:
        resp = await client.request(
            "POST", "/api/v1/admin/categories", headers={"Content-Type": "application/json"}, data=json.dumps(category_data)
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
        "rate_max": 100,
    }

    async with aiohttp_client(app) as client:
        resp = await client.request(
            "POST", "/api/v1/admin/categories", headers={"Content-Type": "application/json"}, data=json.dumps(category_data)
        )

    assert resp.status == 422


async def test_get_category_success(aiohttp_client, app):
    """Тест: успешное получение категории по id"""
    test_category = {
        "category_id": CAT_ID,
        "name": "Category 1",
        "subtitle": "Subtitle 1",
        "budget_amount": 100000,
        "status": "active",
    }

    with patch("functions.categories.get_category") as mock_get:
        mock_get.return_value = test_category

        async with aiohttp_client(app) as client:
            resp = await client.request(
                "GET", f"/api/v1/admin/categories/{CAT_ID}", headers={"Authorization": "Bearer admin_token"}
            )
            assert resp.status == 200
            data = await resp.json()
            assert data["category_id"] == CAT_ID
            assert data["name"] == "Category 1"


async def test_get_category_not_found(aiohttp_client, app):
    """Тест: категория не найдена"""
    with patch("functions.categories.get_category") as mock_get:
        mock_get.return_value = None

        async with aiohttp_client(app) as client:
            resp = await client.request(
                "GET", f"/api/v1/admin/categories/{NOT_FOUND_CAT_ID}", headers={"Authorization": "Bearer admin_token"}
            )
            assert resp.status == 404
            data = await resp.json()
            assert data["code"] == "NOT_FOUND"


async def test_get_category_invalid_uuid(aiohttp_client, app):
    """Тест: невалидный UUID категории"""
    async with aiohttp_client(app) as client:
        resp = await client.request(
            "GET", "/api/v1/admin/categories/invalid-uuid", headers={"Authorization": "Bearer admin_token"}
        )
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"


async def test_update_category_success(aiohttp_client, app):
    """Тест: успешное обновление категории"""
    update_data = {"category_id": CAT_ID, "name": "Updated Category", "budget_amount": 150000}

    with patch("functions.categories.update_category") as mock_update:
        mock_update.return_value = {"category_id": CAT_ID, "name": "Updated Category"}

        async with aiohttp_client(app) as client:
            resp = await client.request(
                "PATCH",
                f"/api/v1/admin/categories/{CAT_ID}",
                headers={"Content-Type": "application/json", "Authorization": "Bearer admin_token"},
                data=json.dumps(update_data),
            )

        assert resp.status == 200


async def test_update_category_not_found(aiohttp_client, app):
    """Тест: категория для обновления не найдена"""
    update_data = {"category_id": NOT_FOUND_CAT_ID, "name": "Updated Category"}

    with patch("functions.categories.update_category") as mock_update:
        mock_update.return_value = None  # хендлер возвращает 404 при None

        async with aiohttp_client(app) as client:
            resp = await client.request(
                "PATCH",
                f"/api/v1/admin/categories/{NOT_FOUND_CAT_ID}",
                headers={"Content-Type": "application/json", "Authorization": "Bearer admin_token"},
                data=json.dumps(update_data),
            )

        assert resp.status == 404


async def test_create_category_rule_success(aiohttp_client, app):
    """Тест: успешное создание правила для категории"""
    rule_data = {"category_id": CAT_ID, "min_age": 18, "max_age": 65, "gender": "other", "income": 50000}

    with (
        patch("functions.categories.get_category") as mock_get_cat,
        patch("functions.rules.create_rule") as mock_create,
        patch("functions.categories.update_category") as mock_update,
    ):
        mock_get_cat.return_value = {"category_id": CAT_ID}
        mock_create.return_value = {"rule_id": "rule123"}
        mock_update.return_value = {"category_id": CAT_ID, "rule_id": "rule123"}

        async with aiohttp_client(app) as client:
            resp = await client.request(
                "POST",
                f"/api/v1/admin/categories/{CAT_ID}/rule",
                headers={"Content-Type": "application/json", "Authorization": "Bearer admin_token"},
                data=json.dumps(rule_data),
            )
            assert resp.status == 201
            data = await resp.json()
            assert data["rule_id"] == "rule123"


# --- Тесты статусов категорий (running, paused, archived) ---


async def test_get_category_returns_status(aiohttp_client, app):
    """Тест: ответ get_category содержит поле status"""
    test_category = {
        "category_id": CAT_ID,
        "name": "Category 1",
        "subtitle": "Subtitle 1",
        "budget_amount": 100000,
        "status": "running",
    }

    with patch("functions.categories.get_category") as mock_get:
        mock_get.return_value = test_category

        async with aiohttp_client(app) as client:
            resp = await client.request(
                "GET", f"/api/v1/admin/categories/{CAT_ID}", headers={"Authorization": "Bearer admin_token"}
            )
            assert resp.status == 200
            data = await resp.json()
            assert data["status"] == "running"


async def test_run_category_success(aiohttp_client, app):
    """Тест: успешный перевод категории в статус running"""
    with patch("functions.categories.update_category_status") as mock_update:
        mock_update.return_value = {"category_id": CAT_ID, "name": "Test", "status": "running"}

        async with aiohttp_client(app) as client:
            resp = await client.request(
                "POST",
                f"/api/v1/admin/categories/{CAT_ID}/run",
                headers={"Authorization": "Bearer admin_token"},
            )
            assert resp.status == 200
            data = await resp.json()
            assert data["status"] == "running"
        mock_update.assert_called_once_with(CAT_ID, "running")


async def test_pause_category_success(aiohttp_client, app):
    """Тест: успешный перевод категории в статус paused"""
    with patch("functions.categories.update_category_status") as mock_update:
        mock_update.return_value = {"category_id": CAT_ID, "name": "Test", "status": "paused"}

        async with aiohttp_client(app) as client:
            resp = await client.request(
                "POST",
                f"/api/v1/admin/categories/{CAT_ID}/pause",
                headers={"Authorization": "Bearer admin_token"},
            )
            assert resp.status == 200
            data = await resp.json()
            assert data["status"] == "paused"
        mock_update.assert_called_once_with(CAT_ID, "paused")


async def test_archive_category_success(aiohttp_client, app):
    """Тест: успешный перевод категории в статус archived"""
    with patch("functions.categories.update_category_status") as mock_update:
        mock_update.return_value = {"category_id": CAT_ID, "name": "Test", "status": "archived"}

        async with aiohttp_client(app) as client:
            resp = await client.request(
                "DELETE",
                f"/api/v1/admin/categories/{CAT_ID}/archive",
                headers={"Authorization": "Bearer admin_token"},
            )
            assert resp.status == 200
            data = await resp.json()
            assert data["status"] == "archived"
        mock_update.assert_called_once_with(CAT_ID, "archived")


async def test_archive_category_not_found(aiohttp_client, app):
    """Тест: archive категории — категория не найдена (404)"""
    with patch("functions.categories.update_category_status") as mock_update:
        mock_update.return_value = None

        async with aiohttp_client(app) as client:
            resp = await client.request(
                "DELETE",
                f"/api/v1/admin/categories/{NOT_FOUND_CAT_ID}/archive",
                headers={"Authorization": "Bearer admin_token"},
            )
            assert resp.status == 404
            data = await resp.json()
            assert data["code"] == "NOT_FOUND"


async def test_run_category_not_found(aiohttp_client, app):
    """Тест: run категории — категория не найдена (404)"""
    with patch("functions.categories.update_category_status") as mock_update:
        mock_update.return_value = None

        async with aiohttp_client(app) as client:
            resp = await client.request(
                "POST",
                f"/api/v1/admin/categories/{NOT_FOUND_CAT_ID}/run",
                headers={"Authorization": "Bearer admin_token"},
            )
            assert resp.status == 404
            data = await resp.json()
            assert data["code"] == "NOT_FOUND"


async def test_update_category_status_via_patch(aiohttp_client, app):
    """Тест: обновление статуса категории через PATCH"""
    with patch("functions.categories.update_category") as mock_update:
        mock_update.return_value = {"category_id": CAT_ID, "name": "Test", "status": "paused"}

        async with aiohttp_client(app) as client:
            resp = await client.request(
                "PATCH",
                f"/api/v1/admin/categories/{CAT_ID}",
                headers={"Content-Type": "application/json", "Authorization": "Bearer admin_token"},
                data=json.dumps({"status": "paused"}),
            )
            assert resp.status == 200
            data = await resp.json()
            assert data["status"] == "paused"
        mock_update.assert_called_once()
        call_kwargs = mock_update.call_args[1]
        assert call_kwargs.get("status") == "paused"


async def test_update_category_invalid_status(aiohttp_client, app):
    """Тест: PATCH с недопустимым status возвращает 422"""
    async with aiohttp_client(app) as client:
        resp = await client.request(
            "PATCH",
            f"/api/v1/admin/categories/{CAT_ID}",
            headers={"Content-Type": "application/json", "Authorization": "Bearer admin_token"},
            data=json.dumps({"status": "active"}),
        )
        assert resp.status == 422
        data = await resp.json()
        assert data["code"] == "VALIDATION_FAILED"
