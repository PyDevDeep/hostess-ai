from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: SecretStr
    openai_model: str = "gpt-4o-mini-audio-preview"
    openai_analytics_model: str = "gpt-4o-mini"
    n8n_webhook_base_url: str
    airtable_api_key: SecretStr
    airtable_base_id: str
    telegram_bot_token: SecretStr
    telegram_chat_id: str
    sentry_dsn: str | None = None
    database_url: str = "./data/app.db"
    session_hold_ttl_seconds: int = 180
    log_level: str = "INFO"
    fastapi_internal_url: str

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[reportCallIssue]
