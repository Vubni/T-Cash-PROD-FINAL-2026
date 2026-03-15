"""Фикстуры для интеграционных тестов: мок авторизации админа."""

import pytest
from unittest.mock import patch


# Патчим до импорта app, чтобы все эндпоинты с require_admin/require_super_admin получали подмену
async def _pass_ordinary(request):
    request["admin_payload"] = {"admin_id": 1, "main_admin": False, "approved": True}
    return None


async def _pass_super(request):
    request["admin_payload"] = {"admin_id": 1, "main_admin": True, "approved": True}
    return None


# Тесты, которые проверяют 401 без токена/с невалидным токеном — мок не применяем
_AUDIT_NO_AUTH_TEST_NAMES = {"test_get_audit_unauthorized", "test_get_audit_invalid_token"}


@pytest.fixture(autouse=True)
def mock_admin_auth(request):
    """Подмена проверки админа: в интеграционных тестах пропускаем JWT и подставляем admin_payload."""
    if request.node.name in _AUDIT_NO_AUTH_TEST_NAMES:
        yield
        return
    with patch("api.validate._check_ordinary_admin", side_effect=_pass_ordinary):
        with patch("api.validate._check_super_admin", side_effect=_pass_super):
            yield
