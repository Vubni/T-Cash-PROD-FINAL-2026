from database.database import Database


async def get_admin_by_login(login: str) -> dict | None:
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
    await create_main_admin(login, password)


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
    existing = await get_admin_by_login(login)
    if existing is not None:
        return None
    async with Database() as db:
        row = await db.execute(
            """
            INSERT INTO admin_users (main_admin, login, password, approved)
            VALUES (FALSE, $1, $2, FALSE)
            RETURNING admin_id, main_admin, login, password, approved
            """,
            (login, password),
        )
    return dict(row) if row else None


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
    """Главный админ одобряет обычного админа."""
    main_admin = await authenticate_admin(main_login, main_password)
    if not main_admin or not main_admin.get("main_admin"):
        return None

    async with Database() as db:
        row = await db.execute(
            """
            UPDATE admin_users
            SET approved = TRUE
            WHERE admin_id = $1
            RETURNING admin_id, main_admin, login, password, approved
            """,
            (admin_id,),
        )
    return dict(row) if row else None

