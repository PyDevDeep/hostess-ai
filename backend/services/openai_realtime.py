import base64
import contextlib
import json
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
import websockets
from pydantic import ValidationError
from websockets.exceptions import ConnectionClosed

from backend.config import Settings
from backend.core.exceptions import SessionExpired
from backend.models.n8n_payloads import CheckAvailabilityPayload, ConfirmBookingPayload
from backend.models.session import SessionStatus, VoiceSession

logger = structlog.get_logger()


class OpenAIRealtimeClient:
    def __init__(self, settings: Settings) -> None:
        self.api_key = settings.openai_api_key.get_secret_value()
        self.model = settings.openai_model
        self.active_sessions: dict[str, VoiceSession] = {}

    async def connect(self, session_id: str, client_ws: Any) -> None:
        url = f"wss://api.openai.com/v1/realtime?model={self.model}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1",
        }

        session = VoiceSession(id=session_id, ws_client=client_ws, status=SessionStatus.CONNECTING)
        self.active_sessions[session_id] = session

        try:
            openai_ws = await websockets.connect(url, extra_headers=headers)
            session.openai_ws = openai_ws

            update_event = {
                "type": "session.update",
                "session": {
                    "instructions": "You are a helpful restaurant booking agent. Be concise.",
                    "tools": [
                        {
                            "type": "function",
                            "name": "check_availability",
                            "description": "Check table availability for a specific date, time, and number of guests.",
                        },
                        {
                            "type": "function",
                            "name": "confirm_booking",
                            "description": "Confirm the booking with the user's name and phone number.",
                        },
                    ],
                    "voice": "alloy",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "turn_detection": {"type": "server_vad"},
                },
            }
            await openai_ws.send(json.dumps(update_event))
            session.status = SessionStatus.ACTIVE
            logger.info("openai_connected", session_id=session_id)
        except Exception as e:
            session.status = SessionStatus.FAILED
            logger.error("openai_connection_failed", session_id=session_id, error=str(e))
            raise

    async def send_audio_chunk(self, session_id: str, chunk: bytes) -> None:
        session = self.active_sessions.get(session_id)
        if not session or not session.openai_ws or session.status != SessionStatus.ACTIVE:
            return

        event = {
            "type": "input_audio_buffer.append",
            "audio": base64.b64encode(chunk).decode("utf-8"),
        }
        await session.openai_ws.send(json.dumps(event))

    async def cancel_response(self, session_id: str) -> None:
        session = self.active_sessions.get(session_id)
        if not session or not session.openai_ws:
            return

        with contextlib.suppress(ConnectionClosed):
            await session.openai_ws.send(json.dumps({"type": "response.cancel"}))
            await session.openai_ws.send(json.dumps({"type": "input_audio_buffer.clear"}))
            logger.info("response_cancelled", session_id=session_id)

    async def close_session(self, session_id: str) -> None:
        session = self.active_sessions.pop(session_id, None)
        if session:
            session.status = SessionStatus.CLOSED
            if session.openai_ws:
                with contextlib.suppress(Exception):
                    await session.openai_ws.close()
            logger.info("session_closed", session_id=session_id)

    async def listen(
        self, session_id: str, on_event: Callable[[str, dict[str, Any]], Awaitable[None]]
    ) -> None:
        session = self.active_sessions.get(session_id)
        if not session or not session.openai_ws:
            return

        try:
            async for message in session.openai_ws:
                payload = json.loads(message)
                event_type = payload.get("type")
                if event_type:
                    await on_event(event_type, payload)
        except ConnectionClosed as e:
            logger.warning(
                "openai_ws_disconnected", session_id=session_id, code=e.code, reason=e.reason
            )
            raise SessionExpired("OpenAI WebSocket disconnected unexpectedly") from e

    async def dispatch_function_call(
        self,
        session_id: str,
        call_id: str,
        fn_name: str,
        args_json: str,
        n8n_client: Any,
        session_repo: Any,
    ) -> dict[str, Any]:
        session = self.active_sessions.get(session_id)
        if not session or not session.openai_ws:
            logger.warning("dispatch_failed_no_session", session_id=session_id)
            return {}

        logger.info(
            "function_call_received", session_id=session_id, fn_name=fn_name, args=args_json
        )
        result_dict: dict[str, Any] = {}

        try:
            args_dict = json.loads(args_json)
            args_dict["session_id"] = session_id

            if fn_name == "check_availability":
                check_payload = CheckAvailabilityPayload(**args_dict)
                result = await n8n_client.check_availability(check_payload)
                await session_repo.set_on_hold(
                    session_id=session_id,
                    date=check_payload.date,
                    time=check_payload.time,
                    guests=check_payload.guests,
                    ttl_seconds=180,
                )
                result_dict = result.model_dump()

            elif fn_name == "confirm_booking":
                confirm_payload = ConfirmBookingPayload(**args_dict)
                result = await n8n_client.confirm_booking(confirm_payload)
                await session_repo.update_status(session_id, SessionStatus.CONFIRMED, None)
                result_dict = result.model_dump()

            else:
                logger.warning("unknown_function", session_id=session_id, fn_name=fn_name)
                result_dict = {"error": f"Unknown function: {fn_name}"}

        except ValidationError as e:
            logger.error(
                "function_call_validation_error",
                session_id=session_id,
                error=str(e),
                original_args=args_json,
            )
            result_dict = {"error": "Invalid parameters, please repeat your request."}
        except Exception as e:
            logger.error("function_call_execution_error", session_id=session_id, error=str(e))
            result_dict = {"error": "Internal system error. Please hold on."}

        event = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": call_id,
                "output": json.dumps(result_dict),
            },
        }
        await session.openai_ws.send(json.dumps(event))
        await session.openai_ws.send(json.dumps({"type": "response.create"}))

        return result_dict
