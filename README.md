## Cashback Backend MVP

### Что это за сервис

Backend‑сервис для MVP кешбэк‑программы:

- **Админские возможности**:
  - управление категориями кешбэка;
  - настройка правил отбора (возраст, пол, доход и т.д.);
  - просмотр журнала аудита изменений;
  - управление админами.
- **Клиентские возможности**:
  - запуск расчёта офферов (`/offers/run`);
  - получение и подтверждение выбора категории (`/client/selection/...`) с защитой от повторов через `Idempotency-Key`.

Сервер гарантирует:
- диапазоны ставок и лимиты;
- идемпотентность при подтверждении выбора;
- валидацию всех бюджетных инвариантов на стороне backend.

**Технологический стек**
- Python 3.12 + `aiohttp`
- PostgreSQL + `asyncpg`
- `marshmallow` + `aiohttp-apispec` (валидация и Swagger)
- Alembic (миграции схемы БД)
- Docker + docker compose

---

### Структура проекта

```text
backend/
├── api/                     # HTTP-слой и обработчики роутов
│   ├── __init__.py
│   ├── admin_auth.py        # Регистрация/апрув админов
│   ├── audit.py             # Админское API журнала аудита
│   ├── categories.py        # Админское API категорий и правил отбора
│   ├── calculate.py         # Клиентский запуск офферов (/offers/run)
│   ├── selection.py         # Клиентский выбор и подтверждение
│   ├── users.py             # API пользователей
│   └── validate.py          # Общие схемы валидации и ошибки
├── core/                    # Базовые сервисы и утилиты
│   ├── __init__.py
│   ├── auth.py              # JWT / авторизация админов
│   └── utils.py             # Общие хелперы
├── functions/               # Бизнес-логика без HTTP
│   ├── __init__.py
│   ├── calculate.py         # Алгоритм отбора категорий, причины
│   └── wordly.py            # Логика игры Wordly
├── database/                # Доступ к БД (PostgreSQL)
│   ├── __init__.py
│   ├── database.py          # Обёртка над asyncpg, транзакции
│   └── functions.py         # Хелперы и инициализация
├── alembic/                 # Миграции схемы БД
│   ├── env.py
│   ├── alembic.ini
│   └── versions/            # 0001_... -> 0009_wordly_words.py
├── docs/
│   ├── __init__.py
│   └── schemas.py           # Описание схем для Swagger
├── tests/                   # Юнит- и интеграционные тесты
│   ├── unit/
│   ├── integration/
│   ├── README.md
│   └── ANALYSIS.md
├── postgres/
│   └── init.sql             # Базовая инициализация БД для docker-compose
├── config/                  # Статическая конфигурация домена
│   └── categories_config.json
├── static/                  # Статика (если нужна для фронта)
├── .gitignore
├── docker-compose.yml
├── docker-compose.ci.yml
├── Dockerfile
├── requirements.txt
├── config.py                # Конфигурация приложения (env, URLs и т.д.)
├── logging_setup.py         # Настройка логирования
├── startup.py               # Инициализация на старте (hook для запуска)
└── server.py                # Точка входа, создание aiohttp-приложения
```

---

### RUNBOOK: как запустить локально

#### Вариант 1. Через Docker (рекомендуется)

1. Установи Docker / Docker Desktop.
2. В корне `backend` создай файл `.env` (можно пустой — базовые переменные заданы в `docker-compose.yml`).
3. Из директории `backend` выполни:

```bash
docker compose up --build
```

4. После старта сервисов:
   - API доступен по `http://localhost:8080`
   - Swagger UI: `http://localhost:8080/doc`

5. Остановка:

```bash
docker compose down
```

#### Вариант 2. Локальный запуск без Docker

Требуется установленный PostgreSQL.

1. Создай БД (по умолчанию: `prod`, пользователь `user`/`password` или свои значения через переменные окружения `DB_*` / `DATABASE_URL`).
2. Установи зависимости:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3. Прогон миграций Alembic:

```bash
alembic upgrade head
```

4. Запусти приложение:

```bash
python server.py
```

После запуска:
- API: `http://localhost:8080`
- Swagger: `http://localhost:8080/doc`

