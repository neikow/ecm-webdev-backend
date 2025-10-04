from starlette.websockets import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.rooms: dict[int, set[WebSocket]] = {}

    async def connect(self, room_id: int, ws: WebSocket) -> None:
        self.rooms.setdefault(room_id, set()).add(ws)

    async def disconnect(self, room_id: int, ws: WebSocket) -> None:
        connections = self.rooms.get(room_id)
        if not connections:
            return
        connections.discard(ws)
        if not connections:
            self.rooms.pop(room_id)
