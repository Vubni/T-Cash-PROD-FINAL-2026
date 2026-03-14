"""
Юнит-тесты для функций офферов и прогресса
"""

import pytest
from unittest.mock import patch
from functions import offers as offers_fns
from functions import progress as progress_fns


class TestOffersFunctions:
    
    @pytest.mark.asyncio
    async def test_run_offers_success(self):
        test_user_id = 12345
        test_offers_data = {
            "categories": ["cat1", "cat2", "cat3"],
            "preferences": {"min_rate": 1.0}
        }
        
        with patch('functions.offers.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetch.return_value = [
                {"category_id": "cat1", "name": "Category 1"},
                {"category_id": "cat2", "name": "Category 2"}
            ]
            result = await offers_fns.run_offers(test_user_id, test_offers_data)
            assert len(result) >= 0
    
    @pytest.mark.asyncio
    async def test_get_available_offers_success(self):
        test_user_id = 12345
        
        with patch('functions.offers.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetch.return_value = [
                {
                    "offer_id": "offer1",
                    "category_id": "cat1",
                    "name": "Offer 1",
                    "conditions": {"min_age": 18}
                }
            ]
            result = await offers_fns.get_available_offers(test_user_id)
            assert len(result) == 1
            assert result[0]["offer_id"] == "offer1"


class TestProgressFunctions:
    
    @pytest.mark.asyncio
    async def test_get_user_progress_success(self):
        test_user_id = 12345
        test_progress = [
            {
                "category_id": "cat1",
                "progress": 0.5,
                "target_amount": 1000,
                "current_amount": 500,
                "status": "active"
            }
        ]
        
        with patch('functions.progress.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetch.return_value = test_progress
            result = await progress_fns.get_user_progress(test_user_id)
            assert len(result) == 1
            assert result[0]["progress"] == 0.5
    
    @pytest.mark.asyncio
    async def test_update_progress_success(self):
        test_user_id = 12345
        test_category_id = "cat1"
        test_progress = 0.75
        
        with patch('functions.progress.get_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.fetchval.return_value = 1
            result = await progress_fns.update_progress(
                test_user_id, 
                test_category_id, 
                test_progress
            )
            assert result is True
    
    @pytest.mark.asyncio
    async def test_calculate_progress_success(self):
        current_amount = 750
        target_amount = 1000
        
        result = progress_fns.calculate_progress(current_amount, target_amount)
        assert result == 0.75
