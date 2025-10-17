import pytest
from flexmock import flexmock
from starlette.websockets import WebSocketDisconnect, WebSocket

from backend.events.bus import EventBus
from backend.infra.memory_event_store import MemoryEventStore
from backend.infra.snapshots import SnapshotBuilderBase
from backend.models.game_player_model import GamePlayerModel, UserRole
from backend.services.room_streamer import RoomStreamerService
from backend.utils.future import build_future
from backend.utils.security import AUTHORIZATION_COOKIE, create_access_token, AccessTokenData


@pytest.mark.asyncio
async def test_websocket_connection_fails_without_auth(client):
    try:
        with client.websocket_connect('/ws/game_rooms/1') as ws:
            assert ws is not None
    except WebSocketDisconnect as x:
        assert x.code == 4403


@pytest.mark.asyncio
async def test_websocket_connection_succeeds_with_auth(client):
    client.cookies[AUTHORIZATION_COOKIE] = create_access_token(
        AccessTokenData(
            player=GamePlayerModel(
                id="test_id",
                user_name="test_user",
                room_id=1,
                role=UserRole.admin,
            )
        )
    )
    with client.websocket_connect('/ws/game_rooms/1') as ws:
        assert ws is not None


def test_websocket_connection_restores_history(client):
    room_id = 1
    player = GamePlayerModel(
        id="test_id",
        user_name="test_user",
        room_id=room_id,
        role=UserRole.admin,
    )
    client.cookies[AUTHORIZATION_COOKIE] = create_access_token(
        AccessTokenData(
            player=player
        )
    )

    flexmock(RoomStreamerService).should_receive("send_current_room_state").with_args(
        ws=WebSocket,
        room_id=room_id,
        store=MemoryEventStore,
        snapshot_builder=SnapshotBuilderBase
    ).and_return(
        build_future(None)
    ).once()
    flexmock(RoomStreamerService).should_receive("stream_room_events").with_args(
        ws=WebSocket,
        room_id=room_id,
        user_id=player.id,
        event_bus=EventBus
    ).and_return(
        build_future(None)
    ).once()

    with client.websocket_connect(f'/ws/game_rooms/{room_id}') as ws:
        assert ws is not None
