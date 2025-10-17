import pytest
import time_machine
from flexmock import flexmock

from backend.domain.events import BaseEvent, GameEvent
from backend.games.abstract import GameException, GameExceptionType, GameStatus, GamePlayer
from backend.games.connect_four import game as connect_four
from backend.games.connect_four.game import ConnectFour
from backend.games.connect_four.schemas import ConnectFourActionData
from backend.models.game_room_model import GameRoomModel
from backend.utils.future import build_future


@pytest.fixture(scope="function")
def game_room():
    return GameRoomModel(
        id=0,
        game_type="connect_four",
        max_players=2,
    )


@pytest.fixture(scope="function")
def empty_grid():
    return [[0 for _ in range(7)] for _ in range(6)]


def test_connect_four_is_subclass_of_game():
    from backend.games.abstract import Game

    assert issubclass(ConnectFour, Game)


def test_connect_four_players_spec():
    spec = ConnectFour.get_players_spec()
    assert spec.min == 2
    assert spec.max == 2


def test_connect_four_metadata():
    assert ConnectFour.metadata.display_name == "Connect Four"
    assert "two-player" in ConnectFour.metadata.tags
    assert len(ConnectFour.metadata.description) > 0
    assert len(ConnectFour.metadata.instructions) > 0


def test_connect_four_initializes_with_defaults(game_room, mock_event_store, mock_event_bus):
    game = ConnectFour(
        game_room=game_room,
        event_store=mock_event_store,
        event_bus=mock_event_bus,
    )
    assert game.state.grid == [[0 for _ in range(7)] for _ in range(6)]
    assert game.state.current_player == 0
    assert game.state.status == GameStatus.not_started


@pytest.mark.asyncio
@time_machine.travel("2025-01-01 12:00:00", tick=False)
async def test_connect_four_handle_game_start_event(
        game_room,
        mock_event_store,
        mock_event_bus,
        empty_grid,
):
    game = ConnectFour(game_room=game_room, event_store=mock_event_store, event_bus=mock_event_bus)
    assert game.state.status == GameStatus.not_started
    current_player = 1

    flexmock(connect_four).should_receive("randint").and_return(current_player)

    await game.add_player("player1")
    await game.add_player("player2")

    assert mock_event_bus.should_receive("publish").with_args(
        event=BaseEvent(
            type=GameEvent.GAME_STATE_UPDATE,
            seq=2,
            actor_id="player1",
            room_id=game_room.id,
            data={
                'can_start': True,
                'status': 'ongoing',
                'grid': empty_grid,
                'current_player': 1,
                'winning_positions': None
            },
        )
    ).once().and_return(build_future(None))

    await game.handle_event(
        BaseEvent(
            type=GameEvent.GAME_START,
            seq=0,
            actor_id="player1",
            room_id=game_room.id,
        ),
    )

    assert game.state.status == GameStatus.ongoing


@pytest.mark.asyncio
async def test_connect_four_handle_game_start_event_twice_raises(
        game_room,
        mock_event_store,
        mock_event_bus,
):
    game = ConnectFour(game_room=game_room, event_store=mock_event_store, event_bus=mock_event_bus)

    await game.add_player('player1')
    await game.add_player('player2')

    await game.handle_event(
        BaseEvent(
            type=GameEvent.GAME_START,
            seq=0,
            actor_id="player1",
            room_id=game_room.id,
        ),
    )
    assert game.state.status == GameStatus.ongoing

    with pytest.raises(GameException) as exc_info:
        await game.handle_event(
            BaseEvent(
                type=GameEvent.GAME_START,
                seq=1,
                actor_id="player1",
                room_id=game_room.id,
            ),
        )

    assert exc_info.value.exception_type == GameExceptionType.state_incompatibility


