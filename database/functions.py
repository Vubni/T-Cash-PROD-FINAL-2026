import csv
import os

from config import logger
from database.database import Database


async def init_db():
    """
    Базовая инициализация БД.

    Схема (CREATE TABLE ...) задаётся в postgres/init.sql и создаётся на стороне Postgres.
    Здесь ничего дополнительно не создаём, оставляем заглушку на случай будущих миграций.
    """
    return None


async def ensure_selections_user_id_column() -> None:
    """Добавляет колонку user_id в selections, если её нет (совместимость со старыми БД)."""
    try:
        async with Database() as db:
            await db.execute(
                "ALTER TABLE selections ADD COLUMN IF NOT EXISTS user_id UUID NULL REFERENCES users(user_id)",
                (),
            )
    except Exception as e:
        logger.warning("Колонка selections.user_id: %s", e)


async def ensure_users_from_csv(csv_path: str = "data/users.csv") -> None:
    if not os.path.exists(csv_path):
        logger.warning(f"Файл с пользователями не найден: {csv_path}")
        return

    to_insert: list[tuple[str]] = []

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
                        if raw:
                            to_insert.append((raw,))
                    continue
                raw = row[0].strip()
                if not raw:
                    continue
                to_insert.append((raw,))
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
                "INSERT INTO users (user_id) VALUES ($1::uuid) ON CONFLICT (user_id) DO NOTHING",
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
    if not os.path.exists(csv_path):
        logger.warning(f"Файл с категориями не найден: {csv_path}")
        return

    rows: list[tuple[str, str]] = []

    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header_skipped = False
            for row in reader:
                if not row:
                    continue
                if not header_skipped:
                    header_skipped = True
                    continue
                if len(row) < 2:
                    continue
                category_id = row[0].strip()
                name = row[1].strip()
                if not category_id or not name:
                    continue
                rows.append((category_id, name))
    except OSError as e:
        logger.error(f"Не удалось прочитать файл категорий {csv_path}: {e}")
        return

    if not rows:
        logger.info(f"В файле {csv_path} не найдено валидных категорий для импорта.")
        return

    DEFAULT_RULE_ID = "a0000000-0000-0000-0000-000000000001"

    params: list[tuple] = []
    for category_id, name in rows:
        params.append(
            (
                category_id,
                name,
                name,
                0,
                ["mass"],
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
                audience_segments,
                rule_id
            )
            VALUES (
                $1, $2, $3, $4, $5, $6
            )
            ON CONFLICT (category_id) DO NOTHING
            """,
            params,
        )
    logger.info(f"Импортировано категорий из CSV: {len(params)}")