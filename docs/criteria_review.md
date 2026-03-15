# Проверка кода по критериям ТЗ / брифа

Источники: `README.md`, `docs/user_journey.md`, `docs/cashback_api.md` (раздел «Что лучше сделать в первой версии»).

---

## 1. API из README и user_journey

### 1.1 Categories — **выполнено**

- `GET` / `POST` /api/v1/admin/categories  
- `GET` / `PATCH` /api/v1/admin/categories/{category_id}  

**В коде:** все перечисленные маршруты есть в `server.py`, реализация в `api/categories.py`. Дополнительно есть icon, rule, run/pause, archive, audit по категории.

---

### 1.2 Rules — **не выполнено**

- `GET` / `POST` /api/v1/admin/rules  
- `GET` / `PATCH` /api/v1/admin/rules/{rule_id}  

**В коде:** отдельных эндпоинтов для rules нет. Правила создаются только через категорию:  
`POST /api/v1/admin/categories/{category_id}/rule` в `api/categories.py`.  
Таблица `rules` и миграции есть, отдельного CRUD API для правил — нет.

**Степень:** полностью отсутствует заявленный в README набор rules API.

---

### 1.3 Audit — **выполнено частично**

- В README и user_journey: **`GET /api/v1/admin/audit`** — общий журнал аудита.  
- В cashback_api: фильтры (actor, entity_type, entity_id, action, from/to).

**В коде:** реализован только аудит **по категории**:  
`GET /api/v1/admin/categories/{category_id}/audit` в `api/audit.py` (параметр `limit` 1–500).

**Не выполнено:**
- общего эндпоинта `GET /api/v1/admin/audit`;
- фильтров по actor, entity_type, entity_id, action, from/to.

**Степень:** сценарий «история изменений по одной категории» закрыт; общий аудит и фильтрация — нет.

---

### 1.4 offers/run — **выполнено**

- `POST /api/v1/offers/run` — расчёт категорий для клиента.

**В коде:** маршрут зарегистрирован, обработчик в `api/calculate.py`. Требуется JWT пользователя, возвращаются `items` и `already_selected_categories`.

---

### 1.5 Selection — **частично выполнено**

**GET selection**

- README / user_journey: **`GET /api/v1/client/selection/{selection_id}`** — получение выбора по id.

**В коде:** такого маршрута нет. Есть только `POST /api/v1/client/selection` (подтверждение выбора по телу и JWT).

**Степень:** не выполнено — клиент не может получить детали выбора по `selection_id`.

---

**POST selection (подтверждение)**

- README: **`GET` / `POST` /api/v1/client/selection/{selection_id}**, при подтверждении — заголовок **`Idempotency-Key`**.
- user_journey: подтверждение с `Idempotency-Key`.

**В коде:**
- Маршрут: `POST /api/v1/client/selection` — без `{selection_id}` в пути (другой контракт: выбор задаётся телом `category_ids`, пользователь — из JWT).
- Заголовок **Idempotency-Key** не читается и не используется; в `api/selection.py` и `functions/selection.py` обработки идемпотентности по ключу нет. В БД колонка `idempotency_key` в `selections` есть (в т.ч. в миграциях), но API её не заполняет.

**Степень:**  
- Формат эндпоинта отличается от ТЗ (нет selection_id в URL).  
- Критерий «Idempotency-Key при подтверждении выбора» — не выполнен.

---

## 2. Гарантии сервера (README)

### 2.1 Диапазоны ставок и лимиты — **выполнено**

- В `api/categories.py`: проверки `rate_min`/`rate_max` (в т.ч. `rate_min <= rate_max`), ограничения полей.  
- Лимиты пагинации (offset/limit) на списках.

### 2.2 Идемпотентность и защита от повторных действий — **не выполнено**

- Явно требуется: **Idempotency-Key при подтверждении выбора**.  
- В коде: не реализовано (см. п. 1.5).

### 2.3 Проверка бюджетных инвариантов на сервере — **частично**

- В категориях проверяется `budget_amount >= 0`, валидация полей.  
- Нет отдельного контура: резерв при подтверждении выбора, списание, ledger, проверки вида `reserved + spent <= budget`.  
- В user_journey и cashback_api это отнесено к «что ещё не доведено» (резервирование/списание в транзакции, движок budget control).

---

## 3. MVP из cashback_api.md («Что лучше сделать в первой версии»)

| Эндпоинт из списка | Статус в коде |
|--------------------|----------------|
| GET/POST/PATCH /api/v1/admin/categories | ✅ Есть (POST/PATCH + расширенный набор) |
| GET/POST/PATCH /api/v1/admin/rules | ❌ Нет отдельного API |
| GET/PUT /api/v1/admin/categories/{id}/budget | ⚠️ Бюджет входит в PATCH категории (`budget_amount`), отдельных GET/PUT budget — нет |
| POST /api/v1/admin/offers/runs | ⚠️ Есть POST /offers/run (одиночный расчёт), не батч runs |
| GET /api/v1/admin/offers/runs/{run_id} | ❌ Нет |
| GET /api/v1/admin/audit | ❌ Нет общего; есть только GET .../categories/{id}/audit |
| POST /api/v1/client/offers:calculate | ⚠️ По смыслу соответствует POST /offers/run (другой путь) |
| GET /api/v1/client/offers/current | ❌ Нет |
| POST /api/v1/client/selections | ✅ Есть как POST /client/selection |
| GET /api/v1/client/selections/current | ❌ Нет (нет и GET .../selection/{id}) |
| GET /api/v1/client/progress | ❌ Нет |

---

## 4. Итоговая таблица: что не выполнено или выполнено не полностью

| Критерий | Статус | Комментарий |
|----------|--------|-------------|
| Rules API (GET/POST/PATCH rules, rules/{id}) | ❌ Не выполнено | Отдельных эндпоинтов нет |
| GET /api/v1/admin/audit (общий аудит) | ❌ Не выполнено | Есть только аудит по category_id |
| GET /api/v1/client/selection/{selection_id} | ❌ Не выполнено | Маршрута нет |
| Idempotency-Key при подтверждении выбора | ❌ Не выполнено | Заголовок не обрабатывается |
| GET/PUT .../budget (отдельные ручки бюджета) | ⚠️ Частично | Бюджет только в PATCH категории |
| GET /admin/offers/runs/{run_id}, GET /client/offers/current, GET /client/progress | ❌ Не выполнено | В коде не реализованы |
| Полный бюджетный контур (резерв/списание/ledger) | ⚠️ Частично | Явно в ТЗ отнесено к «не доведено» |

---

## 5. Рекомендации по приоритетам

1. **Если нужно строго соответствовать README/user_journey:**  
   - Добавить **GET /api/v1/client/selection/{selection_id}** (или эквивалент «текущий выбор» по user из JWT).  
   - Реализовать **обработку Idempotency-Key** в POST подтверждения выбора (чтение заголовка, сохранение в `selections.idempotency_key`, возврат ранее сохранённого ответа при повторном запросе с тем же ключом).  
   - Добавить **GET /api/v1/admin/audit** (общий список с опциональными фильтрами entity_type, entity_id, limit и т.д.), при желании оставив существующий аудит по категории как дополнительный.

2. **Если нужен полный MVP из cashback_api:**  
   - Отдельный CRUD для rules;  
   - Отдельные эндпоинты budget и progress по списку из раздела «Что лучше сделать в первой версии».

3. **Совпадение с документацией:**  
   - Привести README в соответствие с фактическими маршрутами (audit по категории, selection без selection_id в пути) или реализовать недостающие маршруты — по выбору продукта.
