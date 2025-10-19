import enum

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict
from starlette import status


class ErrorCode(str, enum.Enum):
    INTERNAL_ERROR = "internal_error"
    FORBIDDEN = "forbidden"
    NO_REFRESH_TOKEN = "no_refresh"

    ALREADY_IN_GAME_ROOM = "already_in_game_room"
    NOT_IN_GAME_ROOM = "not_in_game_room"
    PASSWORD_USED = "password_used"
    PASSWORD_INVALID = "password_invalid"
    ROOM_FULL = "game_room_full"
    GAME_ROOM_DOES_NOT_EXIST = "game_room_does_not_exist"
    MISSING_QUERY_PARAMS = "missing_query_params"

    GAME_DOES_NOT_EXIST = "game_does_not_exist"


class ApiErrorDetail(BaseModel):
    model_config = ConfigDict(
        extra="allow"
    )

    code: ErrorCode
    should_refresh_token: bool = False
    message: str


class APIException(HTTPException):
    def __init__(self, *,
                 status_code: int,
                 detail: ApiErrorDetail
                 ) -> None:
        if status_code == status.HTTP_401_UNAUTHORIZED or status_code == status.HTTP_403_FORBIDDEN:
            detail.should_refresh_token = True

        super().__init__(
            status_code=status_code,
            detail=detail.model_dump()
        )
