from logging import getLogger

from starlette.websockets import WebSocket

logger = getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self.rooms: dict[int, set[WebSocket]] = {}

    async def connect(self, room_id: int, ws: WebSocket) -> None:
        logger.info(f'New connection to room {room_id} for {id(ws)}')
        self.rooms.setdefault(room_id, set()).add(ws)

    async def disconnect(self, room_id: int, ws: WebSocket) -> None:
        connections = self.rooms.get(room_id)
        if not connections:
            return
        logger.info(f'Disconnecting {id(ws)} from room {room_id}')
        connections.discard(ws)
        if not connections:
            logger.info(f'No more connections in room {room_id}, removing from manager')
            self.rooms.pop(room_id)
