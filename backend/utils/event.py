from starlette.websockets import WebSocket

from backend.domain.events import BaseEvent
from backend.routers.websocket_schemas import WSMessageEvent


async def send_ws_message_event(ws: WebSocket, event: BaseEvent) -> None:
    await ws.send_json(
        WSMessageEvent(
            type="event",
            seq=event.seq,
            event=event
        ).model_dump()
    )
