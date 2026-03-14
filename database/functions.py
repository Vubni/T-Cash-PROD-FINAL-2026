import csv
import os

from config import logger
from database.database import Database


async def init_db():
    async with Database() as db:
        try:
            ...
        except Exception as e:
            print(f"Ошибка при создании таблицы: {e}")


async def ensure_users_from_csv(csv_path: str = "data/users.csv") -> None:
    if not os.path.exists(csv_path):
        logger.warning(f"Файл с пользователями не найден: {csv_path}")
        return

    async with Database() as db:
        existing = await db.execute("SELECT 1 FROM users LIMIT 1")
        if existing is not None:
            logger.info("Таблица users уже содержит записи, импорт из CSV пропущен.")
            return

        to_insert: list[tuple[int]] = []

        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row:
                        continue
                    raw_id = row[0].strip()
                    if not raw_id:
                        continue
                    try:
                        value = int(raw_id)
                    except ValueError:
                        logger.warning(f"Пропускаю некорректный user_id (не bigint) из CSV: {raw_id!r}")
                        continue
                    to_insert.append((value,))
        except OSError as e:
            logger.error(f"Не удалось прочитать файл пользователей {csv_path}: {e}")
            return

        if not to_insert:
            logger.info(f"В файле {csv_path} не найдено валидных пользователей для импорта.")
            return

        await db.executemany(
            "INSERT INTO users (user_id) VALUES ($1) ON CONFLICT (user_id) DO NOTHING",
            to_insert,
        )
        logger.info(f"Импортировано пользователей из CSV: {len(to_insert)}")