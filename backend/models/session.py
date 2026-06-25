import time
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class SessionStatus(StrEnum):
    IDLE = "IDLE"
    CONNECTING = "CONNECTING"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    CLOSED = "CLOSED"


class VoiceSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    status: SessionStatus = SessionStatus.IDLE
    ws_client: Any | None = Field(default=None, exclude=True)
    openai_ws: Any | None = Field(default=None, exclude=True)
    created_at: float = Field(default_factory=time.time)
    transcript: list[str] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}
