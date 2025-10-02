from unittest.mock import MagicMock

import pytest
import time_machine

from backend.utils.security import (
    create_access_token,
    PlayerRole,
    verify_token,
    PlayerData,
    current_player_data, add_authorization_cookie, AUTHORIZATION_COOKIE
)


@time_machine.travel(0.0)
def test_create_access_token(mocked_env, snapshot):
    with mocked_env({"JWT_SECRET_KEY": "test"}):
        token_data = PlayerData(role=PlayerRole.admin, room_id=1)
        encoded_token = create_access_token(token_data)
        assert encoded_token is not None
        assert encoded_token == snapshot


# Precomputed token for data: {"role": "admin", "room_id": 1, "exp": 900}
ENCODED_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYWRtaW4iLCJyb29tX2lkIjoxLCJleHAiOjkwMH0.KxFDPcZok1wcC9viNcfguu0SEPR0i3q_AL2xiMWlZD4"


@time_machine.travel(0.0)
def test_verify_token(mocked_env):
    with mocked_env({"JWT_SECRET_KEY": "test"}):
        verified_data = verify_token(ENCODED_TOKEN)
        assert verified_data.role == PlayerRole.admin
        assert verified_data.room_id == 1


@pytest.mark.asyncio
async def test_current_player_data_no_token():
    user = await current_player_data()
    assert user is None


@pytest.mark.asyncio
@time_machine.travel(0.0)
async def test_current_player_data_with_token():
    user = await current_player_data(authorization=ENCODED_TOKEN)
    assert user is not None
    assert user.role == PlayerRole.admin
    assert user.room_id == 1


def test_add_authorization_cookie() -> None:
    response = MagicMock()
    response.set_cookie = MagicMock()
    token = ENCODED_TOKEN
    add_authorization_cookie(response, token)
    response.set_cookie.assert_called_once_with(AUTHORIZATION_COOKIE, ENCODED_TOKEN, httponly=True)
