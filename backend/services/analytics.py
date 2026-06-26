import json
import typing

import httpx
import structlog
from openai import AsyncOpenAI

from backend.config import Settings
from backend.db.repositories.analytics_repo import AnalyticsRepository
from backend.models.analytics import AnalyticsRecord

logger = structlog.get_logger()


class AnalyticsService:
    def __init__(
        self, settings: Settings, repo: AnalyticsRepository, http_client: httpx.AsyncClient
    ) -> None:
        self.settings = settings
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())
        self.model = settings.openai_analytics_model
        self.repo = repo
        self.http_client = http_client

    async def process_session(self, session_id: str, transcript: list[str]) -> None:
        if not transcript:
            logger.info("analytics_skipped_empty_transcript", session_id=session_id)
            return

        raw_transcript = "\n".join(transcript)

        try:
            prompt = (
                "Analyze this restaurant booking transcript:\n"
                f"{raw_transcript}\n\n"
                "Return strictly JSON matching this schema:\n"
                '{"sentiment": "Positive/Neutral/Negative", "failure_reason": "<reason or null>", "summary": "<short summary>"}'
            )

            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                timeout=15.0,
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")

            parsed = typing.cast(dict[str, typing.Any], json.loads(content))

            record = AnalyticsRecord(
                session_id=session_id,
                sentiment=str(parsed.get("sentiment", "Neutral")),
                failure_reason=typing.cast(str | None, parsed.get("failure_reason")),
                summary=str(parsed.get("summary", "")),
                raw_transcript=raw_transcript,
            )

            await self.repo.save_record(record)

            # Відправка в n8n (некритичний webhook)
            webhook_url = (
                f"{self.settings.n8n_webhook_base_url.rstrip('/')}/webhook/post-call-analytics"
            )
            await self.http_client.post(webhook_url, json=record.model_dump(), timeout=5.0)

            logger.info("analytics_processed_successfully", session_id=session_id)

        except Exception as e:
            # Згідно з специфікацією: помилки аналітики ніколи не поширюються далі
            logger.warning("analytics_processing_failed", session_id=session_id, error=str(e))
