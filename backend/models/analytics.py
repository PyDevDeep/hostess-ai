import time
from uuid import uuid4

from pydantic import BaseModel, Field


class SentimentResult(BaseModel):
    sentiment: str
    failure_reason: str | None = None
    summary: str
    raw_transcript: str


class AnalyticsRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    sentiment: str
    failure_reason: str | None = None
    summary: str
    raw_transcript: str
    created_at: float = Field(default_factory=time.time)
