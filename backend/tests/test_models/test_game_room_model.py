import datetime

import time_machine

from backend.models.game_room_model import GameRoomModel, GameType


@time_machine.travel(0.0, tick=False)
def test_game_room_model_defaults():
    game_room = GameRoomModel(password="securepassword")
    assert game_room.id is None
    assert game_room.password == "securepassword"
    assert game_room.is_active is True
    assert game_room.game_type == GameType.connect_four
    assert game_room.created_at == datetime.datetime(1970, 1, 1, 1)
