import enum
from typing import Literal

from pydantic import BaseModel

from backend.domain.events import BaseEvent
from backend.infra.snapshots import SnapshotBase
from backend.utils.errors import ErrorCode


class WSMessageSnapshot(BaseModel):
    type: Literal["snapshot"] = "snapshot"
    last_seq: int
    data: SnapshotBase


class WSMessageEvent(BaseModel):
    type: Literal["event"] = "event"
    seq: int
    event: BaseEvent


class ClientMessageType(str, enum.Enum):
    PING = "ping"
    CHAT_MESSAGE = "chat_message"


class WEMessageError(BaseModel):
    type: Literal["error"] = "error"
    code: ErrorCode
    message: str
