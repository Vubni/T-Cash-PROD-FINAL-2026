## Cashback Backend MVP

### Описание

Backend‑сервис для MVP программы кэшбэка. Реализует админские ручки (категории, аудит) и клиентские ручки (расчёт категорий, выбор и подтверждение выбора).

Стек:
- Python + aiohttp
- asyncpg (PostgreSQL)
- marshmallow + aiohttp-apispec (валидация и Swagger)
- Docker + docker compose

---

### Структура проекта

```text
backend/
├── api/
│   ├── __init__.py
│   ├── audit.py              # эндпоинты /api/v1/admin/audit
│   ├── calculate.py          # эндпоинты /api/v1/client/calculate
│   ├── categories.py         # эндпоинты /api/v1/admin/categories
│   ├── selection.py          # эндпоинты /api/v1/client/selection/*
│   └── validate.py           # схемы валидации и формат ошибок
├── database/
│   ├── __init__.py
│   ├── database.py           # обёртка над asyncpg и управление транзакциями
│   └── functions.py          # функции инициализации/миграций БД
├── docs/
│   ├── __init__.py
│   └── schems.py             # marshmallow‑схемы для swagger и API
├── functions/                # служебные/потенциальные бизнес‑функции (пока пусто)
├── postgres/
│   └── init.sql              # создание схемы БД (categories, selections, audit_log)
├── static/                   # статика и фронт (index.html и ассеты)
├── .gitignore
├── docker-compose.yml        # описание сервисов app + db
├── Dockerfile                # образ backend‑приложения
├── requirements.txt          # зависимости Python
├── config.py                 # конфиг и логгер, загрузка .env
├── server.py                 # точка входа aiohttp‑приложения
└── README.md
```

---

### RUNBOOK: как запустить локально

**Через Docker (рекомендуется)**

1. Установи Docker / Docker Desktop.
2. В корне `backend` создай файл `.env` (можно пустой, все нужные переменные уже заданы в `docker-compose.yml` через `environment`).
3. Из директории `backend` выполни:

```bash
docker compose up --build
```

4. После старта сервисов:
   - API доступен по `http://localhost:8080`
   - Swagger UI: `http://localhost:8080/doc`

**Завершение работы**

```bash
docker compose down
```

---

### API обзор

Админские эндпоинты:
- `GET  /api/v1/admin/categories` — список категорий кэшбэка.
- `POST /api/v1/admin/categories` — создание категории.
- `GET  /api/v1/admin/categories/{category_id}` — получение категории.
- `PATCH /api/v1/admin/categories/{category_id}` — частичное обновление категории.
- `GET  /api/v1/admin/audit` — журнал аудита изменений.

Клиентские эндпоинты:
- `POST /api/v1/client/calculate` — расчёт списка категорий для клиента.
- `GET  /api/v1/client/selection/{selection_id}` — получение конкретного выбора.
- `POST /api/v1/client/selection/{selection_id}` — подтверждение выбора (поддерживается `Idempotency-Key`).

Все схемы запросов/ответов описаны через `docs/schems.py` и видны в Swagger.

---

### Архитектура

**Слой HTTP / API**
- `server.py` — точка входа:
  - создаёт aiohttp‑приложение;
  - подключает CORS и middleware валидации (`validation_middleware`);
  - настраивает Swagger (`/doc`, `/swagger.json`);
  - регистрирует роуты из модулей `api.categories`, `api.audit`, `api.calculate`, `api.selection`;
  - проксирует все остальные запросы на статику через `handle_get_file`.

**Модули API**
- `api/categories.py` — CRUD категории кэшбэка.
- `api/audit.py` — чтение журнала аудита.
- `api/calculate.py` — расчёт клиентского списка категорий по периоду.
- `api/selection.py` — получение и подтверждение выбора.
- `api/validate.py` — описания схем валидации и общий формат ошибок.

**База данных**

PostgreSQL поднимается из `docker-compose.yml` и инициализируется скриптом `postgres/init.sql`.

Схема:
- Таблица `categories`
  - `id` — внутренний автоинкрементный ID.
  - `category_id` — бизнес‑ID категории (используется в API и связях).
  - `name`, `subtitle`, `icon_key`, `status` — метаданные категории.
  - `budget_amount` — общий бюджет.
  - `target_users` — целевое число уникальных пользователей в период.
  - `avg_spend_per_user` — средний чек/траты одного пользователя по категории (заглушка для будущего ML).
  - `audience_segments` — список сегментов аудитории, для которых категория доступна.
  - `rule_personalized` — признак, что для категории вообще применяются персонализированные правила.
  - `rule_budget_mode` — режим работы с бюджетом.
  - `rule_fallback_message` — текст сообщения при недоступности.
  - `created_at`, `updated_at` — системные временные метки.

- Таблица `selections`
  - `id` — внутренний ID выбора.
  - `selection_id` — внешний ID выбора (отдаётся клиенту).
  - `period_id` — период расчёта (например, `2026-03`).
  - `category_id` — ссылка на `categories.category_id`.
  - `status` — статус выбора.
  - `expected_benefit_amount` — ожидаемая выгода.
  - `availability_status`, `availability_reason` — технический и человекочитаемый статусы доступности.
  - `idempotency_key` — ключ идемпотентности для подтверждения.
  - `created_at`, `updated_at` — временные метки.

- Таблица `audit_log`
  - `id` — внутренний ID записи аудита.
  - `entity_type` — тип сущности (`category`, `selection` и т.д.).
  - `entity_id` — идентификатор сущности.
  - `action` — действие (create/update/confirm и т.п.).
  - `actor` — инициатор изменения.
  - `details` — JSON с деталями события.
  - `created_at` — время события.

**Работа с БД**
- `database/database.py` — обёртка над asyncpg:
  - управление подключением и транзакцией через контекстный менеджер `Database`;
  - методы `execute`, `execute_all`, `fetchval`, `executemany`;
  - сериализация результатов в JSON‑дружелюбный формат.
- `database/functions.py` — точка для инициализации/миграций на старте (сейчас просто шаблон).

---

### Тестирование через Insomnia

В корне проекта лежит файл `insomnia_cashback_mvp.json` — коллекция запросов для Insomnia:
- окружение `Base Environment` с `baseUrl = http://localhost:8080`;
- позитивные запросы к каждому endpoint;
- отдельные [NEGATIVE]‑запросы для проверки валидации и ошибок (не перепутай их с основными).

Импортируй файл в Insomnia и используй `baseUrl` из окружения.

