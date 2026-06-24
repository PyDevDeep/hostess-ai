from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import aiosqlite

from backend.config import get_settings


@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[aiosqlite.Connection]:
    settings = get_settings()
    async with aiosqlite.connect(settings.database_url) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA foreign_keys=ON;")
        yield db
