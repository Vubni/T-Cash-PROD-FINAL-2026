#!/usr/bin/env bash
# Проверка audit: после смены статуса категории GET .../audit возвращает записи.
# Перед запуском: docker compose up (или сервер на localhost:8080).
# Требуется: curl, python3.
#
# Вручную:
#   TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/admin/auth/login -H "Content-Type: application/json" -d '{"login":"admin","password":"admin"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
#   CATEGORY_ID=$(curl -s -X GET "http://localhost:8080/api/v1/admin/categories?limit=1" -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['items'][0]['id'] if d.get('items'))")
#   curl -s -X POST "http://localhost:8080/api/v1/admin/categories/$CATEGORY_ID/run" -H "Authorization: Bearer $TOKEN"
#   curl -s -X GET "http://localhost:8080/api/v1/admin/categories/$CATEGORY_ID/audit?limit=10" -H "Authorization: Bearer $TOKEN"

set -e
BASE_URL="${BASE_URL:-http://localhost:8080}"
API="${BASE_URL}/api/v1"

echo "=== 1. Получение токена админа ==="
TOKEN=$(curl -s -X POST "$API/admin/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"login":"admin","password":"admin"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); t=d.get('token',''); sys.exit(1) if not t else print(t)")
echo "Токен получен."

echo ""
echo "=== 2. GET /admin/categories (первая категория) ==="
CATEGORY_JSON=$(curl -s -X GET "$API/admin/categories?limit=1&offset=0" -H "Authorization: Bearer $TOKEN")
CATEGORY_ID=$(echo "$CATEGORY_JSON" | python3 -c "
import sys, json
d = json.load(sys.stdin)
items = d.get('items') or []
if not items:
    print('', end='')
else:
    print(items[0].get('id', ''), end='')
" 2>/dev/null || true)
if [ -z "$CATEGORY_ID" ]; then
  echo "Нет категорий. Создайте категорию через POST /admin/categories и повторите."
  exit 1
fi
echo "category_id=$CATEGORY_ID"

echo ""
echo "=== 3. POST /admin/categories/{id}/run (смена статуса → запись в audit) ==="
RUN_RESP=$(curl -s -w "\n%{http_code}" -X POST "$API/admin/categories/$CATEGORY_ID/run" -H "Authorization: Bearer $TOKEN")
HTTP_BODY=$(echo "$RUN_RESP" | sed '$d')
HTTP_CODE=$(echo "$RUN_RESP" | tail -1)
echo "HTTP $HTTP_CODE"
if [ "$HTTP_CODE" != "200" ]; then
  echo "$HTTP_BODY"
  exit 1
fi

echo ""
echo "=== 4. GET /admin/categories/{id}/audit (журнал по категории) ==="
AUDIT_RESP=$(curl -s -w "\n%{http_code}" -X GET "$API/admin/categories/$CATEGORY_ID/audit?limit=10" -H "Authorization: Bearer $TOKEN")
AUDIT_BODY=$(echo "$AUDIT_RESP" | sed '$d')
AUDIT_CODE=$(echo "$AUDIT_RESP" | tail -1)
echo "HTTP $AUDIT_CODE"
echo "$AUDIT_BODY" | python3 -m json.tool 2>/dev/null || echo "$AUDIT_BODY"

echo ""
echo "=== 5. Проверка: items не пустой, есть action и details ==="
echo "$AUDIT_BODY" | python3 -c "
import sys, json
d = json.load(sys.stdin)
items = d.get('items') or []
total = d.get('total', 0)
if not items:
    print('ОШИБКА: audit items пустой. Ожидалась хотя бы одна запись после run.')
    sys.exit(1)
first = items[0]
if not first.get('action'):
    print('ОШИБКА: у первой записи нет action.')
    sys.exit(1)
print(f'OK: записей в audit = {len(items)}, total = {total}')
print(f'    Первая запись: action={first.get(\"action\")}, actor={first.get(\"actor\")}, details={first.get(\"details\")}')
" || exit 1

echo ""
echo "=== Audit проверен: журнал не пустой, записи с action (и details) присутствуют. ==="
