import enum
from typing import Literal

from pydantic import BaseModel

from backend.games.connect_four.schemas import ConnectFourActionData


class ClientMessageErrorCode(str, enum.Enum):
    INVALID_MESSAGE = "invalid_message"
    UNKNOWN_TYPE = "unknown_type"
    GAME_NOT_FOUND = "game_not_found"
    MISSING_PERMISSIONS = "missing_permissions"


class ClientMessageType(str, enum.Enum):
    PING = "ping"
    CHAT_MESSAGE = "chat_message"
    ACTION = "action"
    GAME_START = "game_start"
    GAME_RESET = "game_reset"


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


class ClientMessageGameStart(ClientMessageBase):
    type: Literal[ClientMessageType.GAME_START] = ClientMessageType.GAME_START


class ClientMessageGameReset(ClientMessageBase):
    type: Literal[ClientMessageType.GAME_RESET] = ClientMessageType.GAME_RESET


class ClientMessageGameAction(ClientMessageBase):
    type: Literal[ClientMessageType.ACTION] = ClientMessageType.ACTION
    data: ConnectFourActionData


WSClientMessage = ClientMessagePing | ClientMessageChatMessage | ClientMessageGameStart | ClientMessageGameReset | ClientMessageGameAction
