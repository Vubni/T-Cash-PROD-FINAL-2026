from database.database import Database
from aiohttp import web

async def init_db():
    async with Database() as db:
        try:
            ...
        except Exception as e:
            print(f"Ошибка при создании таблицы: {e}")