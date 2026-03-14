"""
Юнит-тесты для функций пользователей
"""

import pytest
from unittest.mock import patch, AsyncMock
from functions import users as users_fns


class TestUserExists:

    @pytest.mark.asyncio
    async def test_user_exists_true(self):
        with patch("functions.users.Database") as MockDB:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock(return_value={"x": 1})
            MockDB.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            MockDB.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await users_fns.user_exists(12345)
            assert result is True

    @pytest.mark.asyncio
    async def test_user_exists_false(self):
        with patch("functions.users.Database") as MockDB:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock(return_value=None)
            MockDB.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            MockDB.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await users_fns.user_exists(99999)
            assert result is False

    @pytest.mark.asyncio
    async def test_user_exists_exception(self):
        """При ошибке «таблица не существует» возвращаем True, чтобы не блокировать клиентские ручки."""
        with patch("functions.users.Database") as MockDB:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock(
                side_effect=Exception('relation "users" does not exist')
            )
            MockDB.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            MockDB.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await users_fns.user_exists(12345)
            assert result is True

    @pytest.mark.asyncio
    async def test_user_exists_negative_id(self):
        with patch("functions.users.Database") as MockDB:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock(return_value=None)
            MockDB.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            MockDB.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await users_fns.user_exists(-1)
            assert result is False


@pytest.mark.skip(reason="functions.users.get_user_categories не реализован")
class TestGetUserCategories:
    pass
