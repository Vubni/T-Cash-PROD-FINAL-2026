"""
Интеграционные тесты для Offers/Progress API
"""

import pytest
from aiohttp.test import AioHTTPTestCase, unittest_run_loop
from unittest.mock import patch
import json


class TestOffersAPI(AioHTTPTestCase):
    
    async def get_application(self):
        from server import create_app
        return await create_app()
    
    @unittest_run_loop
    async def test_run_offers_success(self):
        test_user_id = 12345
        offers_data = {
            "categories": ["cat1", "cat2", "cat3"],
            "preferences": {"min_rate": 1.0}
        }
        
        test_offers = [
            {
                "offer_id": "offer1",
                "category_id": "cat1",
                "name": "Special Offer 1",
                "benefit": {"cashback_percent": 5.0}
            }
        ]
        
        with patch('functions.offers.run_offers') as mock_offers:
            mock_offers.return_value = test_offers
            
            resp = await self.client.request(
                "POST",
                "/api/v1/offers/run",
                headers={
                    "Content-Type": "application/json",
                    "X-User-ID": str(test_user_id)
                },
                data=json.dumps(offers_data)
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert len(data["offers"]) == 1


class TestProgressAPI(AioHTTPTestCase):
    
    async def get_application(self):
        from server import create_app
        return await create_app()
    
    @unittest_run_loop
    async def test_get_progress_success(self):
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
        
        with patch('functions.progress.get_user_progress') as mock_progress:
            mock_progress.return_value = test_progress
            
            resp = await self.client.request(
                "GET",
                "/api/v1/progress",
                headers={"X-User-ID": str(test_user_id)}
            )
            
            assert resp.status == 200
            data = await resp.json()
            assert len(data["items"]) == 1
            assert data["items"][0]["progress"] == 0.5
