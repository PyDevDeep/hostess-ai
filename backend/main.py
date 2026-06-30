from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from backend.api.health import router as health_router
from backend.api.webhook_n8n import router as webhook_router
from backend.api.ws_admin import router as admin_router
from backend.api.ws_voice import router as voice_router
from backend.core.logging import configure_logging
from backend.core.sentry import init_sentry
from backend.db.migrations import init_db
from backend.deps import get_n8n_client, get_session_repo, http_client
from backend.services.session_manager import SessionManager

logger = structlog.get_logger()
session_manager_instance: SessionManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    global session_manager_instance
    configure_logging()
    init_sentry()
    await init_db()

    session_manager_instance = SessionManager(repo=get_session_repo(), n8n_client=get_n8n_client())
    await session_manager_instance.start_cleanup_task()

    logger.info("Application started")
    yield

    if session_manager_instance:
        await session_manager_instance.stop_cleanup_task()
    await http_client.aclose()
    logger.info("Shutdown complete")


app = FastAPI(lifespan=lifespan, title="Restaurant Voice Booking Agent")

app.include_router(health_router)
app.include_router(voice_router)
app.include_router(admin_router)
app.include_router(webhook_router)
