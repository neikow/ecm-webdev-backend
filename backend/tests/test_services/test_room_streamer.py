import asyncio
import contextlib
from asyncio import Future
from typing import Callable, Any, AsyncGenerator, Coroutine

import pytest
import time_machine
from flexmock import flexmock, Mock

from backend.domain.events import BaseEvent, RoomEvent, GameEvent
from backend.events.bus import EventBus
from backend.factories.game_player_factory import GamePlayerFactory
from backend.games.abstract import GameException, GameExceptionType
from backend.games.connect_four.schemas import ConnectFourActionData
from backend.infra.snapshots import SnapshotBase
from backend.models.game_player_model import GamePlayerModel
from backend.models.game_room_model import GameType
from backend.schemas.websocket.client import ClientMessageType, ClientMessageErrorCode, ClientMessageGameAction
from backend.services.game_room_service import GameRoomService
from backend.services.game_service import GameService
from backend.services.room_streamer import RoomStreamerService, StreamingError
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
    user_id = "user"
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
            user_id,
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


@contextlib.asynccontextmanager
async def perform_receive_client_messages_test(
        ws: Mock,
        mock_event_store,
        mock_event_bus,
        mock_game_store,
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
            ws=ws,
            current_user=current_user,
            event_store=mock_event_store,
            game_store=mock_game_store,
            event_bus=mock_event_bus,
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
        mock_event_bus,
        mock_game_store,
):
    ws = flexmock()
    current_user = GamePlayerModel(
        id="user1",
        user_name="Player 1",
        role="player",
        room_id=1,
    )

    async with perform_receive_client_messages_test(
            ws=ws,
            mock_event_store=mock_event_store,
            mock_event_bus=mock_event_bus,
            mock_game_store=mock_game_store,
            current_user=current_user,
            message={
                "type": ClientMessageType.PING
            },
    ) as complete_future:
        ws.should_receive('send_json').with_args({
            "type": ClientMessageType.PING.value,
            "timestamp": 1735729200000  # 2025-01-01 12:00:00 in milliseconds
        }).once().replace_with(
            lambda _: complete_future()
        )


@pytest.mark.asyncio
async def test_room_streamer_sends_an_error_on_missing_type(
        mock_event_store,
        mock_event_bus,
        mock_game_store
):
    ws = flexmock()
    current_user = GamePlayerModel(
        id="user1",
        user_name="Player 1",
        role="player",
        room_id=1,
    )

    async with perform_receive_client_messages_test(
            ws=ws,
            mock_event_store=mock_event_store,
            mock_event_bus=mock_event_bus,
            mock_game_store=mock_game_store,
            current_user=current_user,
            message={
                # No "type" field
            },
    ) as complete_future:
        ws.should_receive('send_json').with_args({
            "type": "error",
            "code": ClientMessageErrorCode.INVALID_MESSAGE.value,
            "message": "Invalid message format"
        }).once().replace_with(
            lambda _: complete_future()
        )


@pytest.mark.asyncio
@time_machine.travel("2025-01-01 12:00:00", tick=False)
async def test_room_streamer_publishes_a_message_event_to_bus(
        mock_event_store,
        mock_event_bus,
        mock_game_store,
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
            ws=ws,
            mock_event_store=mock_event_store,
            mock_event_bus=mock_event_bus,
            mock_game_store=mock_game_store,
            current_user=current_user,
            message={
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
                    "sender_id": current_user.id,
                    "value": message_value
                },
                seq=1,  # seq is set by the event store, so it will be 1 here
            )
        ).once().replace_with(
            lambda event: complete_future()
        )


@pytest.mark.asyncio
async def test_room_streamer_sends_an_error_on_missing_chat_text(
        mock_event_store,
        mock_event_bus,
        mock_game_store,
):
    ws = flexmock()
    current_user = GamePlayerModel(
        id="user1",
        user_name="Player 1",
        role="player",
        room_id=1,
    )

    async with perform_receive_client_messages_test(
            ws=ws,
            mock_event_store=mock_event_store,
            mock_event_bus=mock_event_bus,
            mock_game_store=mock_game_store,
            current_user=current_user,
            message={
                "type": ClientMessageType.CHAT_MESSAGE.value,
                # No "text" field
            },
    ) as complete_future:
        ws.should_receive('send_json').with_args({
            "type": "error",
            "code": ClientMessageErrorCode.INVALID_MESSAGE.value,
            "message": "Malformed chat message"
        }).once().replace_with(
            lambda _: complete_future()
        )


