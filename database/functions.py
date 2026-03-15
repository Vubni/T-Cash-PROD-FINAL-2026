import csv
import os

from config import logger
from database.database import Database


_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _data_path(filename: str) -> str:
    """Путь к файлу в data/ относительно корня backend."""
    return os.path.join(_BACKEND_ROOT, "data", filename)


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
                "ALTER TABLE selections ADD COLUMN IF NOT EXISTS user_id BIGINT NULL REFERENCES users(user_id)",
                (),
            )
    except Exception as e:
        logger.warning("Колонка selections.user_id: %s", e)


_BIGINT_MIN = -(2**63)
_BIGINT_MAX = 2**63 - 1


def _parse_user_id(raw: str) -> int | None:
    """Парсит строку в user_id (BIGINT). Возвращает int или None при невалидном значении."""
    s = raw.strip()
    if not s:
        return None
    try:
        n = int(s)
        if _BIGINT_MIN <= n <= _BIGINT_MAX:
            return n
    except ValueError:
        pass
    return None


async def ensure_users_from_csv(csv_path: str | None = None) -> None:
    if csv_path is None:
        csv_path = _data_path("users.csv")
    if not os.path.exists(csv_path):
        logger.warning("Файл с пользователями не найден: %s", csv_path)
        return

    to_insert: list[tuple[int]] = []
    skipped = 0

    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header_skipped = False
            for row in reader:
                if not row:
                    continue
                if not header_skipped:
                    header_skipped = True
                    continue
                user_id = _parse_user_id(row[0])
                if user_id is None:
                    skipped += 1
                    continue
                to_insert.append((user_id,))
    except OSError as e:
        logger.error("Не удалось прочитать файл пользователей %s: %s", csv_path, e)
        return

    if skipped:
        logger.warning("Пропущено невалидных строк в %s: %d", csv_path, skipped)
    if not to_insert:
        logger.info("В файле %s не найдено валидных пользователей для импорта.", csv_path)
        return

    try:
        async with Database() as db:
            existing = await db.execute("SELECT 1 FROM users LIMIT 1")
            if existing is not None:
                logger.info("Таблица users уже содержит записи, импорт из CSV пропущен.")
                return

            batch_size = 5000
            for i in range(0, len(to_insert), batch_size):
                batch = to_insert[i : i + batch_size]
                await db.executemany(
                    "INSERT INTO users (user_id) VALUES ($1::bigint) ON CONFLICT (user_id) DO NOTHING",
                    batch,
                )
            logger.info("Импортировано пользователей из CSV: %d", len(to_insert))
    except Exception as e:
        msg = str(e)
        if (
            "UndefinedTableError" in msg
            or 'relation "users" does not exist' in msg
            or "DataError" in msg
            or "invalid input for query argument" in msg
        ):
            logger.warning(
                "Не удалось импортировать пользователей из CSV, пропускаю ensure_users_from_csv: %s",
                e,
            )
            return
        raise


async def ensure_categories_from_csv(csv_path: str | None = None) -> None:
    if csv_path is None:
        csv_path = _data_path("categories.csv")
    if not os.path.exists(csv_path):
        logger.warning("Файл с категориями не найден: %s", csv_path)
        return

    # CSV: category_id, name, subtitle, icon_key, budget_amount, audience_segments, rule_id, status, ...
    rows: list[tuple[str, str, str, int, str]] = []

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
                subtitle = row[2].strip() if len(row) > 2 else name
                budget_amount = 0
                if len(row) > 4 and row[4].strip():
                    try:
                        budget_amount = max(0, int(float(row[4].strip())))
                    except (ValueError, TypeError):
                        pass
                rule_id = row[6].strip() if len(row) > 6 and row[6].strip() else "a0000000-0000-0000-0000-000000000001"
                rows.append((category_id, name, subtitle, budget_amount, rule_id))
    except OSError as e:
        logger.error(f"Не удалось прочитать файл категорий {csv_path}: {e}")
        return

    if not rows:
        logger.info(f"В файле {csv_path} не найдено валидных категорий для импорта.")
        return

    params: list[tuple] = []
    for category_id, name, subtitle, budget_amount, rule_id in rows:
        params.append(
            (
                category_id,
                name,
                subtitle,
                budget_amount,
                5,
                15,
                rule_id,
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
                rule_id = EXCLUDED.rule_id
            """,
            params,
        )
    logger.info(f"Импортировано/обновлено категорий из CSV: {len(params)}")