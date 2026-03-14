from asyncpg import UniqueViolationError
from database.database import Database


async def get_admin_by_id(admin_id: int) -> dict | None:
    async with Database() as db:
        row = await db.execute(
            """
            SELECT admin_id, main_admin, login, approved
            FROM admin_users
            WHERE admin_id = $1
            """,
            (admin_id,),
        )
    return dict(row) if row else None


async def get_admin_by_login(login: str) -> dict | None:
    if not login or not isinstance(login, str):
        return None
    login = login.strip()
    if not login:
        return None
    async with Database() as db:
        row = await db.execute(
            """
            SELECT admin_id, main_admin, login, password, approved
            FROM admin_users
            WHERE login = $1
            """,
            (login,),
        )
    return dict(row) if row else None


async def ensure_main_admin(login: str, password: str) -> None:
    """
    Гарантирует наличие главного админа.

    Если таблицы admin_users ещё нет (например, init.sql не применился),
    не падаем при старте сервера, а просто логируем предупреждение.
    """
    try:
        await create_main_admin(login, password)
    except Exception as e:
        msg = str(e)
        if "UndefinedTableError" in msg or 'relation "admin_users" does not exist' in msg:
            from config import logger
            logger.warning("Таблица admin_users отсутствует, пропускаю ensure_main_admin: %s", e)
            return
        raise


async def create_main_admin(login: str, password: str) -> dict | None:
    async with Database() as db:
        row = await db.execute(
            "SELECT admin_id FROM admin_users WHERE main_admin = TRUE",
            (),
        )
        if row:
            return None

        row = await db.execute(
            """
            INSERT INTO admin_users (main_admin, login, password, approved)
            VALUES (TRUE, $1, $2, TRUE)
            RETURNING admin_id, main_admin, login, password, approved
            """,
            (login, password),
        )
    return dict(row) if row else None


async def create_admin(login: str, password: str) -> dict | None:
    login = (login or "").strip()
    password = (password or "").strip()
    if not login or not password:
        return None
    async with Database() as db:
        try:
            await db.execute(
                """
                INSERT INTO admin_users (main_admin, login, password, approved)
                VALUES (FALSE, $1, $2, FALSE)
                """,
                (login, password),
            )
        except UniqueViolationError:
            return None
    return await get_admin_by_login(login)


async def authenticate_admin(login: str, password: str) -> dict | None:
    async with Database() as db:
        row = await db.execute(
            """
            SELECT admin_id, main_admin, login, password, approved
            FROM admin_users
            WHERE login = $1 AND password = $2
            """,
            (login, password),
        )
    return dict(row) if row else None


async def approve_admin(main_login: str, main_password: str, admin_id: int) -> dict | None:
    main_admin = await authenticate_admin(main_login, main_password)
    if not main_admin or not main_admin.get("main_admin"):
        return None

    return await set_admin_approved(admin_id)


async def set_admin_approved(admin_id: int) -> dict | None:
    async with Database() as db:
        await db.execute(
            "UPDATE admin_users SET approved = TRUE WHERE admin_id = $1", (admin_id,),)
    return await get_admin_by_id(admin_id)


async def list_pending_admins() -> list[dict]:
    """Список заявок на админа (main_admin = FALSE, approved = FALSE). Только для супер-админа."""
    async with Database() as db:
        rows = await db.execute_all(
            """
            SELECT admin_id, login
            FROM admin_users
            WHERE main_admin = FALSE AND approved = FALSE
            ORDER BY admin_id
            """,
            (),
        )
    return rows or []


async def delete_pending_admin(admin_id: int) -> bool:
    async with Database() as db:
        await db.execute(
            """
            DELETE FROM admin_users
            WHERE admin_id = $1 AND main_admin = FALSE AND approved = FALSE
            """,(admin_id,))
    
