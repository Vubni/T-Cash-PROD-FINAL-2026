# Cashback Service API

Документ описывает рекомендуемую серверную API-модель для сервиса персонализированного кэшбэка с жёстким контролем бюджетов.

## Принципы

- Разделять `admin` и `client` API.
- Делать персональное предложение отдельной сущностью `offer_run`, а не вычислять его "на лету" в каждом запросе.
- Хранить выбор клиента отдельной сущностью `selection`.
- Все бюджетные инварианты проверять на сервере в транзакции.
- Все операции подтверждения делать идемпотентными.
- Для объяснимости возвращать не только результат, но и `reason_codes`.

## Основные сущности

- `category`: управляемая категория кэшбэка.
- `category_rule`: правила eligibility, аудитории, диапазона ставок, fallback-сценарии.
- `budget`: бюджет категории, глобальный бюджет, текущие резервы и факт списания.
- `offer_run`: результат расчёта персонального предложения на период.
- `offer_item`: конкретная категория внутри предложения с рекомендованной ставкой и объяснением.
- `selection`: выбор пользователя в механике.
- `progress`: прогресс по начислениям, миссиям, бустам, лимитам.
- `ledger_entry`: формальный журнал резервирования и списания бюджета.
- `audit_event`: аудит действий админа, ML-решения и клиентских подтверждений.

## Базовые рекомендации по URL

- Версионирование через `/api/v1`.
- Админские маршруты через `/api/v1/admin/...`.
- Клиентские маршруты через `/api/v1/client/...`.
- ML/engine действия не прятать в generic `/run`, лучше выделять как расчёт оффера.

## Admin API

### Categories

#### `GET /api/v1/admin/categories`

Список категорий с фильтрами.

Параметры:

- `status=draft|active|paused|archived`
- `audience_id`
- `cursor`
- `limit`

Ответ:

- список категорий
- budget summary
- active rules count

#### `POST /api/v1/admin/categories`

Создание категории.

Тело:

```json
{
  "name": "Restaurants",
  "subtitle": "Кэшбэк в кафе и ресторанах",
  "icon_key": "utensils",
  "status": "draft",
  "rate_min": 0.03,
  "rate_max": 0.10,
  "fallback_mode": "waitlist",
  "audience": {
    "segment_ids": ["mass", "young"]
  }
}
```

#### `GET /api/v1/admin/categories/{category_id}`

Карточка категории.

#### `PATCH /api/v1/admin/categories/{category_id}`

Изменение метаданных, диапазона ставки, статуса, аудитории.

Важно:

- нельзя поставить `rate_min > rate_max`
- нельзя активировать категорию без бюджета и правил fallback

#### `GET /api/v1/admin/categories/{category_id}/history`

История изменений категории.

#### `POST /api/v1/admin/categories/{category_id}/activate`

Явная активация категории после проверок.

#### `POST /api/v1/admin/categories/{category_id}/pause`

Приостановка выдачи новых офферов.

### Rules

#### `GET /api/v1/admin/rules`

Список правил с фильтрацией по категории, механике и статусу.

#### `POST /api/v1/admin/rules`

Создание правила назначения.

Тело:

```json
{
  "category_id": "cat_123",
  "priority": 100,
  "status": "active",
  "period": {
    "from": "2026-03-01T00:00:00Z",
    "to": "2026-03-31T23:59:59Z"
  },
  "eligibility": {
    "min_turnover_30d": 10000,
    "excluded_mcc": ["4829"]
  },
  "pricing": {
    "target_cpa": 0.25,
    "max_expected_cost_per_user": 300
  },
  "mechanic": {
    "type": "package",
    "slots": 3
  }
}
```

#### `GET /api/v1/admin/rules/{rule_id}`

#### `PATCH /api/v1/admin/rules/{rule_id}`

#### `POST /api/v1/admin/rules/{rule_id}/simulate`

Dry-run по сегменту: сколько пользователей eligible, какой ожидаемый cost, где риски по бюджету.

### Budgets

#### `GET /api/v1/admin/budgets`

Сводка:

- глобальный бюджет
- бюджеты категорий
- reserved
- spent
- available
- utilization_pct

#### `PUT /api/v1/admin/budgets/global`

Установка или изменение глобального бюджета периода.

#### `PUT /api/v1/admin/categories/{category_id}/budget`

Изменение бюджета категории.

Тело:

