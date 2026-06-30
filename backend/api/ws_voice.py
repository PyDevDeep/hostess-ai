import asyncio
import base64
import contextlib
from typing import Any
from uuid import uuid4

import structlog
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosed

from backend.core.exceptions import SessionExpired
from backend.db.repositories.session_repo import SessionRepository
from backend.deps import get_analytics_service, get_n8n_client, get_openai_client, get_session_repo
from backend.models.session import SessionStatus
from backend.services.analytics import AnalyticsService
from backend.services.n8n_client import N8nClient
from backend.services.openai_realtime import OpenAIRealtimeClient

logger = structlog.get_logger()
router = APIRouter()
_active_tasks: set[asyncio.Task[Any]] = set()


@router.websocket("/ws/voice")
async def voice_websocket(
    websocket: WebSocket,
    openai_client: OpenAIRealtimeClient = Depends(get_openai_client),
    session_repo: SessionRepository = Depends(get_session_repo),
    n8n_client: N8nClient = Depends(get_n8n_client),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> None:
    await websocket.accept()
    session_id = str(uuid4())
    await session_repo.create_session(session_id)
    logger.info("voice_ws_connected", session_id=session_id)

    try:
        await openai_client.connect(session_id, websocket)
    except Exception:
        with contextlib.suppress(Exception):
            await websocket.close(code=1011)
        return

    transcript: list[str] = []

    async def client_to_openai() -> None:
        try:
            while True:
                message = await websocket.receive()
                if "bytes" in message:
                    await openai_client.send_audio_chunk(session_id, message["bytes"])
        except WebSocketDisconnect:
            logger.info("client_disconnected", session_id=session_id)
        except Exception as e:
            logger.error("client_to_openai_error", error=str(e))

    async def on_openai_event(event_type: str, payload: dict[str, Any]) -> None:
        if event_type == "response.audio.delta":
            delta = payload.get("delta")
            if delta:
                await websocket.send_bytes(base64.b64decode(delta))

        elif event_type == "input_audio_buffer.speech_started":
            await openai_client.cancel_response(session_id)
            await websocket.send_json({"type": "interrupt"})

        elif event_type == "response.function_call.arguments.done":
            call_id = payload.get("call_id")
            fn_name = payload.get("name")
            args = payload.get("arguments")
            if call_id and fn_name and args:
                transcript.append(f"[Function] {fn_name}: {args}")
                await openai_client.dispatch_function_call(
                    session_id=session_id,
                    call_id=call_id,
                    fn_name=fn_name,
                    args_json=args,
                    n8n_client=n8n_client,
                    session_repo=session_repo,
                )

        elif event_type == "response.done":
            session_data = await session_repo.get_session(session_id)
            if session_data and session_data.get("status") == SessionStatus.CONFIRMED.value:
                await websocket.send_json({"type": "session_end"})
                with contextlib.suppress(Exception):
                    await websocket.close(code=1000)

        elif event_type == "response.audio_transcript.done":
            text = payload.get("transcript")
            if text:
                transcript.append(f"AI: {text}")

        elif event_type == "conversation.item.input_audio_transcription.completed":
            text = payload.get("transcript")
            if text:
                transcript.append(f"User: {text}")

    async def openai_to_client() -> None:
        try:
            await openai_client.listen(session_id, on_openai_event)
        except (SessionExpired, ConnectionClosed):
            logger.info("openai_session_expired", session_id=session_id)
        except Exception as e:
            logger.error("openai_to_client_error", error=str(e))

    try:
        await asyncio.gather(client_to_openai(), openai_to_client(), return_exceptions=False)
    except Exception as e:
        logger.error("voice_session_error", error=str(e))
    finally:
        await openai_client.close_session(session_id)
        with contextlib.suppress(Exception):
            await websocket.close()

        task = asyncio.create_task(analytics_service.process_session(session_id, transcript))
        _active_tasks.add(task)
        task.add_done_callback(_active_tasks.discard)
