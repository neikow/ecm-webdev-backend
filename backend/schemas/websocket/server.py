import enum
from typing import Literal

from pydantic import BaseModel

from backend.domain.events import BaseEvent
from backend.games.abstract import GameExceptionType
from backend.infra.snapshots import SnapshotBase
from backend.schemas.websocket.client import ClientMessageErrorCode


class WSMessageType(str, enum.Enum):
    SNAPSHOT = "snapshot"
    EVENT = "event"
    PING = "ping"
    RESPONSE = "response"
    ERROR = "error"


class WSMessageBase(BaseModel):
    type: WSMessageType


class WSMessageSnapshot(WSMessageBase):
    type: Literal[WSMessageType.SNAPSHOT] = WSMessageType.SNAPSHOT
    last_seq: int
    data: SnapshotBase


class WSMessageEvent(WSMessageBase):
    type: Literal[WSMessageType.EVENT] = WSMessageType.EVENT
    seq: int
    event: BaseEvent


class WSMessagePing(WSMessageBase):
    type: Literal[WSMessageType.PING] = WSMessageType.PING
    timestamp: int


class WSMessageError(BaseModel):
    type: Literal[WSMessageType.ERROR] = WSMessageType.ERROR
    code: ClientMessageErrorCode | GameExceptionType
    message: str


class WSMessageResponse(WSMessageBase):
    type: Literal[WSMessageType.RESPONSE] = WSMessageType.RESPONSE
    event_key: str
    success: bool
    error: WSMessageError | None = None


WSServerMessage = WSMessageBase | WSMessageSnapshot | WSMessageEvent | WSMessagePing | WSMessageError | WSMessageResponse
