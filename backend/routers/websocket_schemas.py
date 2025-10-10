import enum
from typing import Literal

from pydantic import BaseModel

from backend.domain.events import BaseEvent
from backend.infra.snapshots import SnapshotBase


class ClientMessageErrorCode(str, enum.Enum):
    INVALID_MESSAGE = "invalid_message"
    UNKNOWN_TYPE = "unknown_type"


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
    code: ClientMessageErrorCode
    message: str


class WSMessageResponse(WSMessageBase):
    type: Literal[WSMessageType.RESPONSE] = WSMessageType.RESPONSE
    event_key: str
    success: bool
    error: WSMessageError | None = None


class ClientMessageType(str, enum.Enum):
    PING = "ping"
    CHAT_MESSAGE = "chat_message"


class ClientMessageException(Exception):
    code: ClientMessageErrorCode


class ClientMessageBase(BaseModel):
    type: ClientMessageType
    event_key: str | None = None

    class InvalidMessage(ClientMessageException):
        code = ClientMessageErrorCode.INVALID_MESSAGE


class ClientMessagePing(ClientMessageBase):
    type: Literal[ClientMessageType.PING] = ClientMessageType.PING


class ClientMessageChatMessage(ClientMessageBase):
    type: Literal[ClientMessageType.CHAT_MESSAGE] = ClientMessageType.CHAT_MESSAGE
    text: str

    class InvalidMessage(ClientMessageException):
        code = ClientMessageErrorCode.INVALID_MESSAGE
