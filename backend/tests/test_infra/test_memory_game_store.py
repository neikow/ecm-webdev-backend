import pytest
from flexmock import flexmock

from backend.domain.events import BaseEvent
from backend.factories.game_room_factory import GameRoomFactory
from backend.games.abstract import Game, Metadata, PlayerSpec


@pytest.fixture()
def mock_game(mock_event_store, mock_event_bus):
    class DummyGame(Game):
        @classmethod
        def get_players_spec(cls) -> PlayerSpec:
            return PlayerSpec(
                min=2,
                max=4,
            )

        @property
        def metadata(self) -> Metadata:
            return Metadata(
                display_name="Dummy Game",
                description="Description",
                instructions="",
                tags=["tag1"], )

        async def handle_event(self, event: BaseEvent) -> None:
            pass

    game_room = GameRoomFactory.build()

    return flexmock(
        DummyGame(
            game_room=game_room,
            event_store=mock_event_store,
            event_bus=mock_event_bus,
        )
    )


def test_create_memory_game_store(mock_game_store):
    assert mock_game_store is not None


def test_memory_game_store_initial_state(mock_game_store):
    assert isinstance(mock_game_store._games, dict)
    assert len(mock_game_store._games) == 0


def test_memory_game_store_add_game(mock_game_store, mock_game):
    mock_game_store.add_game("game1", mock_game)
    assert len(mock_game_store._games) == 1
    assert "game1" in mock_game_store._games


def test_memory_game_store_get_game_existing(mock_game_store, mock_game):
    mock_game_store.add_game("game1", mock_game)
    retrieved_game = mock_game_store.get_game("game1")
    assert retrieved_game == mock_game


def test_memory_game_store_get_game_non_existing(mock_game_store):
    retrieved_game = mock_game_store.get_game("non_existing_game")
    assert retrieved_game is None


def test_memory_game_store_delete_game(mock_game_store, mock_game):
    mock_game_store.add_game("game1", mock_game)
    assert len(mock_game_store._games) == 1
    mock_game_store.delete_game("game1")
    assert len(mock_game_store._games) == 0
    assert mock_game_store.get_game("game1") is None
