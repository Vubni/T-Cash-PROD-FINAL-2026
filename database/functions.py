import csv
import os

from config import logger
from database.database import Database

BIGINT_MIN = -(2**63)
BIGINT_MAX = 2**63 - 1


def _is_valid_user_id(value: str) -> bool:
    """Проверяет, что строка является валидным целым в диапазоне BIGINT (user_id)."""
    if not value or not value.strip():
        return False
    try:
        n = int(value.strip())
        return BIGINT_MIN <= n <= BIGINT_MAX
    except (ValueError, TypeError, AttributeError):
        return False


async def init_db():
    """
    Базовая инициализация БД.

    Схема (CREATE TABLE ...) задаётся в postgres/init.sql и создаётся на стороне Postgres.
    Здесь ничего дополнительно не создаём, оставляем заглушку на случай будущих миграций.
    """
    return None


async def ensure_users_from_csv(csv_path: str = "data/users.csv") -> None:
    if not os.path.exists(csv_path):
        logger.warning(f"Файл с пользователями не найден: {csv_path}")
        return

    to_insert: list[tuple[int]] = []

    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header_skipped = False
            for row in reader:
                if not row:
                    continue
                if not header_skipped:
                    header_skipped = True
                    if row[0].strip().lower() != "user_id":
                        raw = row[0].strip()
                        if raw and _is_valid_user_id(raw):
                            to_insert.append((int(raw),))
                        elif raw:
                            logger.warning("Пропуск невалидного user_id в CSV (ожидается целое BIGINT): %r", raw)
                    continue
                raw = row[0].strip()
                if not raw:
                    continue
                if not _is_valid_user_id(raw):
                    logger.warning("Пропуск невалидного user_id в CSV (ожидается целое BIGINT): %r", raw)
                    continue
                to_insert.append((int(raw),))
    except OSError as e:
        logger.error(f"Не удалось прочитать файл пользователей {csv_path}: {e}")
        return

    if not to_insert:
        logger.info(f"В файле {csv_path} не найдено валидных пользователей для импорта.")
        return

    try:
        async with Database() as db:
            existing = await db.execute("SELECT 1 FROM users LIMIT 1")
            if existing is not None:
                logger.info("Таблица users уже содержит записи, импорт из CSV пропущен.")
                return

            await db.executemany(
                "INSERT INTO users (user_id) VALUES ($1::bigint) ON CONFLICT (user_id) DO NOTHING",
                to_insert,
            )
            logger.info(f"Импортировано пользователей из CSV: {len(to_insert)}")
    except Exception as e:
        msg = str(e)
        if (
            "UndefinedTableError" in msg
            or 'relation \"users\" does not exist' in msg
            or "DataError" in msg
            or "invalid input for query argument" in msg
        ):
            logger.warning("Не удалось импортировать пользователей из CSV, пропускаю ensure_users_from_csv: %s", e)
            return
        raise


async def ensure_categories_from_csv(csv_path: str = "data/categories.csv") -> None:
    logger.info(f"Начинаю загрузку категорий из {csv_path}")
    
    if not os.path.exists(csv_path):
        logger.warning(f"Файл с категориями не найден: {csv_path}")
        return

    rows: list[tuple[str, str, int]] = []
    debug_counter = 0

    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header_skipped = False
            header = {}
            
            for row in reader:
                if not row:
                    continue
                if not header_skipped:
                    # Определяем индексы колонок
                    for i, col in enumerate(row):
                        header[col.strip()] = i
                    header_skipped = True
                    continue
                if len(row) < 5:
                    logger.warning(f"Пропуск строки с недостаточным количеством колонок ({len(row)}): {row}")
                    continue
                    
                category_id = row[header.get('category_id', 0)].strip()
                name = row[header.get('name', 1)].strip()
                budget_str = row[header.get('budget_amount', 4)].strip()
                
                if not category_id or not name:
                    continue
                    
                try:
                    budget = int(budget_str) if budget_str else 0
                except ValueError:
                    budget = 0
                    
                # Отладка для первых 10 строк
                if debug_counter < 10:
                    logger.info(f"Category: {category_id}, Budget str: '{budget_str}', Budget int: {budget}")
                    debug_counter += 1
                    
                rows.append((category_id, name, budget))
    except OSError as e:
        logger.error(f"Не удалось прочитать файл категорий {csv_path}: {e}")
        return

    if not rows:
        logger.info(f"В файле {csv_path} не найдено валидных категорий для импорта.")
        return

    DEFAULT_RULE_ID = "a0000000-0000-0000-0000-000000000001"

    params: list[tuple] = []
    for category_id, name, budget in rows:
        params.append(
            (
                category_id,
                name,
                name,
                budget,
                5,
                15,
                DEFAULT_RULE_ID,
            )
        )

    async with Database() as db:
        await db.executemany(
            """
            INSERT INTO categories (
                category_id,
                name,
                subtitle,
                budget_amount,
                rate_min,
                rate_max,
                rule_id
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7
            )
            ON CONFLICT (category_id) DO UPDATE SET
                name = EXCLUDED.name,
                subtitle = EXCLUDED.subtitle,
                budget_amount = EXCLUDED.budget_amount,
                rate_min = EXCLUDED.rate_min,
                rate_max = EXCLUDED.rate_max,
                rule_id = EXCLUDED.rule_id
            """,
            params,
        )
        logger.info(f"Импортировано категорий из CSV: {len(params)}")