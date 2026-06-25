import asyncio

import httpx
import structlog

from backend.config import Settings
from backend.core.exceptions import N8nError
from backend.models.n8n_payloads import (
    AvailabilityResult,
    CheckAvailabilityPayload,
    ConfirmBookingPayload,
    N8nBookingResponse,
)

logger = structlog.get_logger()


class N8nClient:
    def __init__(self, settings: Settings, http_client: httpx.AsyncClient) -> None:
        self.base_url = settings.n8n_webhook_base_url.rstrip("/")
        self.http_client = http_client

    async def check_availability(self, payload: CheckAvailabilityPayload) -> AvailabilityResult:
        url = f"{self.base_url}/webhook/check-availability"
        delays = [1, 2]

        for attempt in range(3):
            try:
                response = await self.http_client.post(url, json=payload.model_dump(), timeout=10.0)
                response.raise_for_status()
                return AvailabilityResult.model_validate(response.json())

            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status < 500:
                    # Client errors (4xx) should not be retried
                    logger.error("n8n_check_availability_4xx", status=status, error=e.response.text)
                    raise N8nError(f"Client error {status}", "check-availability") from e

                if attempt < len(delays):
                    logger.warning(
                        "n8n_check_availability_retry", attempt=attempt + 1, status=status
                    )
                    await asyncio.sleep(delays[attempt])
                    continue

                logger.error("n8n_check_availability_failed", status=status, retries_exhausted=True)
                raise N8nError(f"Server error {status} after retries", "check-availability") from e

            except httpx.RequestError as e:
                if attempt < len(delays):
                    logger.warning(
                        "n8n_check_availability_retry", attempt=attempt + 1, error=str(e)
                    )
                    await asyncio.sleep(delays[attempt])
                    continue

                logger.error("n8n_check_availability_timeout_or_network", error=str(e))
                raise N8nError(
                    "Network or timeout error after retries", "check-availability"
                ) from e
        raise N8nError("Max retries exhausted for check_availability", "check-availability")

    async def confirm_booking(self, payload: ConfirmBookingPayload) -> N8nBookingResponse:
        url = f"{self.base_url}/webhook/confirm-booking"

        for attempt in range(2):
            try:
                response = await self.http_client.post(url, json=payload.model_dump(), timeout=15.0)
                if response.status_code == 409:
                    raise N8nError("Booking conflict", "confirm-booking")
                response.raise_for_status()
                return N8nBookingResponse.model_validate(response.json())

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 409:
                    raise N8nError("Booking conflict", "confirm-booking") from e
                if attempt == 0 and e.response.status_code >= 500:
                    logger.warning("n8n_confirm_booking_retry", error=str(e))
                    await asyncio.sleep(1)
                    continue
                raise N8nError(
                    f"Failed to confirm booking: {e.response.status_code}", "confirm-booking"
                ) from e

            except httpx.RequestError as e:
                if attempt == 0:
                    logger.warning("n8n_confirm_booking_retry", error=str(e))
                    await asyncio.sleep(1)
                    continue
                raise N8nError("Network or timeout error", "confirm-booking") from e
        raise N8nError("Failed to confirm booking after retries", "confirm-booking")

    async def release_on_hold(self, session_id: str) -> None:
        url = f"{self.base_url}/webhook/release-hold"
        try:
            # Fire-and-forget logic
            await self.http_client.post(url, json={"session_id": session_id}, timeout=5.0)
            logger.info("hold_released", session_id=session_id)
        except Exception as e:
            # Errors are logged, not raised
            logger.warning("release_hold_failed", session_id=session_id, error=str(e))
