import time
from logging import getLogger

from fastapi import WebSocket
from pydantic import ValidationError

from backend.domain.events import RoomEvent, BaseEvent, GameEvent
from backend.events.bus import EventBus
from backend.games.abstract import GameException
from backend.infra.memory_event_store import MemoryEventStore
from backend.infra.memory_game_store import MemoryGameStore
from backend.infra.snapshots import SnapshotBuilderBase
from backend.models.game_player_model import GamePlayerModel
from backend.schemas.websocket.client import ClientMessageChatMessage, ClientMessageErrorCode, ClientMessageBase, \
    ClientMessageType, ClientMessageGameAction
from backend.schemas.websocket.server import WSMessageSnapshot, WSMessageType, WSMessageEvent, WSMessagePing, \
    WSMessageResponse, WSMessageError

logger = getLogger(__name__)


class StreamingError(Exception):
    def __init__(self, error: WSMessageError, event_key: str | None = None) -> None:
        self.error = error
        self.event_key = event_key
        super().__init__("Streaming error occurred")


class RoomStreamerService:
    @staticmethod
    async def send_current_room_state(
            ws: WebSocket,
            room_id: int,
            user_id: str,
            store: MemoryEventStore,
            snapshot_builder: SnapshotBuilderBase,
    ) -> None:
        history, current_last = await store.read_from(room_id)
        snapshot = await snapshot_builder.build(room_id, history, user_id=user_id)

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
            user_id: str,
            event_bus: EventBus
    ) -> None:
        async with event_bus.subscribe(room_id, user_id) as queue:
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
            raise StreamingError(
                error=WSMessageError(
                    code=ClientMessageErrorCode.INVALID_MESSAGE,
                    message="Malformed chat message"
                ),
                event_key=event_key,
            )

    @staticmethod
    async def _execute_game_event(
            game_store: MemoryGameStore,
            current_user: GamePlayerModel,
            event: BaseEvent,
            event_key: str | None = None,
    ) -> bool:
        game = game_store.get_game(current_user.room_id)
        if not game:
            raise StreamingError(
                error=WSMessageError(
                    code=ClientMessageErrorCode.GAME_NOT_FOUND,
                    message="No game instance found for this room"
                ),
                event_key=event_key,
            )
        try:
            await game.handle_event(event)
        except GameException as e:
            raise StreamingError(
                error=WSMessageError(
                    code=e.exception_type,
                    message=e.message,
                ),
                event_key=event_key,
            )

        return True

    @staticmethod
    async def receive_client_messages(
            ws: WebSocket,
            current_user: GamePlayerModel,
            event_store: MemoryEventStore,
            event_bus: EventBus,
            game_store: MemoryGameStore,
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
                        event_store,
                        event_bus,
                        raw_json,
                        message_base.event_key
                    )
                elif typ == ClientMessageType.GAME_START:
                    event = await event_store.append(
                        room_id=current_user.room_id,
                        event_type=GameEvent.GAME_START,
                        actor_id=current_user.id,
                    )
                    result = await RoomStreamerService._execute_game_event(
                        game_store=game_store,
                        current_user=current_user,
                        event=event,
                        event_key=message_base.event_key,
                    )
                elif typ == ClientMessageType.GAME_RESET:
                    event = await event_store.append(
                        room_id=current_user.room_id,
                        event_type=GameEvent.GAME_RESET,
                        actor_id=current_user.id,
                    )
                    result = await RoomStreamerService._execute_game_event(
                        game_store=game_store,
                        current_user=current_user,
                        event=event,
                        event_key=message_base.event_key,
                    )
                elif typ == ClientMessageType.ACTION:
                    game_action = ClientMessageGameAction.model_validate(raw_json)
                    event = await event_store.append(
                        room_id=current_user.room_id,
                        event_type=GameEvent.PLAYER_ACTION,
                        actor_id=current_user.id,
                        data=game_action.data.model_dump(mode="json")
                    )
                    result = await RoomStreamerService._execute_game_event(
                        game_store=game_store,
                        current_user=current_user,
                        event=event,
                        event_key=message_base.event_key,
                    )

                # Acknowledge successful handling if event_key is provided, even if it was already handled
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
            except StreamingError as err:
                if err.event_key:
                    # If the client expects a response, send a WSMessageResponse
                    await ws.send_json(
                        WSMessageResponse(
                            success=False,
                            event_key=err.event_key,
                            error=err.error
                        ).model_dump(mode="json")
                    )
                else:
                    # Otherwise, send a global message that should be displayed in the user's UI with no specific context
                    await ws.send_json(
                        err.error.model_dump(mode="json")
                    )
            except Exception as e:
                logger.exception("Unexpected error while processing client message", e)
