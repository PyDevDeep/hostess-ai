from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from backend.api.health import router as health_router
from backend.core.logging import configure_logging
from backend.core.sentry import init_sentry
from backend.db.migrations import init_db

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    configure_logging()
    init_sentry()
    await init_db()
    logger.info("Application started")
    yield
    logger.info("Shutdown complete")


app = FastAPI(lifespan=lifespan, title="Restaurant Voice Booking Agent")

app.include_router(health_router)
