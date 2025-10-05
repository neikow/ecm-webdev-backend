import asyncio
import contextlib
from asyncio import Future
from typing import Callable, Any, AsyncGenerator, Coroutine

import pytest
import time_machine
from flexmock import flexmock, Mock

from backend.domain.events import BaseEvent, RoomEvent
from backend.events.bus import EventBus
from backend.infra.snapshots import SnapshotBase
from backend.models.game_player_model import GamePlayerModel
from backend.routers.websocket_schemas import ClientMessageType
from backend.services.room_streamer import RoomStreamerService
from backend.utils.errors import ErrorCode
from backend.utils.future import build_future


@pytest.mark.asyncio
async def test_send_current_room_state(
        mock_event_store,
        mock_snapshot_builder,
):
    room_id = 0
    events = []
    snapshot = SnapshotBase(room_id=room_id)
    mock_event_store.should_receive('read_from').with_args(
        room_id
    ).once().and_return(
        build_future((events, 0))
    )
    mock_snapshot_builder.should_receive('build').with_args(
        room_id,
        events,
    ).once().and_return(
        build_future(
            snapshot
        )
    )

    ws = flexmock()
    ws.should_receive('send_json').with_args(
        {
            "type": "snapshot",
            "last_seq": 0,
            "data": snapshot.model_dump(mode="json"),
        }
    ).once().and_return(build_future(None))

    await RoomStreamerService.send_current_room_state(
        ws,  # type: ignore[arg-type]
        room_id,
        mock_event_store,
        mock_snapshot_builder
    )


@pytest.mark.asyncio
async def test_stream_room_events_should_send_ws_message_events_when_they_arrive_on_the_bus():
    mock_event_bus = EventBus()
    ws = flexmock()
    room_id = 0
    event = BaseEvent(
        room_id=room_id,
        data={},
        seq=1,
        type=RoomEvent.PLAYER_JOINED,
    )

    send_task = asyncio.create_task(
        RoomStreamerService.stream_room_events(
            ws,  # type: ignore[arg-type]
            room_id,
            mock_event_bus
        )
    )

    async def task_func():
        flexmock(RoomStreamerService).should_receive('send_ws_message_event').with_args(
            ws,
            event
        ).twice().and_return(
            build_future(None),
            build_future(None),
        ).one_by_one()

        await mock_event_bus.publish(
            event
        )
        await mock_event_bus.publish(
            event
        )

    test_task = asyncio.create_task(
        task_func()
    )

    done, pending = await asyncio.wait(
        {send_task, test_task},
        return_when=asyncio.FIRST_COMPLETED,
        timeout=1.0
    )

    for t in done:
        t.result()

    for t in pending:
        t.cancel()


@pytest.mark.asyncio
async def test_send_ws_error(client):
    ws = flexmock()
    ws.should_receive("send_json").once().with_args(
        {
            "type": "error",
            "code": ErrorCode.WS_INVALID_TYPE.value,
            "message": "Invalid message type",
        }
    ).and_return(build_future(None))

    await RoomStreamerService.send_ws_message_error(
        ws=ws,  # type: ignore[arg-type]
        code=ErrorCode.WS_INVALID_TYPE,
        message="Invalid message type"
    )


@pytest.mark.asyncio
async def test_send_ws_message_event() -> None:
    event = BaseEvent(
        room_id=1,
        data={"key": "value"},
        seq=1,
        type="test_event"
    )
    ws = flexmock()
    ws.should_receive("send_json").once().with_args(
        {
            "type": "event",
            "seq": event.seq,
            "event": event.model_dump(mode="json"),
        }
    ).and_return(build_future(None))
    await RoomStreamerService.send_ws_message_event(
        ws,  # type: ignore[arg-type]
        event
    )


@pytest.mark.asyncio
async def test_send_ws_message_error() -> None:
    error_code = ErrorCode.WS_INVALID_TYPE
    message = "Invalid message type"
    ws = flexmock()
    ws.should_receive("send_json").once().with_args(
        {
            "type": "error",
            "code": error_code.value,
            "message": message,
        }
    ).and_return(build_future(None))
    await RoomStreamerService.send_ws_message_error(
        ws,  # type: ignore[arg-type]
        code=error_code,
        message=message,
    )


