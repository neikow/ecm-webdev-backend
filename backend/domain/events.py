import enum
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class RoomEvent(str, enum.Enum):
    PLAYER_JOINED = "player.joined"
    PLAYER_LEFT = "player.left"

    ROOM_CLOSED = "room.closed"

    MESSAGE_SENT = "message.sent"


class BaseEvent(BaseModel):
    model_config = ConfigDict(frozen=True)
    seq: int
    room_id: int
    type: RoomEvent | str
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor_id: str | None = None
    data: dict = Field(default_factory=lambda: {})
