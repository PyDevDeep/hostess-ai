from backend.db.database import get_db_connection
from backend.models.analytics import AnalyticsRecord


class AnalyticsRepository:
    async def save_record(self, record: AnalyticsRecord) -> None:
        async with get_db_connection() as db:
            await db.execute(
                """
                INSERT INTO analytics (id, session_id, sentiment, failure_reason, summary, raw_transcript, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.session_id,
                    record.sentiment,
                    record.failure_reason,
                    record.summary,
                    record.raw_transcript,
                    record.created_at,
                ),
            )
            await db.commit()
