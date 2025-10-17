import pytest

from backend.domain.events import BaseEvent, RoomEvent, GameEvent
from backend.infra.snapshots import SnapshotBuilderBase, SnapshotBase, SnapshotPlayer, RoomStatus, SnapshotChatMessage, \
    PlayerStatus
from backend.models.game_player_model import UserRole


@pytest.fixture()
def snapshot_builder() -> SnapshotBuilderBase:
    builder = SnapshotBuilderBase()
    return builder


@pytest.mark.asyncio
async def test_build_player_list_snapshot(snapshot_builder) -> None:
    room_id = 0
    admin_data = {'id': "0", "user_name": "admin", "role": UserRole.admin.value}
    snapshot_admin = SnapshotPlayer(user_name="admin", id="0", role=UserRole.admin)
    player_data = {'id': "1", "user_name": "player", "role": UserRole.player.value}
    snapshot_player = SnapshotPlayer(user_name="player", id="1", role=UserRole.player)

    events: list[BaseEvent] = []

    assert await snapshot_builder.build(room_id, events) == SnapshotBase(
        room_id=room_id,
    )

    events.append(
        BaseEvent(
            room_id=room_id,
            data=admin_data,
            seq=1,
            type=RoomEvent.PLAYER_JOINED,
        )
    )

    assert await snapshot_builder.build(room_id, events) == SnapshotBase(
        room_id=room_id,
        players=[snapshot_admin]
    )

    events.append(
        BaseEvent(
            room_id=room_id,
            data=player_data,
            seq=2,
            type=RoomEvent.PLAYER_JOINED,
        )
    )

    assert await snapshot_builder.build(room_id, events) == SnapshotBase(
        room_id=room_id,
        players=[
            snapshot_admin,
            snapshot_player
        ]
    )

    events.append(
        BaseEvent(
            room_id=room_id,
            data=admin_data,
            seq=3,
            type=RoomEvent.PLAYER_LEFT,
        )
    )

    assert await snapshot_builder.build(room_id, events) == SnapshotBase(
        room_id=room_id,
        players=[
            snapshot_admin.model_copy(
                update={"status": PlayerStatus.DISCONNECTED}
            ),
            snapshot_player
        ]
    )


@pytest.mark.asyncio
async def test_snapshot_status_game_closed(snapshot_builder):
    room_id = 0

    snapshot = await snapshot_builder.build(room_id, [
        BaseEvent(
            seq=1,
            room_id=room_id,
            type=RoomEvent.ROOM_CLOSED
        )
    ])

    assert snapshot.status == RoomStatus.CLOSED


@pytest.mark.asyncio
async def test_snapshot_captures_message_feed(snapshot_builder):
    room_id = 0

    snapshot = await snapshot_builder.build(room_id, [
        BaseEvent(
            seq=1,
            room_id=room_id,
            type=RoomEvent.MESSAGE_SENT,
            data={
                "type": "text",
                "sender_id": "0",
                "value": "Hello"
            }
        ),
        BaseEvent(
            seq=2,
            room_id=room_id,
            type=RoomEvent.MESSAGE_SENT,
            data={
                "type": "text",
                "sender_id": "0",
                "value": "World"
            }
        ),
    ])

    assert snapshot.chat_messages == [
        SnapshotChatMessage(
            type="text",
            sender_id="0",
            value="Hello"
        ),
        SnapshotChatMessage(
            type="text",
            sender_id="0",
            value="World"
        )
    ]


@pytest.mark.asyncio
async def test_snapshot_with_a_game_start_event_should_have_in_progress_status(
        mock_snapshot_builder
):
    room_id = 0
    snapshot = await mock_snapshot_builder.build(room_id, [
        BaseEvent(
            room_id=room_id,
            type=GameEvent.GAME_START,
            seq=1,
        )
    ])

    assert snapshot.status == RoomStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_snapshot_with_a_game_state_update_event_should_set_the_data_as_current_room_game_data(
        mock_snapshot_builder
):
    room_id = 0
    snapshot = await mock_snapshot_builder.build(room_id, [
        BaseEvent(
            room_id=room_id,
            type=GameEvent.GAME_STATE_UPDATE,
            seq=1,
            data={
                "some": "data"
            }
        )
    ])

    assert snapshot.game_state == {"some": "data"}