@pytest.mark.asyncio
@time_machine.travel("2025-01-01 12:00:00", tick=False)
async def test_room_streamer_sends_response_on_event_key(
        mock_event_store,
        mock_event_bus,
        mock_game_store,
):
    ws = flexmock()
    event_key = "test_event_key"
    message_value = "Hello, World!"
    current_user = GamePlayerModel(
        id="user1",
        user_name="Player 1",
        role="player",
        room_id=1,
    )

    async with perform_receive_client_messages_test(
            ws=ws,
            mock_event_store=mock_event_store,
            mock_event_bus=mock_event_bus,
            mock_game_store=mock_game_store,
            current_user=current_user,
            message={
                "type": ClientMessageType.CHAT_MESSAGE.value,
                "text": message_value,
                "event_key": event_key
            },
    ) as complete_future:
        mock_event_bus.should_receive('publish').with_args(
            event=BaseEvent(
                room_id=current_user.room_id,
                actor_id=current_user.id,
                type=RoomEvent.MESSAGE_SENT,
                data={
                    "sender_id": current_user.id,
                    "value": message_value
                },
                seq=1,  # seq is set by the event store, so it will be 1 here
            )
        ).once().replace_with(
            lambda event: build_future(None)
        )
        ws.should_receive('send_json').with_args({
            "type": "response",
            "event_key": event_key,
            "success": True,
            "error": None
        }).once().replace_with(
            lambda _: complete_future()
        )


@pytest.mark.asyncio
async def test_room_streamer_sends_error_response_on_malformed_chat_message(
        mock_event_store,
        mock_event_bus,
        mock_game_store,
):
    ws = flexmock()
    event_key = "test_event_key"
    current_user = GamePlayerModel(
        id="user1",
        user_name="Player 1",
        role="player",
        room_id=1,
    )

    async with perform_receive_client_messages_test(
            ws=ws,
            mock_event_store=mock_event_store,
            mock_event_bus=mock_event_bus,
            mock_game_store=mock_game_store,
            current_user=current_user,
            message={
                "type": ClientMessageType.CHAT_MESSAGE.value,
                "text": '',
                "event_key": event_key
            },
    ) as complete_future:
        ws.should_receive('send_json').with_args({
            "type": "response",
            "event_key": event_key,
            "success": False,
            "error": {
                "type": "error",
                "code": ClientMessageErrorCode.INVALID_MESSAGE.value,
                "message": "Malformed chat message"
            }
        }).once().replace_with(
            lambda _: complete_future()
        )


@pytest.mark.asyncio
@time_machine.travel("2025-01-01 12:00:00", tick=False)
async def test_room_streamer_receives_game_start_event_should_forward_it_to_the_game(
        session,
        mock_event_store,
        mock_event_bus,
        mock_game_store,
):
    ws = flexmock()
    game_room = GameRoomService.create(session, password="password", game_type=GameType.connect_four)
    user: GamePlayerModel = GamePlayerFactory.build(
        room_id=0
    )

    GameService.create_game(
        game_room=game_room,
        game_type=game_room.game_type,
        event_bus=mock_event_bus,
        game_store=mock_game_store,
        event_store=mock_event_store,
    )

    async with perform_receive_client_messages_test(
            ws=ws,
            mock_event_store=mock_event_store,
            mock_event_bus=mock_event_bus,
            mock_game_store=mock_game_store,
            current_user=user,
            message={
                "type": ClientMessageType.GAME_START.value,
                "room_id": game_room.id,
            },
    ) as complete_future:
        flexmock(RoomStreamerService).should_receive("_execute_game_event").once().with_args(
            game_store=mock_game_store,
            current_user=user,
            event=BaseEvent(
                room_id=user.room_id,
                type=GameEvent.GAME_START,
                actor_id=user.id,
                seq=1,
            ),
            event_key=None,
        ).replace_with(
            lambda *_, **__: complete_future()
        )


