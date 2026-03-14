"""Общие фикстуры для тестов (aiohttp app и клиент)."""
import pytest


@pytest.fixture
def app():
    """Приложение aiohttp для интеграционных тестов."""
    from server import create_app
    return create_app()
