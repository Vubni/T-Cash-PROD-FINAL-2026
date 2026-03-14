"""Пользователи: вспомогательные функции работы с users."""

from config import logger
from database.database import Database


async def user_exists(user_id: str) -> bool:
    """
    Проверка существования пользователя по user_id (UUID).

    Если таблицы users нет (например, локальная БД без полной схемы),
    возвращаем True, чтобы не блокировать работу клиентских ручек.
    """
    try:
        async with Database() as db:
            row = await db.execute(
                "SELECT 1 FROM users WHERE user_id = $1::uuid",
                (user_id,),
            )
        return row is not None
    except Exception as e:
        msg = str(e)
        if "UndefinedTableError" in msg or 'relation \"users\" does not exist' in msg:
            logger.warning("Таблица users отсутствует, user_exists(%s) -> True: %s", user_id, e)
            return True
        raise