import asyncio
import contextlib

import structlog

from backend.db.repositories.session_repo import SessionRepository
from backend.models.session import SessionStatus
from backend.services.n8n_client import N8nClient

logger = structlog.get_logger()


class SessionManager:
    def __init__(self, repo: SessionRepository, n8n_client: N8nClient) -> None:
        self.repo = repo
        self.n8n_client = n8n_client
        self._cleanup_task: asyncio.Task[None] | None = None

    async def start_cleanup_task(self) -> None:
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("session_cleanup_task_started")

    async def stop_cleanup_task(self) -> None:
        if self._cleanup_task:
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task
            logger.info("session_cleanup_task_stopped")

    async def _cleanup_loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(60)
                expired_ids = await self.repo.get_expired_holds()
                for session_id in expired_ids:
                    logger.info("releasing_expired_hold", session_id=session_id)
                    await self.repo.update_status(session_id, SessionStatus.FAILED, None)
                    await self.n8n_client.release_on_hold(session_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("session_cleanup_task_error", error=str(e))
                await asyncio.sleep(5)  # Backoff перед наступною ітерацією при збої БД