@pytest.mark.asyncio
@time_machine.travel("2025-01-01 12:00:00", tick=False)
async def test_connect_four_handle_player_action(
        game_room,
        mock_event_store,
        mock_event_bus,
        empty_grid,
):
    game = ConnectFour(game_room=game_room, event_store=mock_event_store, event_bus=mock_event_bus)
    flexmock(connect_four).should_receive("randint").and_return(1)

    await game.add_player('player1')
    await game.add_player('player2')

    await game.handle_event(
        BaseEvent(
            type=GameEvent.GAME_START,
            seq=0,
            actor_id="player1",
            room_id=game_room.id,
        ),
    )
    assert game.state.status == GameStatus.ongoing
    assert game.state.current_player == 1

    assert mock_event_bus.should_receive("publish").with_args(
        event=BaseEvent(
            type=GameEvent.GAME_STATE_UPDATE,
            seq=3,
            actor_id="player1",
            room_id=game_room.id,
            data={
                'can_start': True,
                'status': 'ongoing',
                'grid': [
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0],
                ],
                'current_player': 2,
                'winning_positions': None
            },
        )
    ).once().and_return(build_future(None))

    await game.handle_event(
        BaseEvent(
            type=GameEvent.PLAYER_ACTION,
            seq=1,
            actor_id="player1",
            room_id=game_room.id,
            data=ConnectFourActionData(
                player=1,
                column=3,
            ).model_dump(),
        )
    )

    expected_grid = [row[:] for row in empty_grid]
    expected_grid[5][3] = 1
    assert game.state.grid == expected_grid
    assert game.state.current_player == 2


def test_connect_four_get_column_height():
    grid = [
        [0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 2, 1, 0],
        [0, 0, 0, 1, 2, 1, 0],
        [0, 0, 2, 1, 2, 1, 0],
        [0, 1, 2, 1, 2, 1, 0],
        [2, 1, 2, 1, 2, 1, 0],
    ]
    assert ConnectFour._get_column_height(grid, 0) == 1
    assert ConnectFour._get_column_height(grid, 1) == 2
    assert ConnectFour._get_column_height(grid, 2) == 3
    assert ConnectFour._get_column_height(grid, 3) == 4
    assert ConnectFour._get_column_height(grid, 4) == 5
    assert ConnectFour._get_column_height(grid, 5) == 6
    assert ConnectFour._get_column_height(grid, 6) == 0


@pytest.mark.asyncio
async def test_connect_four_handle_player_action_out_of_turn(
        game_room,
        mock_event_store,
        mock_event_bus,
):
    game = ConnectFour(game_room=game_room, event_store=mock_event_store, event_bus=mock_event_bus)
    flexmock(connect_four).should_receive("randint").and_return(1)

    await game.add_player('player1')
    await game.add_player('player2')

    await game.handle_event(
        BaseEvent(
            type=GameEvent.GAME_START,
            seq=0,
            actor_id="player1",
            room_id=game_room.id,
        ),
    )
    assert game.state.status == GameStatus.ongoing
    assert game.state.current_player == 1

    with pytest.raises(GameException) as exc_info:
        await game.handle_event(
            BaseEvent(
                type=GameEvent.PLAYER_ACTION,
                seq=1,
                actor_id="player2",
                room_id=game_room.id,
                data=ConnectFourActionData(
                    player=2,
                    column=3,
                ).model_dump(),
            )
        )

    assert exc_info.value.exception_type == GameExceptionType.wrong_player


@pytest.mark.asyncio
async def test_connect_four_handle_player_action_column_full(
        game_room,
        mock_event_store,
        mock_event_bus,
):
    game = ConnectFour(game_room=game_room, event_store=mock_event_store, event_bus=mock_event_bus)
    flexmock(connect_four).should_receive("randint").and_return(1)

    await game.add_player('player1')
    await game.add_player('player2')

    await game.handle_event(
        BaseEvent(
            type=GameEvent.GAME_START,
            seq=0,
            actor_id="player1",
            room_id=game_room.id,
        ),
    )
    assert game.state.status == GameStatus.ongoing
    assert game.state.current_player == 1

    game.state.grid = [
        [0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 2, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 2, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 2, 0, 0, 0],
    ]

    with pytest.raises(GameException) as exc_info:
        await game.handle_event(
            BaseEvent(
                type=GameEvent.PLAYER_ACTION,
                seq=7,
                actor_id="player1",
                room_id=game_room.id,
                data=ConnectFourActionData(
                    player=1,
                    column=3,
                ).model_dump(),
            )
        )

    assert exc_info.value.exception_type == GameExceptionType.forbidden_action


@pytest.mark.asyncio
async def test_connect_four_handle_player_action_wrong_state(
        game_room,
        mock_event_store,
        mock_event_bus,
):
    game = ConnectFour(game_room=game_room, event_store=mock_event_store, event_bus=mock_event_bus)
    assert game.state.status == GameStatus.not_started

    with pytest.raises(GameException) as exc_info:
        await game.handle_event(
            BaseEvent(
                type=GameEvent.PLAYER_ACTION,
                seq=0,
                actor_id="player1",
                room_id=game_room.id,
                data=ConnectFourActionData(
                    player=1,
                    column=3,
                ).model_dump(),
            )
        )

    assert exc_info.value.exception_type == GameExceptionType.state_incompatibility


