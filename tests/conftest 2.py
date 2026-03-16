"""Общие фикстуры для тестов (aiohttp app и клиент)."""

import pytest


@pytest.fixture
def app():
    """Приложение aiohttp для интеграционных тестов."""
    from server import create_app

    return create_app()


@pytest.fixture
def aiohttp_client():
    """Фабрика клиента aiohttp: использовать как async with aiohttp_client(app) as client."""
    from aiohttp.test_utils import TestClient, TestServer

    def _factory(app):
        return TestClient(TestServer(app))

    return _factory
