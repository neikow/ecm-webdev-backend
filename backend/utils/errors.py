import enum

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict


class ErrorCode(str, enum.Enum):
    INTERNAL_ERROR = "internal_error"
    FORBIDDEN = "forbidden"

    ALREADY_IN_GAME_ROOM = "already_in_game_room"
    NOT_IN_GAME_ROOM = "not_in_game_room"
    PASSWORD_USED = "password_used"
    PASSWORD_INVALID = "password_invalid"
    ROOM_FULL = "game_room_full"
    GAME_ROOM_DOES_NOT_EXIST = "game_room_does_not_exist"
    MISSING_QUERY_PARAMS = "missing_query_params"

    WS_INVALID_TYPE = "ws_invalid_type"
    WS_CHAT_MESSAGE_MISSING_TEXT = "ws_chat_message_missing_text"


class ApiErrorDetail(BaseModel):
    model_config = ConfigDict(
        extra="allow"
    )

    code: ErrorCode
    message: str


class APIException(HTTPException):
    def __init__(self, *,
                 status_code: int,
                 detail: ApiErrorDetail
                 ) -> None:
        super().__init__(
            status_code=status_code,
            detail=detail.model_dump()
        )
