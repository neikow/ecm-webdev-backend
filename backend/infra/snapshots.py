import enum
from logging import getLogger
from typing import Literal

from pydantic import BaseModel, Field

from backend.domain.events import BaseEvent, RoomEvent, GameEvent
from backend.games.connect_four.schemas import ConnectFourPlayerData
from backend.models.game_player_model import UserRole


class PlayerStatus(str, enum.Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class SnapshotPlayer(BaseModel):
    user_name: str
    role: UserRole
    id: str
    status: PlayerStatus = Field(default=PlayerStatus.CONNECTED)


class SnapshotChatMessage(BaseModel):
    type: Literal["text"] = Field(default="text")
    sender_id: str
    value: str


class RoomStatus(str, enum.Enum):
    WAITING_FOR_PLAYERS = "waiting_for_players"
    WAITING_FOR_START = "waiting_for_start"

    WAITING_FOR_PLAYER = "waiting_for_player"

    IN_PROGRESS = "in_progress"

    CLOSED = "closed"


class SnapshotBase(BaseModel):
    room_id: int
    status: RoomStatus = RoomStatus.WAITING_FOR_PLAYERS
    players: list[SnapshotPlayer] = Field(default_factory=lambda: [])
    chat_messages: list[SnapshotChatMessage] = Field(default_factory=lambda: [])
    player_data: ConnectFourPlayerData | None = None
    game_state: dict | None = None


logger = getLogger(__name__)


class SnapshotBuilderBase:
    async def build(
            self,
            room_id: int,
            events: list[BaseEvent],
            user_id: str | None = None
    ) -> SnapshotBase:
        # A nice optimization would be to build snapshot incrementally and cache it
        logger.info(f"Building snapshot for room_id={room_id} with {len(events)} events")
        state = SnapshotBase(
            room_id=room_id,
        )
        players: list[SnapshotPlayer] = []
        for e in events:
            if e.type == RoomEvent.PLAYER_JOINED:
                players.append(
                    SnapshotPlayer(
                        id=e.data['id'],
                        role=e.data['role'],
                        user_name=e.data['user_name'],
                        status=PlayerStatus.CONNECTED
                    )
                )
            elif e.type == RoomEvent.PLAYER_LEFT:
                player = next((_p for _p in players if _p.id == e.data['id']), None)
                if player:
                    player.status = PlayerStatus.DISCONNECTED
            elif e.type == RoomEvent.ROOM_CLOSED:
                state.status = RoomStatus.CLOSED
            elif e.type == RoomEvent.MESSAGE_SENT:
                state.chat_messages.append(
                    SnapshotChatMessage(
                        sender_id=e.data["sender_id"],
                        value=e.data["value"],
                    )
                )
            elif e.type == GameEvent.GAME_START:
                state.status = RoomStatus.IN_PROGRESS
            elif e.type == GameEvent.GAME_INIT:
                if e.target_id == user_id:
                    state.player_data = ConnectFourPlayerData.model_validate(e.data)
            elif e.type == GameEvent.GAME_STATE_UPDATE:
                state.game_state = e.data
            else:
                logger.info("Unhandled event type in snapshot builder", e.type)

        state.players = players

        return state
