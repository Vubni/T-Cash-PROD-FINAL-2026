"""
Юнит-тесты для функций категорий
"""

import pytest
from unittest.mock import patch, AsyncMock
from asyncpg import UniqueViolationError
from functions import categories as categories_fns


class TestListCategories:
    @pytest.mark.asyncio
    async def test_list_categories_success(self):
        test_rows = [
            {
                "category_id": "cat1",
                "name": "Category 1",
                "subtitle": "s1",
                "icon_url": "https://cdn.example.com/cat1.png",
                "budget_amount": 100000,
                "rate_min": 0,
                "rate_max": 100,
                "rule_id": None,
                "min_age": None,
                "max_age": None,
                "gender": None,
                "income": None,
            },
            {
                "category_id": "cat2",
                "name": "Category 2",
                "subtitle": "s2",
                "budget_amount": 200000,
                "rate_min": 0,
                "rate_max": 100,
                "rule_id": None,
                "min_age": None,
                "max_age": None,
                "gender": None,
                "income": None,
            },
        ]
        with patch("functions.categories.Database") as MockDB:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock(return_value={"n": 2})
            mock_conn.execute_all = AsyncMock(return_value=test_rows)
            MockDB.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            MockDB.return_value.__aexit__ = AsyncMock(return_value=None)

            items, total = await categories_fns.list_categories(offset=0, limit=10)
            assert total == 2
            assert len(items) == 2
            assert items[0]["name"] == "Category 1"
            assert items[0]["icon_url"] == "https://cdn.example.com/cat1.png"

    @pytest.mark.asyncio
    async def test_list_categories_exception(self):
        with patch("functions.categories.Database") as MockDB:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock(side_effect=Exception("DB Error"))
            MockDB.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            MockDB.return_value.__aexit__ = AsyncMock(return_value=None)

            with pytest.raises(Exception):
                await categories_fns.list_categories(offset=0, limit=10)


class TestCreateCategory:
    @pytest.mark.asyncio
    async def test_create_category_success(self):
        row = {
            "category_id": "cat123",
            "name": "Test Category",
            "subtitle": "Test subtitle",
            "icon_url": "https://cdn.example.com/test.png",
            "budget_amount": 100000,
            "rate_min": 0,
            "rate_max": 100,
            "rule_id": None,
            "min_age": None,
            "max_age": None,
            "gender": None,
            "income": None,
        }
        with patch("functions.categories.Database") as MockDB:
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(return_value="cat123")
            mock_conn.execute = AsyncMock(return_value=row)
            MockDB.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            MockDB.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await categories_fns.create_category(
                admin_id=1,
                name="Test Category",
                subtitle="Test subtitle",
                budget_amount=100000,
                rate_min=0,
                rate_max=100,
            )
            category, created_now = result
            assert category is not None
            assert created_now is True
            assert category.get("id") == "cat123"
            assert category.get("icon_url") == "https://cdn.example.com/test.png"

    @pytest.mark.asyncio
    async def test_create_category_idempotent_replay_returns_saved_response(self):
        saved_response = {"id": "cat123", "name": "Test Category"}
        with patch("functions.categories.Database") as MockDB:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock(
                side_effect=[
                    {},
                    {"request_hash": categories_fns._build_create_category_request_hash("Test Category", "Test subtitle", 100000, 0, 100), "response_body": saved_response},
                ]
            )
            MockDB.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            MockDB.return_value.__aexit__ = AsyncMock(return_value=None)

            category, created_now = await categories_fns.create_category(
                admin_id=1,
                name="Test Category",
                subtitle="Test subtitle",
                budget_amount=100000,
                rate_min=0,
                rate_max=100,
                idempotency_key="same-key",
            )

            assert category == saved_response
            assert created_now is False
            assert mock_conn.fetchval.await_count == 0

    @pytest.mark.asyncio
    async def test_create_category_duplicate_name_raises_domain_error(self):
        with patch("functions.categories.Database") as MockDB:
            mock_conn = AsyncMock()
            mock_conn.fetchval = AsyncMock(side_effect=UniqueViolationError("duplicate key"))
            MockDB.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            MockDB.return_value.__aexit__ = AsyncMock(return_value=None)

            with pytest.raises(categories_fns.DuplicateCategoryNameError):
                await categories_fns.create_category(
                    admin_id=1,
                    name="Test Category",
                    subtitle="Test subtitle",
                    budget_amount=100000,
                    rate_min=0,
                    rate_max=100,
                )


class TestGetCategory:
    @pytest.mark.asyncio
    async def test_get_category_success(self):
        test_row = {
            "category_id": "cat1",
            "name": "Category 1",
            "subtitle": "s",
            "icon_url": "https://cdn.example.com/cat1.png",
            "budget_amount": 100000,
            "rate_min": 0,
            "rate_max": 100,
            "rule_id": None,
            "min_age": None,
            "max_age": None,
            "gender": None,
            "income": None,
        }
        with patch("functions.categories.Database") as MockDB:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock(return_value=test_row)
            MockDB.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            MockDB.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await categories_fns.get_category("cat1")
            assert result is not None
            assert result["id"] == "cat1"
            assert result["icon_url"] == "https://cdn.example.com/cat1.png"

    @pytest.mark.asyncio
    async def test_get_category_not_found(self):
        with patch("functions.categories.Database") as MockDB:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock(return_value=None)
            MockDB.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            MockDB.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await categories_fns.get_category("nonexistent")
            assert result is None


class TestUpdateCategory:
    @pytest.mark.asyncio
    async def test_update_category_success(self):
        test_row = {
            "category_id": "cat1",
            "name": "Updated",
            "subtitle": "s",
            "icon_url": "https://cdn.example.com/updated.png",
            "budget_amount": 150000,
            "rate_min": 0,
            "rate_max": 100,
            "rule_id": None,
            "min_age": None,
            "max_age": None,
            "gender": None,
            "income": None,
        }
        with patch("functions.categories.Database") as MockDB:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock(side_effect=[None, test_row])
            MockDB.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            MockDB.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await categories_fns.update_category("cat1", name="Updated Category", budget_amount=150000)
            assert result is not None
            assert result["icon_url"] == "https://cdn.example.com/updated.png"

    @pytest.mark.asyncio
    async def test_update_category_not_found(self):
        with patch("functions.categories.Database") as MockDB:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock(side_effect=[None, None])
            MockDB.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            MockDB.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await categories_fns.update_category("nonexistent", name="Updated")
            assert result is None
