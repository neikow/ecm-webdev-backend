import abc
from dataclasses import dataclass

from backend.domain.events import BaseEvent
from backend.events.bus import EventBus
from backend.infra.memory_event_store import MemoryEventStore


class StateIncompatibilityError(Exception):
    pass


class WrongPlayerMoveError(Exception):
    pass


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
