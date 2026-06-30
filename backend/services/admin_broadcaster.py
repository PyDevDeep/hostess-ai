import json
from typing import Any

import structlog
from fastapi import WebSocket

logger = structlog.get_logger()


class AdminBroadcaster:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("admin_ws_connected", total=len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("admin_ws_disconnected", total=len(self.active_connections))

    async def broadcast(self, message: dict[str, Any]) -> None:
        payload = json.dumps(message)
        dead_connections: list[WebSocket] = []

        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.warning("admin_ws_send_error", error=str(e))
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)
