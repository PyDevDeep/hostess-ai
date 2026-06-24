from backend.db.database import get_db_connection


async def init_db() -> None:
    async with get_db_connection() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                status TEXT,
                date TEXT,
                time TEXT,
                guests INTEGER,
                name TEXT,
                phone TEXT,
                hold_expires_at REAL,
                created_at REAL,
                updated_at REAL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                sentiment TEXT,
                failure_reason TEXT,
                summary TEXT,
                raw_transcript TEXT,
                created_at REAL,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
        """)
        await db.commit()
