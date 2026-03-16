"""Единая точка инициализации приложения: БД, миграции, начальные данные, главный админ."""
import os

from config import logger
from database.functions import (
    init_db,
    ensure_users_from_csv,
    ensure_selections_user_id_column,
    ensure_selections_idempotency_key_column,
    ensure_selections_amount_columns,
    ensure_selection_idempotency_requests_table,
    ensure_categories_from_csv,
    ensure_categories_status_column,
    ensure_categories_icon_url_column,
    ensure_categories_unique_name_constraint,
    ensure_category_creation_idempotency_requests_table,
)
from functions import admin_users as admin_users_fns


async def run_startup() -> None:
    """Выполняет все шаги старта: БД, главный админ, загрузка CSV, миграции колонок."""
    await init_db()
    main_login = os.environ.get("MAIN_ADMIN_LOGIN", "admin")
    main_password = os.environ.get("MAIN_ADMIN_PASSWORD", "admin")
    await admin_users_fns.ensure_main_admin(main_login, main_password)
    logger.info("Главный админ создан.")
    await ensure_users_from_csv()
    await ensure_categories_from_csv()
    await ensure_selections_user_id_column()
    await ensure_selections_idempotency_key_column()
    await ensure_selections_amount_columns()
    await ensure_selection_idempotency_requests_table()
    await ensure_categories_status_column()
    await ensure_categories_icon_url_column()
    await ensure_categories_unique_name_constraint()
    await ensure_category_creation_idempotency_requests_table()
