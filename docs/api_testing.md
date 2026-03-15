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
