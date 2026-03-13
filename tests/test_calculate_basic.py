import json

from api import calculate


# def test_calculate_response_structure(monkeypatch):
#     class DummyRequest:
#         def __init__(self):
#             self._app = {}

#         @property
#         def app(self):
#             return self._app

#     class DummyParsed:
#         def __init__(self, period_id=None):
#             self.period_id = period_id

#     import asyncio

#     async def _call():
#         return await calculate.calculate(DummyRequest(), DummyParsed())

#     response = asyncio.run(_call())

#     assert response.status == 200

#     body = json.loads(response.text)
#     assert "period_id" in body
#     assert "items" in body
#     assert isinstance(body["items"], list)
#     assert body["period_id"] == "2026-03"

