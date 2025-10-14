import asyncio
import logging
from typing import Annotated

from fastapi import WebSocket, APIRouter
from fastapi.params import Depends
from starlette.websockets import WebSocketDisconnect

from backend.dependencies import get_connection_manager, get_event_store, get_snapshot_builder, get_event_bus, \
    get_game_store
from backend.events.bus import EventBus
from backend.infra.memory_event_store import MemoryEventStore
from backend.infra.memory_game_store import MemoryGameStore
from backend.infra.snapshots import SnapshotBuilderBase
from backend.models.game_player_model import GamePlayerModel
from backend.services.room_streamer import RoomStreamerService
from backend.state.connection_manager import ConnectionManager
from backend.utils.security import current_player_data

router = APIRouter()

logger = logging.getLogger(__name__)


@router.websocket('/ws/game_rooms/{room_id}')
async def game_room_events(
        *,
        websocket: WebSocket,
        room_id: int,
        current_user: Annotated[GamePlayerModel | None, Depends(current_player_data)],
        connections: Annotated[ConnectionManager, Depends(get_connection_manager)],
        event_store: Annotated[MemoryEventStore, Depends(get_event_store)],
        game_store: Annotated[MemoryGameStore, Depends(get_game_store)],
        snapshot_builder: Annotated[SnapshotBuilderBase, Depends(get_snapshot_builder)],
        event_bus: Annotated[EventBus, Depends(get_event_bus)],
):
    logger.debug("WebSocket connection attempt", room_id, current_user)
    if not current_user or current_user.room_id != room_id:
        await websocket.close(code=4403)
        return

    await websocket.accept()
    await connections.connect(room_id, websocket)

    send_task: asyncio.Task | None = None
    receive_task: asyncio.Task | None = None

    try:
        await RoomStreamerService.send_current_room_state(
            ws=websocket,
            room_id=room_id,
            store=event_store,
            snapshot_builder=snapshot_builder
        )

        send_task = asyncio.create_task(
            RoomStreamerService.stream_room_events(
                ws=websocket,
                room_id=room_id,
                event_bus=event_bus,
            )
        )
        receive_task = asyncio.create_task(
            RoomStreamerService.receive_client_messages(
                ws=websocket,
                current_user=current_user,
                event_store=event_store,
                game_store=game_store,
                event_bus=event_bus,
            )
        )

        done, pending = await asyncio.wait(
            {send_task, receive_task},
            return_when=asyncio.FIRST_EXCEPTION
        )

        for t in done:
            t.result()

    except WebSocketDisconnect:
        pass
    finally:
        for t in (send_task, receive_task):
            if t and not t.done():
                t.cancel()

        await connections.disconnect(room_id, websocket)