```json
{
  "period_id": "2026-03",
  "limit_amount": 5000000,
  "currency": "RUB",
  "reserve_policy": {
    "mode": "hard_cap",
    "safety_buffer_pct": 10
  }
}
```

#### `GET /api/v1/admin/categories/{category_id}/budget`

Детали бюджета категории.

#### `GET /api/v1/admin/categories/{category_id}/ledger`

Журнал резервов, списаний, освобождений.

### Offer calculation and control

#### `POST /api/v1/admin/offers/runs`

Запуск батчевого расчёта офферов.

Тело:

```json
{
  "period_id": "2026-03",
  "segment_id": "mass",
  "dry_run": false,
  "control_policy": {
    "type": "quota_ranker",
    "objective": "gmv_uplift_minus_cashback_cost"
  }
}
```

Ответ:

- `run_id`
- статус запуска
- сколько пользователей обработано
- сколько категорий распределено
- сколько бюджета зарезервировано

#### `GET /api/v1/admin/offers/runs/{run_id}`

Статус расчёта и агрегированные метрики.

#### `GET /api/v1/admin/offers/runs/{run_id}/decisions`

Объяснимость:

- почему категория назначена
- почему не назначена
- какой budget gate сработал
- какая модель/версия использовалась

### Audit

#### `GET /api/v1/admin/audit`

Аудит действий по фильтрам:

- actor
- entity_type
- entity_id
- action
- from/to

#### `GET /api/v1/admin/audit/{event_id}`

Полная запись события.

## Client API

### Personal offer

#### `POST /api/v1/client/offers:calculate`

Синхронный или асинхронный расчёт предложения для одного клиента. Хорош для демо и E2E.

Тело:

```json
{
  "period_id": "2026-03",
  "customer_id": "u_123",
  "mode": "interactive"
}
```

Ответ:

```json
{
  "offer_id": "offer_001",
  "status": "ready",
  "mechanic": {
    "type": "package",
    "slots_total": 3,
    "slots_required": 3
  },
  "items": [
    {
      "category_id": "cat_restaurants",
      "title": "Рестораны",
      "subtitle": "До 10% в марте",
      "rate": 0.08,
      "rate_range": {
        "min": 0.03,
        "max": 0.10
      },
      "expected_value": 420,
      "explanation": [
        "Вы часто тратите в этой категории",
        "Категория доступна в вашем пакете"
      ],
      "availability": {
        "status": "available",
        "reason_codes": []
      }
    }
  ],
  "budget_notice": {
    "soft_warning": false,
    "message": null
  }
}
```

#### `GET /api/v1/client/offers/current`

Текущее актуальное предложение клиента.

#### `GET /api/v1/client/offers/{offer_id}`

Детали оффера и его статуса.

### Interaction and selection

#### `POST /api/v1/client/selections`

Создание или подтверждение выбора.

Заголовки:

- `Idempotency-Key: <uuid>`

Тело:

```json
{
  "offer_id": "offer_001",
  "customer_id": "u_123",
  "selected_category_ids": ["cat_restaurants", "cat_travel", "cat_fuel"],
  "mechanic_context": {
    "type": "package",
    "risk_mode": "balanced"
  }
}
```

Сервер обязан:

- проверить, что оффер актуален
- проверить число слотов
- проверить доступность категорий на момент подтверждения
- атомарно зарезервировать бюджет
- вернуть fallback, если бюджет закончился между экраном выбора и подтверждением

#### `GET /api/v1/client/selections/current`

Текущий подтверждённый выбор.

#### `GET /api/v1/client/selections/{selection_id}`

Детали выбора, включая reserved budget snapshot.

#### `POST /api/v1/client/selections/{selection_id}:reconfirm`

Повторное подтверждение при возврате пользователя или смене механики.

#### `POST /api/v1/client/selections/{selection_id}:cancel`

Отмена до дедлайна, если продуктовая механика это позволяет.

### Progress

#### `GET /api/v1/client/progress`

Текущий прогресс клиента.

Ответ:

- выбранные категории
- накопленный кэшбэк
- прогноз до конца периода
- прогресс по миссиям/бустам
- статус лимитов

#### `GET /api/v1/client/progress/transactions`

Список транзакций, повлиявших на начисление.

#### `GET /api/v1/client/progress/accruals`

История начислений и статусы `pending|confirmed|reversed`.

### Transparency

#### `GET /api/v1/client/explanations/offers/{offer_id}`

Человекочитаемое объяснение:

- почему показаны именно эти категории
- что влияет на размер ставки
- почему что-то недоступно

