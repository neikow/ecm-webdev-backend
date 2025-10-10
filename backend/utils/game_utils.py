from backend.games.abstract import Game
from backend.games.connect_four.game import ConnectFour
from backend.models.game_room_model import GameType


def get_game_class(game_type: GameType) -> type[Game]:
    if game_type == GameType.connect_four:
        return ConnectFour

    raise ValueError(f"Unsupported game type: {game_type}")


def get_room_max_users(game_type: GameType) -> int:
    game_class = get_game_class(game_type)
    return game_class.get_players_spec().max


def get_room_min_users(game_type: GameType) -> int:
    game_class = get_game_class(game_type)
    return game_class.get_players_spec().min