---

### API обзор (высокоуровнево)

**Админские эндпоинты**
- **categories**  
  - `GET /api/v1/admin/categories`
  - `POST /api/v1/admin/categories`
  - `GET /api/v1/admin/categories/{category_id}`
  - `PATCH /api/v1/admin/categories/{category_id}`  
  - Правила отбора:  
    `GET|POST|PATCH|DELETE /api/v1/admin/categories/{category_id}/rule`

- **audit**  
  - `GET /api/v1/admin/audit` — журнал аудита изменений.

- **admin_auth / users**  
  - регистрация/одобрение админов, авторизация, список ожидающих и т.д.

**Клиентские эндпоинты**
- **offers/run**  
  - `POST /api/v1/offers/run` — запуск расчёта списка категорий для клиента (внутри — вызов внешнего ML‑сервиса).

- **selection**  
  - `GET /api/v1/client/selection/{selection_id}` — получение информации по выбору;
  - `POST /api/v1/client/selection/{selection_id}` — подтверждение выбора.  
    Идемпотентность обеспечивается заголовком `Idempotency-Key`.

Все схемы запросов/ответов описаны в `docs/schemas.py` и отображаются в Swagger.

---

### Архитектура (слойный монолит)

- **Слой HTTP / API (`api/`, `server.py`)**
  - Парсинг запросов / параметров;
  - валидация входных данных;
  - формирование HTTP‑ответов и ошибок;
  - подключение middleware (логирование, валидация, обработка ошибок);
  - Swagger‑документация.

- **Слой бизнес‑логики (`functions/`, частично `core/`)**
  - Алгоритм расчёта офферов и причин (reasons) по категории;
  - вызов внешнего ML‑сервиса;
  - логика игры Wordly;
  - вспомогательные функции и авторизация (`core/auth.py`, `core/utils.py`).

- **Слой доступа к данным (`database/`, `alembic/`)**
  - `database/database.py` — обёртка над asyncpg, управление соединениями и транзакциями;
  - миграции в `alembic/versions/` описывают эволюцию схемы (rules, categories, selections, users, admin_users, audit_log, wordly_words и т.д.).

Архитектурно это **слойный монолит**: API → бизнес‑логика → слой данных, развёртываемый как единый сервис.

---

### Миграции БД

Используется Alembic, конфиг — в `alembic.ini` и `alembic/env.py`.

- Применить все миграции:

```bash
alembic upgrade head
```

- Откатить на один шаг назад:

```bash
alembic downgrade -1
```

Основные изменения в схемe:
- `0001_initial_schema` — базовые `categories`, `selections`, `audit_log`;
- `0002_rules_and_category_rule_id` — таблица `rules` и связь с `categories`;
- `0002_users_and_selection_user_period` / `0003_drop_users_role` — пользователи и связь `selections.user_id`;
- `0003_uuid_ids` — переход бизнес‑ID на `UUID`;
- `0004`–`0007` — очистка ненужных полей, `rate_min`/`rate_max`, CHECK‑ограничения, BIGINT для бюджета;
- `0008` — `UNIQUE (user_id, category_id)` в `selections`;
- `0009_wordly_words` — таблица слов для игры Wordly.

---

### Тестирование

#### Юнит‑ и интеграционные тесты (pytest)

Запуск всех тестов:

```bash
pytest
```

С покрытием:

```bash
pytest --cov=. --cov-report=term-missing
```

Структура тестов:
- `tests/unit/` — юнит‑тесты бизнес‑логики и вспомогательных функций;
- `tests/integration/` — интеграционные тесты HTTP‑ручек;
- `tests/ANALYSIS.md` — подробный разбор покрытия и соответствия ТЗ.

#### Тестирование через Insomnia

В корне проекта лежит файл `insomnia_cashback_mvp.json` — коллекция запросов для Insomnia:
- окружение `Base Environment` с `baseUrl = http://localhost:8080`;
- позитивные запросы ко всем основным endpoint;
- отдельные `[NEGATIVE]`‑запросы для проверки валидации и ошибок.

Импортируй файл в Insomnia и используй `baseUrl` из окружения.