@pytest.mark.asyncio
async def test_connect_four_handle_player_action_invalid_column(
        game_room,
        mock_event_store,
        mock_event_bus,
):
    game = ConnectFour(game_room=game_room, event_store=mock_event_store, event_bus=mock_event_bus)
    flexmock(connect_four).should_receive("randint").and_return(1)

    await game.add_player("player1")
    await game.add_player("player2")

    await game.handle_event(
        BaseEvent(
            type=GameEvent.GAME_START,
            seq=0,
            actor_id="player1",
            room_id=game_room.id,
        ),
    )
    assert game.state.status == GameStatus.ongoing
    assert game.state.current_player == 1

    with pytest.raises(ValueError):
        await game.handle_event(
            BaseEvent(
                type=GameEvent.PLAYER_ACTION,
                seq=1,
                actor_id="player1",
                room_id=game_room.id,
                data=ConnectFourActionData(
                    player=1,
                    column=7,  # Invalid column, should be between 0 and 6
                ).model_dump(),
            )
        )


def test_check_winner_horizontal():
    grid = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 1],
        [0, 0, 0, 2, 2, 0, 0],
        [0, 0, 0, 2, 1, 0, 0],
    ]
    has_winner, positions = ConnectFour._check_winner(grid, player=1)
    assert has_winner is True
    assert positions == [(2, 3), (2, 4), (2, 5), (2, 6)]


def test_check_winner_vertical():
    grid = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 2, 0, 0],
        [0, 0, 0, 1, 2, 0, 0],
        [0, 0, 0, 2, 1, 0, 0],
    ]
    has_winner, positions = ConnectFour._check_winner(grid, player=1)
    assert has_winner is True
    assert positions == [(4, 3), (3, 3), (2, 3), (1, 3)]


def test_check_winner_diagonal():
    grid = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
        [0, 0, 1, 2, 0, 0, 0],
        [0, 1, 2, 1, 2, 0, 0],
        [1, 2, 2, 1, 2, 0, 0],
        [2, 1, 1, 2, 1, 0, 0],
    ]
    has_winner, positions = ConnectFour._check_winner(grid, player=1)
    assert has_winner is True
    assert positions == [(4, 3), (3, 2), (2, 1), (1, 0)]


def test_check_winner_draw():
    grid = [
        [1, 2, 1, 2, 1, 2, 1],
        [2, 1, 2, 1, 2, 1, 2],
        [1, 2, 1, 2, 1, 2, 1],
        [2, 1, 2, 1, 2, 1, 2],
        [1, 2, 1, 2, 1, 2, 1],
        [2, 1, 2, 1, 2, 1, 2],
    ]
    is_draw = ConnectFour._check_draw(grid)
    assert is_draw is True

    grid[0][0] = 0
    is_draw = ConnectFour._check_draw(grid)
    assert is_draw is False


@pytest.mark.asyncio
@time_machine.travel("2025-01-01 12:00:00", tick=False)
async def test_connect_four_handle_player_action_winning_move(
        game_room,
        mock_event_store,
        mock_event_bus,
):
    game = ConnectFour(game_room=game_room, event_store=mock_event_store, event_bus=mock_event_bus)
    flexmock(connect_four).should_receive("randint").and_return(1)

    await game.add_player("player1")
    await game.add_player("player2")

    await game.handle_event(
        BaseEvent(
            type=GameEvent.GAME_START,
            seq=0,
            actor_id="player1",
            room_id=game_room.id,
        ),
    )
    assert game.state.status == GameStatus.ongoing
    assert game.state.current_player == 1

    game.state.grid = [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 2, 0, 0],
        [0, 0, 0, 1, 2, 0, 0],
        [0, 0, 0, 1, 2, 0, 0],
    ]

    assert mock_event_bus.should_receive("publish").with_args(
        event=BaseEvent(
            type=GameEvent.GAME_STATE_UPDATE,
            seq=3,
            actor_id="player1",
            room_id=game_room.id,
            data={
                'can_start': True,
                'status': 'win',
                'grid': [
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0],
                    [0, 0, 0, 1, 2, 0, 0],
                    [0, 0, 0, 1, 2, 0, 0],
                    [0, 0, 0, 1, 2, 0, 0],
                ],
                'current_player': 1,
                'winning_positions': [[3, 3], [2, 3], [1, 3], [0, 3]]
            },
        )
    ).once().and_return(build_future(None))

    await game.handle_event(
        BaseEvent(
            type=GameEvent.PLAYER_ACTION,
            seq=1,
            actor_id="player1",
            room_id=game_room.id,
            data=ConnectFourActionData(
                player=1,
                column=3,
            ).model_dump(),
        )
    )


