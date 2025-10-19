import enum
from datetime import timezone, datetime, timedelta
from typing import Annotated, Literal

import jwt
from fastapi import Cookie
from jwt.exceptions import DecodeError
from pydantic import BaseModel, ValidationError
from starlette.responses import Response

from backend.models.game_player_model import GamePlayerModel
from backend.utils.env import get_env

JWT_SECRET_KEY = get_env("JWT_SECRET_KEY")
ALGORITHM = "HS256"
AUTHORIZATION_COOKIE = "authorization"
AUTHORIZATION_COOKIE_EXPIRATION = timedelta(minutes=15)
REFRESH_COOKIE = "refresh"
REFRESH_COOKIE_EXPIRATION = timedelta(days=1)


class FailedToDecodeToken(Exception):
    pass


class InvalidTokenError(Exception):
    pass


class TokenExpiredError(Exception):
    pass


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenType(str, enum.Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class AccessTokenData(BaseModel):
    player: GamePlayerModel
    typ: Literal[TokenType.ACCESS] = TokenType.ACCESS


class RefreshTokenData(BaseModel):
    player_id: str
    room_id: int
    typ: Literal[TokenType.REFRESH] = TokenType.REFRESH


def _encode(payload: dict, expires_delta: timedelta):
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {**payload, "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(data: AccessTokenData, expires_delta: timedelta | None = None) -> str:
    return _encode(
        data.model_dump(),
        expires_delta=expires_delta or AUTHORIZATION_COOKIE_EXPIRATION,
    )


def create_refresh_token(data: RefreshTokenData, expires_delta: timedelta | None = None) -> str:
    return _encode(
        data.model_dump(),
        expires_delta=expires_delta or REFRESH_COOKIE_EXPIRATION,
    )


def verify_access_token(token: str) -> AccessTokenData:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return AccessTokenData.model_validate(payload)
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError
    except ValidationError:
        raise InvalidTokenError
    except (DecodeError, ValueError):
        raise FailedToDecodeToken


def verify_refresh_token(token: str) -> RefreshTokenData:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return RefreshTokenData(**payload)
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError
    except (ValidationError, ValueError):
        raise InvalidTokenError
    except DecodeError:
        raise FailedToDecodeToken


def add_access_cookie(response: Response, token: str) -> None:
    response.delete_cookie(key=AUTHORIZATION_COOKIE)
    response.set_cookie(
        key=AUTHORIZATION_COOKIE,
        value=token,
        httponly=True,
        secure=True,
        path="/",
        samesite="none",
    )


def add_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=True,
        path="/",
        samesite="none",
    )


def remove_authorization_cookie(response: Response) -> None:
    response.set_cookie(
        key=AUTHORIZATION_COOKIE,
        expires=0,
        max_age=0,
        httponly=True,
        path="/",
        samesite="none",
        secure=True
    )


def remove_refresh_cookie(response: Response) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        expires=0,
        max_age=0,
        httponly=True,
        path="/",
        samesite="none",
        secure=True
    )


async def current_player_data(authorization: Annotated[str | None, Cookie()] = None) -> GamePlayerModel | None:
    if not authorization:
        return None
    try:
        return verify_access_token(authorization).player
    except TokenExpiredError:
        return None
