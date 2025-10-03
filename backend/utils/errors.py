import enum


class ErrorCode(str, enum.Enum):
    ALREADY_IN_GAME_ROOM = "already_in_game_room"
    NOT_IN_GAME_ROOM = "not_in_game_room"
