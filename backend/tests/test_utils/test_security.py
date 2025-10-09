from datetime import timedelta
from unittest.mock import MagicMock

import pytest
import time_machine

from backend.models.game_player_model import GamePlayerModel, UserRole
from backend.utils.security import (
    create_access_token,
    verify_access_token,
    current_player_data, add_access_cookie, AUTHORIZATION_COOKIE, remove_authorization_cookie, AccessTokenData,
    TokenType, _encode, InvalidTokenError, RefreshTokenData, create_refresh_token, verify_refresh_token,
    TokenExpiredError
)


@time_machine.travel(0.0)
def test_create_access_token(mocked_env, snapshot):
    with mocked_env({"JWT_SECRET_KEY": "test"}):
        token_data = AccessTokenData(
            player=GamePlayerModel(role=UserRole.admin, room_id=1, id="nanoid")
        )
        encoded_token = create_access_token(
            token_data
        )
        assert encoded_token is not None
        assert encoded_token == snapshot


ENCODED_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwbGF5ZXIiOnsiaWQiOiJuYW5vaWQiLCJyb29tX2lkIjoxLCJyb2xlIjoiYWRtaW4ifSwidHlwIjoiYWNjZXNzIiwiZXhwIjo5MDB9.w8F1jUybacNYpuGw2KxgZ2JTwV_45JM09mJuLIljcnw"


@time_machine.travel(0.0)
def test_verify_access_token(mocked_env):
    with mocked_env({"JWT_SECRET_KEY": "test"}):
        data = verify_access_token(ENCODED_ACCESS_TOKEN)
        assert data.typ == TokenType.ACCESS
        assert data.player.role == UserRole.admin
        assert data.player.room_id == 1


@time_machine.travel(0.0)
def test_verify_access_token_invalid_token_type(mocked_env):
    with mocked_env({"JWT_SECRET_KEY": "test"}):
        invalid_token = _encode(
            GamePlayerModel(id="nanoid", room_id=1, role=UserRole.admin).model_dump() | {
                "typ": TokenType.REFRESH.value},
            expires_delta=timedelta(minutes=15)
        )
        with pytest.raises(InvalidTokenError):
            verify_access_token(invalid_token)


@pytest.mark.asyncio
async def test_current_player_data_no_token():
    user = await current_player_data()
    assert user is None


@pytest.mark.asyncio
@time_machine.travel(0.0)
async def test_current_player_data_with_token():
    user = await current_player_data(authorization=ENCODED_ACCESS_TOKEN)
    assert user is not None
    assert user.role == UserRole.admin
    assert user.room_id == 1


def test_add_authorization_cookie() -> None:
    response = MagicMock()
    response.set_cookie = MagicMock()
    token = ENCODED_ACCESS_TOKEN
    add_access_cookie(response, token)
    response.set_cookie.assert_called_once_with(
        key=AUTHORIZATION_COOKIE,
        value=ENCODED_ACCESS_TOKEN,
        httponly=True,
        secure=True,
        path='/',
        samesite='none'
    )


def test_remove_authorization_cookie() -> None:
    response = MagicMock()
    response.set_cookie = MagicMock()
    remove_authorization_cookie(response)
    response.set_cookie.assert_called_once_with(
        key=AUTHORIZATION_COOKIE,
        expires=0,
        max_age=0,
        httponly=True,
        path="/",
        samesite="none",
        secure=True,
    )


@time_machine.travel(0.0)
def test_create_refresh_token(mocked_env, snapshot):
    with mocked_env({"JWT_SECRET_KEY": "test"}):
        token_data = RefreshTokenData(
            player_id="nanoid",
            room_id=0,
        )
        encoded_token = create_refresh_token(
            token_data
        )
        assert encoded_token is not None
        assert encoded_token == snapshot


refresh_token_data = RefreshTokenData(
    room_id=0,
    player_id="nanoid",
)
ENCODED_REFRESH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwbGF5ZXJfaWQiOiJuYW5vaWQiLCJyb29tX2lkIjowLCJ0eXAiOiJyZWZyZXNoIiwiZXhwIjo4NjQwMH0.jrOrX8bQjrIK_hEOoSu2zA7BS03y1QsSixbnnGxLp1w"


@time_machine.travel(0.0)
def test_verify_refresh_token(mocked_env):
    with mocked_env({"JWT_SECRET_KEY": "test"}):
        data = verify_refresh_token(ENCODED_REFRESH_TOKEN)
        assert data.player_id == refresh_token_data.player_id
        assert data.room_id == refresh_token_data.room_id
        assert data.typ == TokenType.REFRESH


@time_machine.travel(0.0)
def test_verify_refresh_token_invalid_token_type(mocked_env):
    with mocked_env({"JWT_SECRET_KEY": "test"}):
        invalid_token = _encode(
            GamePlayerModel(id="nanoid", room_id=1, role=UserRole.admin).model_dump() | {
                "typ": TokenType.ACCESS.value},
            expires_delta=timedelta(days=1)
        )
        with pytest.raises(InvalidTokenError):
            verify_refresh_token(invalid_token)


@time_machine.travel(10.0)
def test_verify_refresh_token_expired(mocked_env):
    with mocked_env({"JWT_SECRET_KEY": "test"}):
        expired_token = _encode(
            refresh_token_data.model_dump(),
            expires_delta=timedelta(seconds=-1)
        )
        with pytest.raises(TokenExpiredError):
            verify_refresh_token(expired_token)


@time_machine.travel(0.0)
def test_add_refresh_cookie(mocked_env):
    with mocked_env({"JWT_SECRET_KEY": "test"}):
        response = MagicMock()
        response.set_cookie = MagicMock()
        token = create_refresh_token(refresh_token_data)
        add_access_cookie(response, token)
        response.set_cookie.assert_called_once_with(
            key=AUTHORIZATION_COOKIE,
            value=token,
            httponly=True,
            secure=True,
            path='/',
            samesite='none'
        )


@time_machine.travel(0.0)
def test_remove_refresh_cookie():
    response = MagicMock()
    response.set_cookie = MagicMock()
    remove_authorization_cookie(response)
    response.set_cookie.assert_called_once_with(
        key=AUTHORIZATION_COOKIE,
        expires=0,
        max_age=0,
        httponly=True,
        path="/",
        samesite="none",
        secure=True,
    )
