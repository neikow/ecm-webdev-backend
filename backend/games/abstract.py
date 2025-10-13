import abc
import enum
from dataclasses import dataclass

from backend.domain.events import BaseEvent
from backend.events.bus import EventBus
from backend.infra.memory_event_store import MemoryEventStore
from backend.models.game_room_model import GameRoomModel


class GameExceptionType(str, enum.Enum):
    state_incompatibility = "state_incompatibility"
    wrong_player = "wrong_player"
    forbidden_action = "forbidden_action"
    invalid_action_data = "invalid_action_data"


class GameException(Exception):
    def __init__(self, *, exception_type: GameExceptionType, message: str) -> None:
        self.exception_type = exception_type
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class PlayerSpec:
    min: int
    max: int


@dataclass(frozen=True)
class Metadata:
    display_name: str
    description: str
    instructions: str
    tags: list[str]


class Game(abc.ABC):
    event_store: MemoryEventStore
    event_bus: EventBus
    game_room: GameRoomModel

    def __init__(
            self,
            game_room: GameRoomModel,
            event_store: MemoryEventStore,
            event_bus: EventBus
    ) -> None:
        self.game_room = game_room
        self.event_store = event_store
        self.event_bus = event_bus

    @classmethod
    @abc.abstractmethod
    def get_players_spec(cls) -> PlayerSpec: ...

    @property
    @abc.abstractmethod
    def metadata(self) -> Metadata: ...

    @abc.abstractmethod
    async def handle_event(
            self,
            event: BaseEvent,
    ) -> None: ...