@contextlib.asynccontextmanager
async def perform_receive_client_messages_test(
        ws: Mock,
        mock_event_store: Mock,
        mock_event_bus: Mock,
        current_user: GamePlayerModel,
        message: dict,
) -> AsyncGenerator[Callable[[], Coroutine[Any, Any, Future[None]]], Any]:
    result = asyncio.Future()

    def complete_future():
        result.set_result(None)
        return build_future(None)

    ws.should_receive('receive_json').and_return(
        build_future(message),
        # The loop should break after the first message,
        # but we need another value to be awaited when the
        # loop restarts
        asyncio.Future()
    ).one_by_one()

    yield complete_future

    async def task_func():
        await result

    test_task = asyncio.create_task(
        task_func()
    )

    receive_task = asyncio.create_task(
        RoomStreamerService.receive_client_messages(
            ws,  # type: ignore[arg-type]
            current_user,
            mock_event_store,  # type: ignore[arg-type]
            mock_event_bus,  # type: ignore[arg-type]
        )
    )

    done, pending = await asyncio.wait(
        {receive_task, test_task},
        return_when=asyncio.FIRST_COMPLETED,
        timeout=1.0
    )

    for t in done:
        t.result()

    for t in pending:
        t.cancel()


@pytest.mark.asyncio
@time_machine.travel("2025-01-01 12:00:00", tick=False)
async def test_room_streamer_should_receive_client_ping(
        mock_event_store,
        mock_event_bus
):
    ws = flexmock()
    current_user = GamePlayerModel(
        id="user1",
        user_name="Player 1",
        role="player",
        room_id=1,
    )

    async with perform_receive_client_messages_test(
            ws,
            mock_event_store,
            mock_event_bus,
            current_user,
            {
                "type": ClientMessageType.PING
            },
    ) as complete_future:
        ws.should_receive('send_json').with_args({
            "type": ClientMessageType.PING,
            "timestamp": 1735729200000  # 2025-01-01 12:00:00 in milliseconds
        }).once().replace_with(
            lambda _: complete_future()
        )


@pytest.mark.asyncio
async def test_room_streamer_sends_an_error_on_missing_type(
        mock_event_store,
        mock_event_bus
):
    ws = flexmock()
    current_user = GamePlayerModel(
        id="user1",
        user_name="Player 1",
        role="player",
        room_id=1,
    )

    async with perform_receive_client_messages_test(
            ws,
            mock_event_store,
            mock_event_bus,
            current_user,
            {
                # No "type" field
            },
    ) as complete_future:
        ws.should_receive('send_json').with_args({
            "type": "error",
            "code": ErrorCode.WS_INVALID_TYPE.value,
            "message": "type field is required"
        }).once().replace_with(
            lambda _: complete_future()
        )


@pytest.mark.asyncio
@time_machine.travel("2025-01-01 12:00:00", tick=False)
async def test_room_streamer_publishes_a_message_event_to_bus(
        mock_event_store,
        mock_event_bus
):
    ws = flexmock()
    message_value = "Hello, World!"
    current_user = GamePlayerModel(
        id="user1",
        user_name="Player 1",
        role="player",
        room_id=1,
    )

    async with perform_receive_client_messages_test(
            ws,
            mock_event_store,
            mock_event_bus,
            current_user,
            {
                "type": ClientMessageType.CHAT_MESSAGE.value,
                "text": message_value
            },
    ) as complete_future:
        mock_event_bus.should_receive('publish').with_args(
            event=BaseEvent(
                room_id=current_user.room_id,
                actor_id=current_user.id,
                type=RoomEvent.MESSAGE_SENT,
                data={
                    "text": message_value
                },
                seq=1,  # seq is set by the event store, so it will be 1 here
            )
        ).once().replace_with(
            lambda event: complete_future()
        )


@pytest.mark.asyncio
async def test_room_streamer_sends_an_error_on_missing_chat_text(
        mock_event_store,
        mock_event_bus
):
    ws = flexmock()
    current_user = GamePlayerModel(
        id="user1",
        user_name="Player 1",
        role="player",
        room_id=1,
    )

    async with perform_receive_client_messages_test(
            ws,
            mock_event_store,
            mock_event_bus,
            current_user,
            {
                "type": ClientMessageType.CHAT_MESSAGE.value,
                # No "text" field
            },
    ) as complete_future:
        ws.should_receive('send_json').with_args({
            "type": "error",
            "code": ErrorCode.WS_CHAT_MESSAGE_MISSING_TEXT.value,
            "message": "text field is required"
        }).once().replace_with(
            lambda _: complete_future()
        )
