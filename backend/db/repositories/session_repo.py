import time
from typing import Any

from backend.db.database import get_db_connection
from backend.models.session import SessionStatus


class SessionRepository:
    async def create_session(self, session_id: str) -> None:
        async with get_db_connection() as db:
            await db.execute(
                "INSERT INTO sessions (id, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (session_id, SessionStatus.CONNECTING.value, time.time(), time.time()),
            )
            await db.commit()

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        async with (
            get_db_connection() as db,
            db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)) as cursor,
        ):
            row = await cursor.fetchone()
            if row and cursor.description:
                cols = [description[0] for description in cursor.description]
                return dict(zip(cols, row, strict=True))
            return None

    async def update_status(
        self, session_id: str, status: SessionStatus, hold_expires_at: float | None = None
    ) -> None:
        async with get_db_connection() as db:
            await db.execute(
                "UPDATE sessions SET status = ?, hold_expires_at = ?, updated_at = ? WHERE id = ?",
                (status.value, hold_expires_at, time.time(), session_id),
            )
            await db.commit()

    async def set_on_hold(
        self, session_id: str, date: str, time_str: str, guests: int, ttl_seconds: int
    ) -> None:
        hold_expires = time.time() + ttl_seconds
        async with get_db_connection() as db:
            await db.execute(
                """
                UPDATE sessions
                SET status = ?, date = ?, time = ?, guests = ?, hold_expires_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    SessionStatus.ON_HOLD.value,
                    date,
                    time_str,
                    guests,
                    hold_expires,
                    time.time(),
                    session_id,
                ),
            )
            await db.commit()

    async def get_expired_holds(self) -> list[str]:
        current_time = time.time()
        async with (
            get_db_connection() as db,
            db.execute(
                "SELECT id FROM sessions WHERE status = ? AND hold_expires_at < ?",
                (SessionStatus.ON_HOLD.value, current_time),
            ) as cursor,
        ):
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
