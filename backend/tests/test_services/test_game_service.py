from backend.factories.game_room_factory import GameRoomFactory
from backend.games.abstract import Game
from backend.models.game_room_model import GameType
from backend.services.game_service import GameService


def test_game_service_create_new_game(
        mock_game_store,
        mock_event_store,
        mock_event_bus,
):
    service = GameService()
    game_room = GameRoomFactory.build()
    game = service.create_game(
        game_room=game_room,
        game_type=GameType.connect_four,
        game_store=mock_game_store,
        event_store=mock_event_store,
        event_bus=mock_event_bus,
    )
    assert isinstance(game, Game)
    assert game.game_room == game_room
    assert game.event_store == mock_event_store
    assert game.event_bus == mock_event_bus


def test_game_service_create_new_game_should_store_game(
        session,
        mock_game_store,
        mock_event_store,
        mock_event_bus,
):
    service = GameService()
    game_room = GameRoomFactory.create()
    service.create_game(
        game_room=game_room,
        game_type=GameType.connect_four,
        game_store=mock_game_store,
        event_store=mock_event_store,
        event_bus=mock_event_bus,
    )
    stored_game = mock_game_store.get_game(game_room.id)
    assert stored_game is not None


def test_game_service_get_game(
        mock_game_store,
        mock_event_store,
        mock_event_bus,
):
    service = GameService()
    game_room = GameRoomFactory.build()
    created_game = service.create_game(
        game_room=game_room,
        game_type=GameType.connect_four,
        game_store=mock_game_store,
        event_store=mock_event_store,
        event_bus=mock_event_bus,
    )
    retrieved_game = service.get_game(
        game_room_id=game_room.id,
        game_store=mock_game_store,
    )
    assert retrieved_game == created_game
