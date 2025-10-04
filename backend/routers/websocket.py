from typing import Annotated

from fastapi import WebSocket, APIRouter
from fastapi.params import Depends
from starlette.websockets import WebSocketDisconnect

from backend.dependencies import get_connection_manager, get_event_store, get_snapshot_builder, get_event_bus
from backend.events.bus import EventBus
from backend.infra.memory_event_store import MemoryEventStore
from backend.infra.snapshots import SnapshotBuilderBase
from backend.models.game_player_model import GamePlayerModel
from backend.services.room_streamer import RoomStreamerService
from backend.state.connection_manager import ConnectionManager
from backend.utils.security import current_player_data

router = APIRouter()


@router.websocket('/ws/game_rooms/{room_id}')
async def game_room_events(
        *,
        websocket: WebSocket,
        room_id: int,
        last_seq: int | None = None,
        current_user: Annotated[GamePlayerModel | None, Depends(current_player_data)],
        connections: Annotated[ConnectionManager, Depends(get_connection_manager)],
        store: Annotated[MemoryEventStore, Depends(get_event_store)],
        snapshot_builder: Annotated[SnapshotBuilderBase, Depends(get_snapshot_builder)],
        event_bus: Annotated[EventBus, Depends(get_event_bus)],
):
    if not current_user or current_user.room_id != room_id:
        await websocket.close(code=4403)
        return

    await websocket.accept()
    await connections.connect(room_id, websocket)

    try:
        await RoomStreamerService.restore_event_history(
            websocket,
            room_id,
            last_seq,
            store,
            snapshot_builder
        )
        await RoomStreamerService.stream_room_events(
            websocket,
            room_id,
            event_bus,
        )
    except WebSocketDisconnect:
        pass
    finally:
        await connections.disconnect(room_id, websocket)
