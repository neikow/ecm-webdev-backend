from factory.alchemy import SQLAlchemyModelFactory

from backend.models.game_player_model import GamePlayerModel


class GamePlayerFactory(SQLAlchemyModelFactory):
    class Meta:
        model = GamePlayerModel
        