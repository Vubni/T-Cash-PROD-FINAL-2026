# Тестирование API (Insomnia / Postman)

## Токен пользователя для `POST /offers/run` и `POST /client/selection`

Эндпоинты `POST /api/v1/offers/run` и `POST /api/v1/client/selection` требуют **JWT пользователя** в заголовке:

```
Authorization: Bearer <token>
```

Если в заголовке указать буквально `Bearer user_token` или переменная не подставлена, сервер вернёт **401 Unauthorized** («Токен отсутствует, невалиден или истёк»).

### Как получить токен

1. Вызовите **GET** `/api/v1/users/{user_id}/auth`, например:
   - `GET {{baseUrl}}/api/v1/users/12345/auth`
2. В ответе 200 будет JSON:
   ```json
   { "user_id": 12345, "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." }
   ```
3. Скопируйте значение поля **`token`** — это и есть токен пользователя.

### Настройка в Insomnia

1. В **Environment** создайте переменную **`user_token`** (значение можно оставить пустым).
2. Выполните запрос **GET /api/v1/users/12345/auth** (или другой `user_id`).
3. Из ответа скопируйте значение `token` и вставьте в переменную **`user_token`** в Environment (или используйте в Insomnia функцию «Send and Set» / Response → Set Environment Variable, если настроена).
4. В запросах **POST /offers/run** и **POST /client/selection** в заголовке укажите:
   - **Name:** `Authorization`
   - **Value:** `Bearer {{ user_token }}`  
   Обратите внимание: подстановка переменной в Insomnia делается через **двойные фигурные скобки** `{{ user_token }}`. Если написать просто `user_token` без скобок, в запрос уйдёт строка «user_token», и сервер вернёт 401.

### Кратко

- Сначала один раз вызвать **GET /api/v1/users/{id}/auth** и сохранить `token` в переменную `user_token`.
- В клиентских запросах использовать заголовок: **`Authorization: Bearer {{ user_token }}`**.

---

## Переменная `category_id` для админских запросов по категории

Запросы вида **GET/PATCH/POST/DELETE** `/api/v1/admin/categories/{category_id}` требуют в пути **реальный UUID категории**. Если переменная `category_id` в Environment пустая или в URL указано буквально `category_id` без подстановки, сервер вернёт **404 Not Found**.

- В коллекции в Environment задана переменная **`category_id`** — подставьте в неё UUID существующей категории (например, из ответа **GET /admin/categories** или используйте уже заданные `category_id_1` … `category_id_5`).
- В URL запроса должно быть: `{{ baseUrl }}/api/v1/admin/categories/{{ category_id }}` (с двойными фигурными скобками).

---

## Как изменить статус категории

Используйте один из эндпоинтов (все с заголовком **Authorization: Bearer {{ admin_token }}**):

| Действие   | Метод | URL | Тело |
|------------|--------|-----|------|
| Запустить  | **POST** | `/api/v1/admin/categories/{{ category_id }}/run` | пустое |
| Приостановить | **POST** | `/api/v1/admin/categories/{{ category_id }}/pause` | пустое |
| Архивировать | **DELETE** | `/api/v1/admin/categories/{{ category_id }}/archive` | — |
| Любой статус | **PATCH** | `/api/v1/admin/categories/{{ category_id }}` | `{"status": "running"}` или `"paused"`, или `"archived"` |

В ответе 200 приходит объект категории с полем **`status`**.
