import enum
from typing import Literal

from pydantic import BaseModel, Field

from backend.domain.events import BaseEvent, RoomEvent


class SnapshotPlayer(BaseModel):
    user_name: str
    id: str


class SnapshotChatMessage(BaseModel):
    type: Literal["text"] = Field(default="text")
    sender_id: str
    value: str


class RoomStatus(str, enum.Enum):
    WAITING_FOR_PLAYERS = "waiting_for_players"
    WAITING_FOR_START = "waiting_for_start"

    WAITING_FOR_PLAYER = "waiting_for_player"

    CLOSED = "closed"


class SnapshotBase(BaseModel):
    room_id: int
    status: RoomStatus = RoomStatus.WAITING_FOR_PLAYERS
    players: list[SnapshotPlayer] = Field(default_factory=lambda: [])
    chat_messages: list[SnapshotChatMessage] = Field(default_factory=lambda: [])


class SnapshotBuilderBase:
    def handle_external_event(self, event: BaseEvent, state: SnapshotBase) -> SnapshotBase:
        raise NotImplementedError

    async def build(self, room_id: int, events: list[BaseEvent]) -> SnapshotBase:
        state = SnapshotBase(
            room_id=room_id,
        )
        player_names: dict[str, str] = {}
        players: list[str] = list()
        for e in events:
            if e.type == RoomEvent.PLAYER_JOINED:
                players.append(e.data["user_id"])
                player_names[e.data["user_id"]] = e.data["user_name"]
            elif e.type == RoomEvent.PLAYER_LEFT:
                players.remove(e.data["user_id"])
            elif e.type == RoomEvent.ROOM_CLOSED:
                state.status = RoomStatus.CLOSED
            elif e.type == RoomEvent.MESSAGE_SENT:
                state.chat_messages.append(
                    SnapshotChatMessage(
                        sender_id=e.data["sender_id"],
                        value=e.data["value"],
                    )
                )
            else:
                state = self.handle_external_event(
                    e,
                    state,
                )

        state.players = [
            SnapshotPlayer(
                user_name=player_names[_id],
                id=_id
            ) for _id in players
        ]
        return state
