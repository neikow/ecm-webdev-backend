import pytest
from flexmock import flexmock

from backend.domain.events import BaseEvent
from backend.events.bus import EventBus
from backend.games.abstract import Game, PlayerSpec, Metadata, GamePlayer, GameState
from backend.infra.memory_event_store import MemoryEventStore
from backend.models.game_room_model import GameRoomModel
from backend.utils.future import build_future


class ConcreteGameState(GameState):
    pass


class ConcreteGame(Game[ConcreteGameState]):
    def __init__(self,
                 game_room: GameRoomModel,
                 event_bus: EventBus,
                 event_store: MemoryEventStore,
                 ) -> None:
        super().__init__(game_room, event_store, event_bus)
        self.state = ConcreteGameState()

    @classmethod
    def get_players_spec(cls) -> PlayerSpec:
        return PlayerSpec(min=1, max=2)

    def metadata(self) -> Metadata:
        return Metadata(
            display_name="Concrete Game",
            description="",
            instructions="",
            tags=[]
        )

    def handle_event(
            self,
            event: BaseEvent,
    ) -> None:
        pass


def test_current_players_getter(mock_event_bus, mock_event_store):
    game_room = GameRoomModel(
        id=0,
        game_type="connect_four",
        max_players=2,
    )
    game = ConcreteGame(
        game_room=game_room,
        event_bus=mock_event_bus,
        event_store=mock_event_store
    )
    assert game.current_players == []
    game.players[0] = GamePlayer(id=0, user_id='player1', status='joined')
    game.players[1] = GamePlayer(id=1, user_id='player2', status='connection_lost')
    game.players[2] = GamePlayer(id=2, user_id='player3', status='left')
    assert game.current_players == [
        GamePlayer(id=0, user_id='player1', status='joined'),
        GamePlayer(id=1, user_id='player2', status='connection_lost'),
    ]


@pytest.mark.asyncio
async def test_add_player_to_game(mock_event_bus, mock_event_store):
    game_room = GameRoomModel(
        id=0,
        game_type="connect_four",
        max_players=2,
    )
    game = ConcreteGame(
        game_room=game_room,
        event_bus=mock_event_bus,
        event_store=mock_event_store
    )
    assert await game.add_player('player1') == GamePlayer(id=0, user_id='player1', status='joined')
    assert len(game.players) == 1
    assert await game.add_player('player2') == GamePlayer(id=1, user_id='player2', status='joined')
    with pytest.raises(ValueError):
        await game.add_player('player3')


@pytest.mark.asyncio
async def test_adding_enough_players_should_send_a_game_state_update_event(mock_event_bus, mock_event_store):
    game_room = GameRoomModel(
        id=0,
        game_type="connect_four",
    )
    game = ConcreteGame(
        game_room=game_room,
        event_bus=mock_event_bus,
        event_store=mock_event_store
    )
    flexmock(game).should_receive(
        'broadcast_game_state_update',
    ).once().with_args(
        actor_id=None
    ).and_return(build_future(None))

    await game.add_player('player1')

    assert game.state.can_start is True


@pytest.mark.asyncio
async def test_adding_players_when_game_already_started_raises_error(mock_event_bus, mock_event_store):
    game_room = GameRoomModel(
        id=0,
        game_type="connect_four",
    )
    game = ConcreteGame(
        game_room=game_room,
        event_bus=mock_event_bus,
        event_store=mock_event_store
    )
    game.state.status = game.state.status.ongoing

    with pytest.raises(ValueError):
        await game.add_player('player1')
