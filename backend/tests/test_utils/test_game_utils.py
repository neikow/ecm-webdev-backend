from backend.games.connect_four.game import ConnectFour
from backend.models.game_room_model import GameType
from backend.utils.game_utils import get_game_class


def test_get_game_class_for_game_type():
    assert get_game_class(GameType.connect_four) == ConnectFour


def test_get_room_max_users():
    assert get_game_class(GameType.connect_four).get_players_spec() == ConnectFour.get_players_spec()
