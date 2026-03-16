import pytest
from unittest.mock import AsyncMock, patch

from functions import selection as selection_fns


class TestSelectionIdempotency:
    @pytest.mark.asyncio
    async def test_confirm_selection_returns_stored_response_for_same_key(self):
        stored_response = {
            "user_id": 12345,
            "category_ids": [
                "00000000-0000-0000-0000-000000000001",
                "00000000-0000-0000-0000-000000000002",
                "00000000-0000-0000-0000-000000000003",
                "00000000-0000-0000-0000-000000000004",
                "00000000-0000-0000-0000-000000000005",
            ],
            "items": [],
        }

        with patch.object(selection_fns, "Database") as MockDB:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock(
                side_effect=[
                    {},
                    {
                        "request_hash": selection_fns._build_request_hash(12345, stored_response["category_ids"]),
                        "response_body": stored_response,
                        "status_code": 200,
                    },
                ]
            )
            MockDB.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            MockDB.return_value.__aexit__ = AsyncMock(return_value=None)

            response_body, status_code = await selection_fns.confirm_selection(
                12345,
                stored_response["category_ids"],
                idempotency_key="selection-key-1",
            )

            assert status_code == 200
            assert response_body == stored_response
            mock_conn.execute_all.assert_not_called()

    @pytest.mark.asyncio
    async def test_confirm_selection_rejects_same_key_with_other_payload(self):
        first_payload = [
            "00000000-0000-0000-0000-000000000001",
            "00000000-0000-0000-0000-000000000002",
            "00000000-0000-0000-0000-000000000003",
            "00000000-0000-0000-0000-000000000004",
            "00000000-0000-0000-0000-000000000005",
        ]

        with patch.object(selection_fns, "Database") as MockDB:
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock(
                side_effect=[
                    {},
                    {
                        "request_hash": "another-hash",
                        "response_body": {"user_id": 12345, "category_ids": first_payload, "items": []},
                        "status_code": 200,
                    },
                ]
            )
            MockDB.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            MockDB.return_value.__aexit__ = AsyncMock(return_value=None)

            with pytest.raises(selection_fns.IdempotencyConflictError):
                await selection_fns.confirm_selection(
                    12345,
                    first_payload,
                    idempotency_key="selection-key-1",
                )

    def test_normalize_idempotency_key_rejects_blank_value(self):
        with pytest.raises(ValueError):
            selection_fns.normalize_idempotency_key("   ")
