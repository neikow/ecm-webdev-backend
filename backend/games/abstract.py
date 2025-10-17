import abc
import enum
from dataclasses import dataclass
from typing import Literal, TypeVar, Generic

from pydantic import BaseModel

from backend.domain.events import BaseEvent, GameEvent
from backend.events.bus import EventBus
from backend.infra.memory_event_store import MemoryEventStore
from backend.models.game_room_model import GameRoomModel


class GameExceptionType(str, enum.Enum):
    state_incompatibility = "game_exception.state_incompatibility"
    wrong_player = "game_exception.wrong_player"
    unknown_action = "game_exception.unknown_action"
    forbidden_action = "game_exception.forbidden_action"
    invalid_action_data = "game_exception.invalid_action_data"
    wrong_players_number = "game_exception.wrong_players_number"


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


@dataclass(frozen=True)
class GamePlayer:
    id: int
    user_id: str
    status: Literal[
        "joined",
        "left",
        "connection_lost"
    ]


class GameStatus(str, enum.Enum):
    not_started = "not_started"
    ongoing = "ongoing"
    draw = "draw"
    win = "win"

    @property
    def can_be_started(self) -> bool:
        return self == GameStatus.not_started

    @property
    def can_be_joined(self) -> bool:
        return self == GameStatus.not_started

    @property
    def accepts_player_actions(self) -> bool:
        return self == GameStatus.ongoing


class GameState(abc.ABC, BaseModel):
    can_start: bool = False
    status: GameStatus = GameStatus.not_started


TGameState = TypeVar('TGameState', bound=GameState)


class Game(abc.ABC, Generic[TGameState]):
    event_store: MemoryEventStore
    event_bus: EventBus
    game_room: GameRoomModel
    _player_count: int = 0
    players: dict[int, GamePlayer]

    state: TGameState

    def __init__(
            self,
            game_room: GameRoomModel,
            event_store: MemoryEventStore,
            event_bus: EventBus
    ) -> None:
        self.game_room = game_room
        self.event_store = event_store
        self.event_bus = event_bus
        self.players = {}

    @classmethod
    @abc.abstractmethod
    def get_players_spec(cls) -> PlayerSpec:
        ...

    @property
    @abc.abstractmethod
    def metadata(self) -> Metadata:
        ...

    @abc.abstractmethod
    async def handle_event(
            self,
            event: BaseEvent,
    ) -> None:
        ...

    async def broadcast_game_state_update(self, *, actor_id: str | None) -> None:
        event = await self.event_store.append(
            room_id=self.game_room.id,
            event_type=GameEvent.GAME_STATE_UPDATE,
            actor_id=actor_id,
            data=self.state.model_dump(mode="json"),
        )
        await self.event_bus.publish(event=event)

    @property
    def current_players(self) -> list[GamePlayer]:
        return [p for p in self.players.values() if p.status != 'left']

    async def add_player(self, user_id: str) -> GamePlayer:
        if not self.state.status.can_be_joined:
            raise ValueError("Cannot join a game that has already started.")
        spec = self.get_players_spec()
        if len(self.current_players) >= spec.max:
            raise ValueError("The game is full.")

        player = GamePlayer(
            id=self._player_count,
            user_id=user_id,
            status="joined"
        )
        self.players[self._player_count] = player
        self._player_count += 1

        if len(self.current_players) >= spec.min and not self.state.can_start:
            self.state.can_start = True

            await self.broadcast_game_state_update(actor_id=None)

        return player
