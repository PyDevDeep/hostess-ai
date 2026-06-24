import sentry_sdk
from fastapi import WebSocketDisconnect
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.types import Event, Hint

from backend.config import get_settings
from backend.core.exceptions import SessionExpired


def filter_events(event: Event, hint: Hint) -> Event | None:
    if "exc_info" in hint:
        exc_type, _, _ = hint["exc_info"]
        if exc_type is not None and issubclass(exc_type, SessionExpired | WebSocketDisconnect):
            return None
    return event


def init_sentry() -> None:
    settings = get_settings()
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            traces_sample_rate=0.2,
            integrations=[FastApiIntegration(transaction_style="url")],
            before_send=filter_events,
        )
