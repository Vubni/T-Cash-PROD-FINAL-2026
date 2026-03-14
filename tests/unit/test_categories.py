"""
Юнит-тесты для функций категорий
"""

import pytest
from unittest.mock import patch
from functions import categories as categories_fns


class TestGetCategories:
    
    @pytest.mark.asyncio
    async def test_get_categories_success(self):
        test_categories = [
            {"category_id": "cat1", "name": "Category 1", "budget_amount": 100000},
            {"category_id": "cat2", "name": "Category 2", "budget_amount": 200000}
        ]
        
        with patch('functions.categories.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetch.return_value = test_categories
            result = await categories_fns.get_categories(limit=10, offset=0)
            assert len(result) == 2
            assert result[0]["name"] == "Category 1"
    
    @pytest.mark.asyncio
    async def test_get_categories_exception(self):
        with patch('functions.categories.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetch.side_effect = Exception("DB Error")
            with pytest.raises(Exception):
                await categories_fns.get_categories()


class TestCreateCategory:
    
    @pytest.mark.asyncio
    async def test_create_category_success(self):
        test_data = {
            "name": "Test Category",
            "subtitle": "Test subtitle",
            "icon_key": "test",
            "budget_amount": 100000,
            "audience_segments": ["mass"],
            "rule_id": "rule1"
        }
        
        with patch('functions.categories.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetchval.return_value = "cat123"
            result = await categories_fns.create_category(test_data)
            assert result == "cat123"


class TestGetCategory:
    
    @pytest.mark.asyncio
    async def test_get_category_success(self):
        test_category = {
            "category_id": "cat1",
            "name": "Category 1",
            "budget_amount": 100000
        }
        
        with patch('functions.categories.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetchrow.return_value = test_category
            result = await categories_fns.get_category("cat1")
            assert result["category_id"] == "cat1"
    
    @pytest.mark.asyncio
    async def test_get_category_not_found(self):
        with patch('functions.categories.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetchrow.return_value = None
            result = await categories_fns.get_category("nonexistent")
            assert result is None


class TestUpdateCategory:
    
    @pytest.mark.asyncio
    async def test_update_category_success(self):
        update_data = {"name": "Updated Category", "budget_amount": 150000}
        
        with patch('functions.categories.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetchval.return_value = 1
            result = await categories_fns.update_category("cat1", update_data)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_update_category_not_found(self):
        update_data = {"name": "Updated Category"}
        
        with patch('functions.categories.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetchval.return_value = 0
            result = await categories_fns.update_category("nonexistent", update_data)
            assert result is False
