import time

from fastapi import WebSocket

from backend.domain.events import RoomEvent, BaseEvent
from backend.events.bus import EventBus
from backend.infra.memory_event_store import MemoryEventStore
from backend.infra.snapshots import SnapshotBuilderBase
from backend.models.game_player_model import GamePlayerModel
from backend.routers.websocket_schemas import WSMessageSnapshot, WEMessageError, ClientMessageType, WSMessageEvent
from backend.utils.errors import ErrorCode


class RoomStreamerService:
    @staticmethod
    async def send_current_room_state(
            ws: WebSocket,
            room_id: int,
            store: MemoryEventStore,
            snapshot_builder: SnapshotBuilderBase,
    ) -> None:
        history, current_last = await store.read_from(room_id)
        snapshot = await snapshot_builder.build(room_id, history)

        await ws.send_json(
            WSMessageSnapshot(
                type="snapshot",
                last_seq=current_last,
                data=snapshot,
            ).model_dump(mode="json")
        )

    @staticmethod
    async def stream_room_events(
            ws: WebSocket,
            room_id: int,
            event_bus: EventBus
    ) -> None:
        async with event_bus.subscribe(room_id) as queue:
            while True:
                e = await queue.get()
                await RoomStreamerService.send_ws_message_event(ws, e)

    @staticmethod
    async def send_ws_message_error(
            ws: WebSocket,
            code: ErrorCode,
            message: str
    ) -> None:
        await ws.send_json(
            WEMessageError(
                type="error",
                code=code,
                message=message
            ).model_dump(mode='json')
        )

    @staticmethod
    async def send_ws_message_event(ws: WebSocket, event: BaseEvent) -> None:
        await ws.send_json(
            WSMessageEvent(
                type="event",
                seq=event.seq,
                event=event
            ).model_dump(mode='json')
        )

    @staticmethod
    async def receive_client_messages(
            ws: WebSocket,
            current_user: GamePlayerModel,
            store: MemoryEventStore,
            event_bus: EventBus,
    ) -> None:
        while True:
            msg = await ws.receive_json()
            typ = msg.get("type")
            if not typ:
                await RoomStreamerService.send_ws_message_error(
                    ws,
                    ErrorCode.WS_INVALID_TYPE,
                    "type field is required"
                )
                continue

            if typ == ClientMessageType.PING:
                await ws.send_json({
                    "type": "ping",
                    "timestamp": round(time.time() * 1000)
                })
                continue

            if typ == ClientMessageType.CHAT_MESSAGE:
                text = (msg.get("text") or "").strip()
                if not text:
                    await RoomStreamerService.send_ws_message_error(
                        ws,
                        ErrorCode.WS_CHAT_MESSAGE_MISSING_TEXT,
                        "text field is required"
                    )
                    continue
                event = await store.append(
                    room_id=current_user.room_id,
                    event_type=RoomEvent.MESSAGE_SENT,
                    actor_id=current_user.id,
                    data={
                        "value": text,
                        "sender_id": current_user.id,
                    }
                )
                await event_bus.publish(event=event)
