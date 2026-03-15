"""
Unit-тесты для functions.calculate.get_calculate_items: кэш selections и вызов ML.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_get_calculate_items_returns_from_cache_when_selections_exist():
    """Если у user_id есть записи в selections — возвращаем их, ML не вызывается."""
    from functions.calculate import get_calculate_items

    cached_rows = [
        {
            "selection_id": "sel-1",
            "category_id": "cat-1",
            "name": "Рестораны",
            "subtitle": "Еда",
            "rate_min": 5,
            "rate_max": 15,
        }
    ]

    async def mock_execute_all(sql, params):
        if "selections" in sql and "user_id" in sql:
            return cached_rows
        return []

    with patch("functions.calculate.Database") as MockDb:
        mock_db = AsyncMock()
        mock_db.__aenter__.return_value.execute_all = AsyncMock(side_effect=mock_execute_all)
        mock_db.__aenter__.return_value.execute = AsyncMock(return_value=None)
        MockDb.return_value = mock_db

        result = await get_calculate_items(31471)

    assert result["already_selected_categories"] is True
    assert len(result["items"]) == 1
    assert result["items"][0]["name"] == "Рестораны"
    assert result["items"][0]["category_id"] == "cat-1"


@pytest.mark.asyncio
async def test_get_calculate_items_calls_ml_with_correct_body_when_no_cache():
    """Без кэша: загружаем категории из БД (LIMIT get_all_categories), шлём в ML categories, client_id, top_n."""
    from functions.calculate import get_calculate_items

    db_categories = [
        {"category_id": "c1", "name": "Аптеки", "subtitle": "Лекарства", "rate_min": 3, "rate_max": 10, "budget_amount": 100_000},
    ]
    ml_predictions = [
        {"category": "Аптеки", "estimated_spend": 50_000},
    ]

    call_count = 0

    async def mock_execute_all(sql, params):
        nonlocal call_count
        call_count += 1
        if "selections" in sql:
            return []
        if "FROM categories LIMIT" in sql:
            return db_categories
        return []

    async def mock_execute(sql, params):
        if "name" in sql and params[0] == "Аптеки":
            return {"category_id": "c1", "name": "Аптеки", "subtitle": "Лекарства", "rate_min": 3, "rate_max": 10, "budget_amount": 100_000}
        return None

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"predictions": ml_predictions})
    mock_response.text = AsyncMock(return_value="")

    mock_post = AsyncMock()
    mock_post.__aenter__ = AsyncMock(return_value=mock_response)
    mock_post.__aexit__ = AsyncMock(return_value=None)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_post)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("functions.calculate.Database") as MockDb, \
         patch("functions.calculate.get_all_categories", return_value=1), \
         patch("functions.calculate.ML_SERVICE_URL", "http://ml:8008"), \
         patch("aiohttp.ClientSession", return_value=mock_session):
        mock_db_instance = AsyncMock()
        mock_db_instance.execute_all = AsyncMock(side_effect=mock_execute_all)
        mock_db_instance.execute = AsyncMock(side_effect=mock_execute)
        MockDb.return_value.__aenter__.return_value = mock_db_instance

        result = await get_calculate_items(99999)

    assert result["already_selected_categories"] is False
    assert len(result["items"]) == 1
    assert result["items"][0]["name"] == "Аптеки"
    assert result["items"][0]["cashback"] == 10  # 100_000*100/50_000=200, clamped to rate_max 10
    # Проверяем, что в ML ушёл запрос с ожидаемыми полями (top_n = max(1, get_all_categories()))
    mock_session.post.assert_called_once()
    call_args = mock_session.post.call_args
    assert call_args[0][0].endswith("/predict")
    body = call_args[1]["json"]
    assert "categories" in body
    assert body["categories"] == ["Аптеки"]
    assert body["client_id"] == "99999"
    assert body["top_n"] == 1


@pytest.mark.asyncio
async def test_get_calculate_items_uses_ml_category_names_fallback_when_db_returns_empty():
    """Когда get_all_categories()=0 и LIMIT 0 даёт 0 категорий — в ML уходит ML_CATEGORY_NAMES."""
    from functions.calculate import get_calculate_items
    from core import ML_CATEGORY_NAMES

    async def mock_execute_all(sql, params):
        if "selections" in sql:
            return []
        if "FROM categories LIMIT" in sql:
            return []
        return []

    async def mock_execute(sql, params):
        return None

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"predictions": []})
    mock_response.text = AsyncMock(return_value="")

    mock_post = AsyncMock()
    mock_post.__aenter__ = AsyncMock(return_value=mock_response)
    mock_post.__aexit__ = AsyncMock(return_value=None)
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_post)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("functions.calculate.Database") as MockDb, \
         patch("functions.calculate.get_all_categories", return_value=0), \
         patch("functions.calculate.ML_SERVICE_URL", "http://ml:8008"), \
         patch("aiohttp.ClientSession", return_value=mock_session):
        mock_db_instance = AsyncMock()
        mock_db_instance.execute_all = AsyncMock(side_effect=mock_execute_all)
        mock_db_instance.execute = AsyncMock(side_effect=mock_execute)
        MockDb.return_value.__aenter__.return_value = mock_db_instance

        result = await get_calculate_items(1)

    assert result["already_selected_categories"] is False
    assert result["items"] == []
    call_args = mock_session.post.call_args
    body = call_args[1]["json"]
    assert body["categories"] == ML_CATEGORY_NAMES
    assert body["client_id"] == "1"
    assert body["top_n"] == 1  # max(1, get_all_categories()) при 0


@pytest.mark.asyncio
async def test_get_calculate_items_raises_on_ml_non_200():
    """При ответе ML != 200 выбрасывается исключение."""
    from functions.calculate import get_calculate_items

    async def mock_execute_all(sql, params):
        if "selections" in sql:
            return []
        if "FROM categories LIMIT" in sql:
            return [{"category_id": "c1", "name": "Аптеки", "subtitle": "", "rate_min": 0, "rate_max": 10}]
        return []

    mock_response = MagicMock()
    mock_response.status = 503
    mock_response.text = AsyncMock(return_value="Service Unavailable")

    mock_post = AsyncMock()
    mock_post.__aenter__ = AsyncMock(return_value=mock_response)
    mock_post.__aexit__ = AsyncMock(return_value=None)
    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_post)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("functions.calculate.Database") as MockDb, \
         patch("functions.calculate.get_all_categories", return_value=1), \
         patch("functions.calculate.ML_SERVICE_URL", "http://ml:8008"), \
         patch("aiohttp.ClientSession", return_value=mock_session):
        mock_db_instance = AsyncMock()
        mock_db_instance.execute_all = AsyncMock(side_effect=mock_execute_all)
        MockDb.return_value.__aenter__.return_value = mock_db_instance

        with pytest.raises(Exception) as exc_info:
            await get_calculate_items(1)
        assert "503" in str(exc_info.value)
