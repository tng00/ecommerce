from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.db import async_session_maker
from typing import AsyncGenerator
from sqlalchemy import text


async def run_sql_script(db: AsyncSession, script_path: str):
    with open(script_path, 'r') as file:
        sql_script = file.read()

    await db.execute(text(sql_script))
    await db.commit()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session