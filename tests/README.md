# Тесты Cashback Backend MVP

## Структура тестов

```
tests/
├── __init__.py
├── unit/                     # Юнит-тесты
│   ├── __init__.py
│   ├── test_users.py         # Тесты функций пользователей
│   ├── test_categories.py    # Тесты функций категорий
│   └── test_calculate.py     # Тесты функций расчета
└── integration/              # Интеграционные тесты
    ├── __init__.py
    ├── test_users_api.py     # Тесты API пользователей
    ├── test_categories_api.py # Тесты API категорий
    └── test_client_api.py    # Тесты Client API
```

## Запуск тестов

### Все тесты
```bash
pytest
```

### Только юнит-тесты
```bash
pytest tests/unit/
```

### Только интеграционные тесты
```bash
pytest tests/integration/
```

### С покрытием кода
```bash
pytest --cov=. --cov-report=html
```

### Конкретный тест
```bash
pytest tests/unit/test_users.py::TestUserExists::test_user_exists_true
```

## Типы данных

- `user_id` везде (в т.ч. `/users/{user_id}/exists`, `POST /api/v1/offers/run`, `/client/*`): **integer** (BIGINT)
- `category_id`: **UUID**
- `admin_id`: **integer**

## Переменные окружения для тестов

Тесты используют следующие переменные:
- `TEST_DATABASE_URL`: URL тестовой базы данных
- `TEST_HOST`: Хост для тестов (по умолчанию localhost)
- `TEST_PORT`: Порт для тестов (по умолчанию 8080)

## Написание тестов

### Юнит-тесты
- Используют `unittest.mock` для мокирования зависимостей
- Тестируют отдельные функции и классы
- Быстрые и изолированные

### Интеграционные тесты
- Используют `aiohttp.test` для тестирования HTTP эндпоинтов
- Тестируют взаимодействие компонентов
- Могут требовать базу данных

### Асинхронные тесты
- Используют декоратор `@pytest.mark.asyncio`
- Для тестирования асинхронных функций

## Примеры

### Юнит-тест
```python
@pytest.mark.asyncio
async def test_user_exists_true():
    with patch('functions.users.get_connection') as mock_conn:
        mock_conn.return_value.__aenter__.return_value.fetchval.return_value = 1
        
        result = await users_fns.user_exists(12345)
        
        assert result is True
```

### Интеграционный тест
```python
@unittest_run_loop
async def test_user_exists_success(self):
    with patch('functions.users.user_exists') as mock_user_exists:
        mock_user_exists.return_value = True
        
        resp = await self.client.request("GET", "/api/v1/users/12345/exists")
        
        assert resp.status == 200
        data = await resp.json()
        assert data["exists"] is True
```

## CI/CD

Тесты автоматически запускаются в GitLab CI при каждом коммите:
- Юнит-тесты: быстрая проверка логики
- Интеграционные тесты: проверка API
- Покрытие кода: отчет о покрытии

## Отладка

Для отладки тестов можно использовать:
```bash
pytest -s -vv tests/unit/test_users.py
```

Для падения в pdb при ошибке:
```bash
pytest --pdb tests/unit/test_users.py
```
