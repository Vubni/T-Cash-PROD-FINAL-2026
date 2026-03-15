## Cashback Backend MVP

### Описание

**Backend**

API: **categories**, **rules**, **offers/run**, **selection**, **audit**.

Сервер гарантирует:
- диапазоны ставок и лимиты;
- идемпотентность и защиту от повторных действий (в т.ч. заголовок `Idempotency-Key` при подтверждении выбора);
- проверку всех бюджетных инвариантов на сервере, а не только в интерфейсе.

Реализует админские ручки (категории, правила, аудит) и клиентские (запуск офферов, выбор, подтверждение).

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
│   ├── categories.py         # эндпоинты /api/v1/admin/categories
│   ├── calculate.py          # эндпоинт /api/v1/offers/run
│   ├── rules.py              # эндпоинты /api/v1/admin/rules
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
│   └── init.sql              # создание схемы БД (rules, categories, selections, audit_log)
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
- **categories**: `GET` / `POST` /api/v1/admin/categories, `GET` / `PATCH` /api/v1/admin/categories/{category_id}.
- **rules**: `GET` / `POST` /api/v1/admin/rules, `GET` / `PATCH` /api/v1/admin/rules/{rule_id}.
- **audit**: `GET /api/v1/admin/audit` — журнал аудита.

Клиентские эндпоинты:
- **offers/run**: `POST /api/v1/offers/run` — запуск офферов (расчёт списка категорий для клиента).
- **selection**: `GET` / `POST` /api/v1/client/selection/{selection_id} — получение и подтверждение выбора (`Idempotency-Key`).

Все схемы запросов/ответов описаны через `docs/schems.py` и видны в Swagger.

---

### Архитектура

**Слой HTTP / API**
- `server.py` — точка входа:
  - создаёт aiohttp‑приложение;
  - подключает CORS и middleware валидации (`validation_middleware`);
  - настраивает Swagger (`/doc`, `/swagger.json`);
  - регистрирует роуты из модулей `api.categories`, `api.rules`, `api.audit`, `api.calculate`, `api.selection`;
  - проксирует все остальные запросы на статику через `handle_get_file`.

**Модули API**
- `api/categories.py` — CRUD категорий кэшбэка (с привязкой к правилу `rule_id`).
- `api/rules.py` — CRUD правил отбора (возраст мин/макс, пол, заработок).
- `api/audit.py` — чтение журнала аудита.
- `api/calculate.py` — запуск офферов (`POST /api/v1/offers/run`).
- `api/selection.py` — получение и подтверждение выбора (идемпотентность по `Idempotency-Key`).
- `api/validate.py` — схемы валидации и формат ошибок.

**База данных**

PostgreSQL поднимается из `docker-compose.yml` и инициализируется скриптом `postgres/init.sql`.

Схема:
- Таблица `rules`
  - `id` — внутренний автоинкрементный ID.
  - `rule_id` — бизнес‑ID правила (уникальный).
  - `min_age`, `max_age` — минимальный и максимальный возраст (nullable).
  - `gender` — пол (nullable).
  - `income` — заработок (nullable).
  - `created_at`, `updated_at` — временные метки.

- Таблица `categories`
  - `id` — внутренний автоинкрементный ID.
  - `category_id` — бизнес‑ID категории (уникальный).
  - `name`, `subtitle` — метаданные категории.
  - `budget_amount` — бюджет на одного пользователя по категории за период.
  - `rule_id` — ссылка на `rules.rule_id` (правило отбора: возраст, пол, заработок).
  - `created_at`, `updated_at` — временные метки.

- Таблица `selections`
  - `id` — внутренний ID выбора.
  - `selection_id` — внешний ID выбора (отдаётся клиенту).
  - `category_id` — ссылка на `categories.category_id` (TEXT).
  - `expected_benefit_amount` — ожидаемая выгода.
  - `availability_status`, `availability_reason` — статусы доступности.
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
