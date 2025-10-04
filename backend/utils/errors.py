import enum

from pydantic import BaseModel, ConfigDict


class ErrorCode(str, enum.Enum):
    INTERNAL_ERROR = "internal_error"
    ALREADY_IN_GAME_ROOM = "already_in_game_room"
    NOT_IN_GAME_ROOM = "not_in_game_room"
    PASSWORD_USED = "password_used"
    PASSWORD_INVALID = "password_invalid"
    ROOM_FULL = "game_room_full"
    GAME_ROOM_DOES_NOT_EXIST = "game_room_does_not_exist"
    MISSING_QUERY_PARAMS = "missing_query_params"


class ExceptionDetail(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )

    code: ErrorCode
    message: str
