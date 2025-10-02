import enum
from datetime import timezone, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Cookie
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from pydantic import BaseModel
from starlette.responses import Response

from backend.utils.env import get_env

JWT_SECRET_KEY = get_env("JWT_SECRET_KEY")
ALGORITHM = "HS256"
AUTHORIZATION_COOKIE = "authorization"


class FailedToDecodeToken(Exception):
    pass


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str


class PlayerRole(str, enum.Enum):
    admin = "admin"
    default = "default"


class PlayerData(BaseModel):
    role: PlayerRole = PlayerRole.default
    room_id: int


def create_access_token(data: PlayerData, expires_delta: timezone | None = None) -> str:
    to_encode = data.model_dump()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> PlayerData:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        return PlayerData(**payload)
    except InvalidTokenError:
        raise FailedToDecodeToken


def add_authorization_cookie(response: Response, token: str) -> None:
    response.set_cookie(AUTHORIZATION_COOKIE, token, httponly=True)


async def current_player_data(authorization: Annotated[str | None, Cookie()] = None) -> PlayerData | None:
    if not authorization:
        return None

    return verify_token(authorization)