@pytest.mark.asyncio
@time_machine.travel("2025-01-01 12:00:00", tick=False)
async def test_room_streamer_receives_player_action_event_should_forward_it_to_the_game(
        session,
        mock_event_store,
        mock_event_bus,
        mock_game_store,
):
    ws = flexmock()
    game_room = GameRoomService.create(session, password="password", game_type=GameType.connect_four)
    user: GamePlayerModel = GamePlayerFactory.build(
        room_id=0
    )

    GameService.create_game(
        game_room=game_room,
        game_type=game_room.game_type,
        event_bus=mock_event_bus,
        game_store=mock_game_store,
        event_store=mock_event_store,
    )

    async with perform_receive_client_messages_test(
            ws=ws,
            mock_event_store=mock_event_store,
            mock_event_bus=mock_event_bus,
            mock_game_store=mock_game_store,
            current_user=user,
            message=ClientMessageGameAction(
                data=ConnectFourActionData(
                    player=1,
                    column=0,
                ),
                event_key="test_event_key",
            ).model_dump(mode="json"),
    ) as complete_future:
        flexmock(RoomStreamerService).should_receive("_execute_game_event").once().with_args(
            game_store=mock_game_store,
            current_user=user,
            event=BaseEvent(
                room_id=user.room_id,
                type=GameEvent.PLAYER_ACTION,
                actor_id=user.id,
                seq=1,
                data={
                    "player": 1,
                    "column": 0,
                },
            ),
            event_key="test_event_key",
        ).replace_with(
            # `and False` to not send a success response
            lambda *_, **__: complete_future()
        )


@pytest.mark.asyncio
async def test_execute_game_event_handles_game_not_found(
        mock_game_store,
        mock_event_bus,
):
    user: GamePlayerModel = GamePlayerFactory.build(
        room_id=0
    )
    event = BaseEvent(
        room_id=user.room_id,
        type=GameEvent.GAME_START,
        actor_id=user.id,
        seq=1,
    )

    with pytest.raises(StreamingError):
        await RoomStreamerService._execute_game_event(
            game_store=mock_game_store,
            current_user=user,
            event=event,
            event_key=None,
        )


@pytest.mark.asyncio
async def test_execute_game_event_handles_game_handle_event_raises(
        mock_game_store,
        mock_event_bus,
        session,
):
    game_room = GameRoomService.create(session, password="password", game_type=GameType.connect_four)
    user: GamePlayerModel = GamePlayerFactory.build(
        room_id=game_room.id
    )
    event = BaseEvent(
        room_id=user.room_id,
        type=GameEvent.GAME_START,
        actor_id=user.id,
        seq=1,
    )

    mock_game = flexmock()
    mock_game.should_receive('handle_event').once().and_raise(
        GameException(
            message="Test exception",
            exception_type=GameExceptionType.forbidden_action
        )
    )

    mock_game_store.should_receive('get_game').with_args(
        key=game_room.id
    ).once().and_return(
        mock_game
    )

    with pytest.raises(StreamingError) as exc_info:
        await RoomStreamerService._execute_game_event(
            game_store=mock_game_store,
            current_user=user,
            event=event,
            event_key=None,
        )
    assert exc_info.value.error.code == GameExceptionType.forbidden_action
    assert exc_info.value.error.message == "Test exception"


@pytest.mark.asyncio
async def test_execute_game_event_succeeds(
        mock_game_store,
        mock_event_bus,
        session,
):
    game_room = GameRoomService.create(session, password="password", game_type=GameType.connect_four)
    user: GamePlayerModel = GamePlayerFactory.build(
        room_id=game_room.id
    )
    event = BaseEvent(
        room_id=user.room_id,
        type=GameEvent.GAME_START,
        actor_id=user.id,
        seq=1,
    )

    mock_game = flexmock()
    mock_game.should_receive('handle_event').once().and_return(
        build_future(None)
    )

    mock_game_store.should_receive('get_game').with_args(
        key=game_room.id
    ).once().and_return(
        mock_game
    )

    result = await RoomStreamerService._execute_game_event(
        game_store=mock_game_store,
        current_user=user,
        event=event,
        event_key=None,
    )
    assert result is True
