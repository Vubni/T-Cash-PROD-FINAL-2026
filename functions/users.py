"""Пользователи: список, получение по id, проверка существования."""

from database.database import Database


async def list_users() -> list[dict]:
    """Список всех пользователей (user_id, name)."""
    async with Database() as db:
        rows = await db.execute_all(
            "SELECT user_id, name FROM users ORDER BY name"
        ) or []
    return [dict(r) for r in rows]


async def get_user(user_id: str) -> dict | None:
    """Один пользователь по user_id."""
    async with Database() as db:
        row = await db.execute(
            "SELECT user_id, name FROM users WHERE user_id = $1",
            (user_id,),
        )
    return dict(row) if row else None


async def user_exists(user_id: str) -> bool:
    """Проверка существования пользователя по user_id."""
    async with Database() as db:
        row = await db.execute(
            "SELECT 1 FROM users WHERE user_id = $1",
            (user_id,),
        )
    return row is not None