@pytest.mark.asyncio
@time_machine.travel("2025-01-01 12:00:00", tick=False)
async def test_connect_four_handle_player_action_draw_move(
        game_room,
        mock_event_store,
        mock_event_bus,
):
    game = ConnectFour(game_room=game_room, event_store=mock_event_store, event_bus=mock_event_bus)
    flexmock(connect_four).should_receive("randint").and_return(2)

    await game.add_player("player1")
    await game.add_player("player2")

    await game.handle_event(
        BaseEvent(
            type=GameEvent.GAME_START,
            seq=0,
            actor_id="player1",
            room_id=game_room.id,
        ),
    )
    assert game.state.status == GameStatus.ongoing
    assert game.state.current_player == 2

    game.state.grid = [
        [1, 2, 1, 0, 1, 2, 1],
        [1, 2, 1, 1, 1, 2, 1],
        [2, 1, 2, 1, 2, 1, 2],
        [2, 1, 2, 2, 2, 1, 2],
        [1, 2, 1, 2, 1, 2, 1],
        [2, 1, 2, 2, 2, 1, 2],
    ]

    assert mock_event_bus.should_receive("publish").with_args(
        event=BaseEvent(
            type=GameEvent.GAME_STATE_UPDATE,
            seq=3,
            actor_id="player2",
            room_id=game_room.id,
            data={
                'can_start': True,
                'status': 'draw',
                'grid': [
                    [1, 2, 1, 2, 1, 2, 1],
                    [1, 2, 1, 1, 1, 2, 1],
                    [2, 1, 2, 1, 2, 1, 2],
                    [2, 1, 2, 2, 2, 1, 2],
                    [1, 2, 1, 2, 1, 2, 1],
                    [2, 1, 2, 2, 2, 1, 2],
                ],
                'current_player': 2,
                'winning_positions': None
            },
        )
    ).once().and_return(build_future(None))

    await game.handle_event(
        BaseEvent(
            type=GameEvent.PLAYER_ACTION,
            seq=1,
            actor_id="player2",
            room_id=game_room.id,
            data=ConnectFourActionData(
                player=2,
                column=3,
            ).model_dump(),
        )
    )


@pytest.mark.asyncio
async def test_cannot_start_game_if_not_enough_players(
        game_room,
        mock_event_store,
        mock_event_bus,
):
    game = ConnectFour(game_room=game_room, event_store=mock_event_store, event_bus=mock_event_bus)

    await game.add_player("player1")

    with pytest.raises(GameException) as exc_info:
        await game.handle_event(
            BaseEvent(
                type=GameEvent.GAME_START,
                seq=0,
                actor_id="player1",
                room_id=game_room.id,
            ),
        )

    assert exc_info.value.exception_type == GameExceptionType.wrong_players_number


@pytest.mark.asyncio
async def test_cannot_start_game_if_too_many_players(
        game_room,
        mock_event_store,
        mock_event_bus,
):
    game = ConnectFour(game_room=game_room, event_store=mock_event_store, event_bus=mock_event_bus)

    await game.add_player("player1")
    await game.add_player("player2")
    # Manually add a third player to simulate too many players
    game.players[2] = GamePlayer(id=2, user_id='player3', status='joined')

    with pytest.raises(GameException) as exc_info:
        await game.handle_event(
            BaseEvent(
                type=GameEvent.GAME_START,
                seq=0,
                actor_id="player1",
                room_id=game_room.id,
            ),
        )

    assert exc_info.value.exception_type == GameExceptionType.wrong_players_number


@pytest.mark.asyncio
async def test_handle_unknown_event_type_raises(
        game_room,
        mock_event_store,
        mock_event_bus,
):
    game = ConnectFour(game_room=game_room, event_store=mock_event_store, event_bus=mock_event_bus)

    with pytest.raises(GameException) as exc_info:
        await game.handle_event(
            BaseEvent(
                type="unknown_event_type",
                seq=0,
                actor_id="player1",
                room_id=game_room.id,
            ),
        )

    assert exc_info.value.exception_type == GameExceptionType.unknown_action
