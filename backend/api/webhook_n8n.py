from fastapi import APIRouter, Depends, Request

from backend.deps import get_admin_broadcaster
from backend.services.admin_broadcaster import AdminBroadcaster

router = APIRouter()


@router.post("/webhook/n8n")
async def handle_n8n_webhook(
    request: Request, broadcaster: AdminBroadcaster = Depends(get_admin_broadcaster)
) -> dict[str, str]:
    payload = await request.json()
    await broadcaster.broadcast(payload)
    return {"status": "ok"}
