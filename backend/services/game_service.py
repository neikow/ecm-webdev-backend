from backend.events.bus import EventBus
from backend.games.abstract import Game
from backend.infra.memory_event_store import MemoryEventStore
from backend.infra.memory_game_store import MemoryGameStore
from backend.models.game_room_model import GameType, GameRoomModel
from backend.utils.game_utils import get_game_class


class GameService:
    @staticmethod
    def create_game(
            game_room: GameRoomModel,
            game_type: GameType,
            game_store: MemoryGameStore,
            event_store: MemoryEventStore,
            event_bus: EventBus,
    ) -> Game:
        cls = get_game_class(game_type)
        game = cls(
            game_room=game_room,
            event_store=event_store,
            event_bus=event_bus,
        )
        game_store.add_game(game_room.id, game)

        return game
