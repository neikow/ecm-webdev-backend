import enum
from typing import Literal

from pydantic import BaseModel


class ClientMessageErrorCode(str, enum.Enum):
    INVALID_MESSAGE = "invalid_message"
    UNKNOWN_TYPE = "unknown_type"


class ClientMessageType(str, enum.Enum):
    PING = "ping"
    CHAT_MESSAGE = "chat_message"
    ACTION = "action"


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


class ClientMessageGameAction(ClientMessageBase):
    type: Literal[ClientMessageType.ACTION] = ClientMessageType.ACTION
    action: dict