#### `GET /api/v1/client/explanations/selections/{selection_id}`

Что именно зафиксировано и какие ограничения действуют после подтверждения.

## Системные API

### Audit and events

#### `POST /api/v1/internal/events/transactions-posted`

Приём событий транзакций для расчёта прогресса и фактического cashback cost.

#### `POST /api/v1/internal/events/period-closed`

Закрытие периода, финализация ledger и архив.

### ML / scoring

Если ML будет отдельным сервисом, лучше выносить его за публичный API.

Внутренние ручки:

- `POST /internal/ml/score-customer`
- `POST /internal/ml/estimate-category-cost`
- `POST /internal/ml/explain-offer`

## Обязательные серверные инварианты

### Бюджеты

- `spent + reserved <= category_budget_limit`
- `global_spent + global_reserved <= global_budget_limit`, если глобальный бюджет включён
- резерв должен создаваться при подтверждении выбора, а не только при фактической трате
- при изменении бюджета вниз система должна уметь блокировать новые подтверждения, не ломая старые

### Ставки

- `rate_min <= assigned_rate <= rate_max`
- ставка в оффере фиксируется снапшотом на момент подтверждения
- при возврате пользователя после дедлайна оффер должен быть пересчитан, а не молча переиспользован

### Идемпотентность

- `POST /client/selections`
- `POST /client/selections/{selection_id}:reconfirm`
- `POST /admin/offers/runs`

Для каждого такого вызова хранить:

- `idempotency_key`
- hash тела запроса
- итоговый status code
- итоговый response body

### Повторные действия и гонки

- один клиент не может подтвердить два активных выбора на один и тот же период
- при конкурентном подтверждении нужен optimistic lock или `SELECT ... FOR UPDATE`
- списание из бюджета делается только в транзакции с ledger entry

## Резервный сценарий при исчерпании бюджета

Лучший практический вариант: явный `fallback_mode` на уровне категории и общий ответ сервера с reason code.

Варианты:

- `waitlist`: категория недоступна, пользователь видит причину и может выбрать альтернативу
- `downgrade_rate`: можно выдать пониженный процент в допустимом диапазоне
- `substitute_category`: сервер предлагает замену из backup-списка
- `locked_progress_only`: категория больше не доступна для новых выборов, но старые начисления продолжают жить

Пример ответа:

```json
{
  "code": "BUDGET_EXHAUSTED",
  "message": "Лимит категории исчерпан",
  "fallback": {
    "mode": "substitute_category",
    "replacement_category_id": "cat_grocery"
  }
}
```

## Что лучше сделать в первой версии

Для MVP, который хорошо выглядит на защите, достаточно следующего набора:

- `GET/POST/PATCH /api/v1/admin/categories`
- `GET/POST/PATCH /api/v1/admin/rules`
- `GET/PUT /api/v1/admin/categories/{category_id}/budget`
- `POST /api/v1/admin/offers/runs`
- `GET /api/v1/admin/offers/runs/{run_id}`
- `GET /api/v1/admin/audit`
- `POST /api/v1/client/offers:calculate`
- `GET /api/v1/client/offers/current`
- `POST /api/v1/client/selections`
- `GET /api/v1/client/selections/current`
- `GET /api/v1/client/progress`

Это уже покрывает весь E2E-маршрут:

- админ настраивает категорию, правило и бюджет
- запускается персональный расчёт
- клиент видит предложение
- клиент делает выбор
- сервер резервирует бюджет
- клиент видит прогресс
- админ меняет бюджет
- система корректно ограничивает новые подтверждения

## Рекомендуемый HTTP-стиль ошибок

Использовать единый формат:

```json
{
  "code": "BUDGET_LIMIT_EXCEEDED",
  "message": "Невозможно подтвердить выбор: превышен бюджет категории",
  "trace_id": "01HQ...",
  "details": {
    "category_id": "cat_restaurants",
    "available_budget": 1200,
    "required_reserve": 1500
  }
}
```

Статусы:

- `400` некорректный запрос
- `401` пользователь не аутентифицирован
- `403` нет доступа
- `404` сущность не найдена
- `409` конфликт состояния, duplicate confirmation, stale offer
- `422` нарушение бизнес-правил

## Почему такая схема хороша

- она прозрачно отделяет управление, расчёт, выбор и прогресс
- позволяет показать доказуемый бюджетный контроль
- поддерживает расширение механик без перелома базовой модели
- даёт понятный E2E для демо и защиты
