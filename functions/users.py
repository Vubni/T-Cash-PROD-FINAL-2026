"""Пользователи: вспомогательные функции работы с users."""

import os

from config import logger
from database.database import Database


async def user_exists(user_id: str) -> bool:
    """Проверка существования пользователя по user_id."""
    async with Database() as db:
        row = await db.execute(
            "SELECT 1 FROM users WHERE user_id = $1",
            (user_id,),
        )
    return row is not None