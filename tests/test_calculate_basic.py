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
#         pass

#     import asyncio

#     async def _call():
#         return await calculate.calculate(DummyRequest(), DummyParsed())

#     response = asyncio.run(_call())

#     assert response.status == 200

#     body = json.loads(response.text)
#     assert "items" in body
#     assert isinstance(body["items"], list)

