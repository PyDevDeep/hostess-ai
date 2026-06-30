import httpx

from backend.config import get_settings
from backend.db.repositories.analytics_repo import AnalyticsRepository
from backend.db.repositories.session_repo import SessionRepository
from backend.services.admin_broadcaster import AdminBroadcaster
from backend.services.analytics import AnalyticsService
from backend.services.n8n_client import N8nClient
from backend.services.openai_realtime import OpenAIRealtimeClient

http_client = httpx.AsyncClient()
admin_broadcaster_instance = AdminBroadcaster()
openai_client_instance = None


def get_admin_broadcaster() -> AdminBroadcaster:
    return admin_broadcaster_instance


def get_session_repo() -> SessionRepository:
    return SessionRepository()


def get_analytics_repo() -> AnalyticsRepository:
    return AnalyticsRepository()


def get_n8n_client() -> N8nClient:
    return N8nClient(settings=get_settings(), http_client=http_client)


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService(
        settings=get_settings(), repo=get_analytics_repo(), http_client=http_client
    )


def get_openai_client() -> OpenAIRealtimeClient:
    global openai_client_instance
    if not openai_client_instance:
        openai_client_instance = OpenAIRealtimeClient(settings=get_settings())
    return openai_client_instance
