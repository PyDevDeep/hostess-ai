from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from backend.deps import get_admin_broadcaster
from backend.services.admin_broadcaster import AdminBroadcaster

router = APIRouter()


@router.websocket("/ws/admin")
async def admin_websocket(
    websocket: WebSocket, broadcaster: AdminBroadcaster = Depends(get_admin_broadcaster)
) -> None:
    await broadcaster.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.disconnect(websocket)
