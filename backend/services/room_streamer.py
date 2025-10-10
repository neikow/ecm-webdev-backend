import time
from logging import getLogger

from fastapi import WebSocket
from pydantic import ValidationError

from backend.domain.events import RoomEvent, BaseEvent
from backend.events.bus import EventBus
from backend.infra.memory_event_store import MemoryEventStore
from backend.infra.snapshots import SnapshotBuilderBase
from backend.models.game_player_model import GamePlayerModel
from backend.schemas.websocket.client import ClientMessageChatMessage, ClientMessageErrorCode, ClientMessageBase, \
    ClientMessageType
from backend.schemas.websocket.server import WSMessageSnapshot, WSMessageType, WSMessageEvent, WSMessagePing, \
    WSMessageResponse, WSMessageError

logger = getLogger(__name__)


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
                type=WSMessageType.SNAPSHOT,
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
    async def send_ws_message_event(ws: WebSocket, event: BaseEvent) -> None:
        await ws.send_json(
            WSMessageEvent(
                type=WSMessageType.EVENT,
                seq=event.seq,
                event=event
            ).model_dump(mode='json')
        )

    @staticmethod
    async def _handle_ping(ws: WebSocket) -> bool:
        await ws.send_json(WSMessagePing(
            timestamp=round(time.time() * 1000)
        ).model_dump(mode="json"))
        return True

    @staticmethod
    async def _handle_chat_message(
            ws: WebSocket,
            current_user: GamePlayerModel,
            store: MemoryEventStore,
            event_bus: EventBus,
            raw_json: dict,
            event_key: str | None = None
    ) -> bool:
        try:
            chat_message = ClientMessageChatMessage.model_validate(raw_json)
            text = chat_message.text.strip()
            if not text:
                raise ClientMessageChatMessage.InvalidMessage
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
            return True
        except (ValidationError, ClientMessageChatMessage.InvalidMessage):
            if event_key:
                await ws.send_json(
                    WSMessageResponse(
                        event_key=event_key,
                        success=False,
                        error=WSMessageError(
                            code=ClientMessageErrorCode.INVALID_MESSAGE,
                            message="Malformed chat message"
                        )
                    ).model_dump(mode="json")
                )
            else:
                await ws.send_json(
                    WSMessageError(
                        code=ClientMessageErrorCode.INVALID_MESSAGE,
                        message="Malformed chat message"
                    ).model_dump(mode="json")
                )
            return False

    @staticmethod
    async def receive_client_messages(
            ws: WebSocket,
            current_user: GamePlayerModel,
            store: MemoryEventStore,
            event_bus: EventBus,
    ) -> None:
        while True:
            raw_json = await ws.receive_json()
            try:
                message_base = ClientMessageBase.model_validate(raw_json)
                typ = message_base.type
                result = False

                if typ == ClientMessageType.PING:
                    result = await RoomStreamerService._handle_ping(ws)
                elif typ == ClientMessageType.CHAT_MESSAGE:
                    result = await RoomStreamerService._handle_chat_message(
                        ws,
                        current_user,
                        store,
                        event_bus,
                        raw_json,
                        message_base.event_key
                    )
                elif typ == ClientMessageType.GAME_START:
                    pass
                elif typ == ClientMessageType.ACTION:
                    pass

                if result and message_base.event_key:
                    await ws.send_json(
                        WSMessageResponse(
                            success=True,
                            event_key=message_base.event_key
                        ).model_dump(mode="json"))
            except ValidationError:
                await ws.send_json(
                    WSMessageError(
                        code=ClientMessageBase.InvalidMessage.code,
                        message="Invalid message format"
                    ).model_dump(mode="json")
                )
