import asyncio
from dataclasses import dataclass, field

from fastapi import WebSocket


@dataclass
class ConnectionManager:
    _connections: dict[int, list[WebSocket]] = field(default_factory=dict)

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, []).append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        conns = self._connections.get(user_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self._connections.pop(user_id, None)

    async def send_to_user(self, user_id: int, data: dict) -> None:
        conns = self._connections.get(user_id, [])
        dead = []
        for ws in conns:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            conns.remove(ws)

    async def broadcast_to_users(self, user_ids: list[int], data: dict) -> None:
        for uid in user_ids:
            await self.send_to_user(uid, data)


manager = ConnectionManager()
