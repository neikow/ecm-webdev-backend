from factory.alchemy import SQLAlchemyModelFactory

from backend.models.game_room_model import GameRoomModel


class GameRoomFactory(SQLAlchemyModelFactory):
    class Meta:
        model = GameRoomModel
