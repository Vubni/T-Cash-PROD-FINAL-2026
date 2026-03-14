"""
Юнит-тесты для функций пользователей
"""

import pytest
from unittest.mock import patch
from functions import users as users_fns


class TestUserExists:
    
    @pytest.mark.asyncio
    async def test_user_exists_true(self):
        with patch('functions.users.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetchval.return_value = 1
            result = await users_fns.user_exists(12345)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_user_exists_false(self):
        with patch('functions.users.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetchval.return_value = 0
            result = await users_fns.user_exists(99999)
            assert result is False
    
    @pytest.mark.asyncio
    async def test_user_exists_exception(self):
        with patch('functions.users.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetchval.side_effect = Exception("Table not found")
            result = await users_fns.user_exists(12345)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_user_exists_negative_id(self):
        with patch('functions.users.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetchval.return_value = 0
            result = await users_fns.user_exists(-1)
            assert result is False


class TestGetUserCategories:
    
    @pytest.mark.asyncio
    async def test_get_user_categories_success(self):
        test_categories = [
            {"category_id": "cat1", "name": "Category 1"},
            {"category_id": "cat2", "name": "Category 2"}
        ]
        
        with patch('functions.users.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetch.return_value = test_categories
            result = await users_fns.get_user_categories(12345)
            assert result == test_categories
    
    @pytest.mark.asyncio
    async def test_get_user_categories_empty(self):
        with patch('functions.users.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetch.return_value = []
            result = await users_fns.get_user_categories(12345)
            assert result == []
    
    @pytest.mark.asyncio
    async def test_get_user_categories_exception(self):
        with patch('functions.users.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetch.side_effect = Exception("DB Error")
            with pytest.raises(Exception):
                await users_fns.get_user_categories(12345)
