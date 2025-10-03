from unittest.mock import MagicMock

import pytest
import time_machine

from backend.models.game_player_model import GamePlayerModel, UserRole
from backend.utils.security import (
    create_access_token,
    verify_token,
    current_player_data, add_authorization_cookie, AUTHORIZATION_COOKIE, remove_authorization_cookie
)


@time_machine.travel(0.0)
def test_create_access_token(mocked_env, snapshot):
    with mocked_env({"JWT_SECRET_KEY": "test"}):
        token_data = GamePlayerModel(role=UserRole.admin, room_id=1, id="nanoid")
        encoded_token = create_access_token(token_data)
        assert encoded_token is not None
        assert encoded_token == snapshot


# Precomputed token for data: {"role": "admin", "room_id": 1, "id": "nanoid", "exp": 900}
ENCODED_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6Im5hbm9pZCIsInJvb21faWQiOjEsInJvbGUiOiJhZG1pbiIsImV4cCI6OTAwfQ.YLz0ED-y0w9BtLFTdT2tNX9XD8VkTwXwREDTwtWleTU"


@time_machine.travel(0.0)
def test_verify_token(mocked_env):
    with mocked_env({"JWT_SECRET_KEY": "test"}):
        verified_data = verify_token(ENCODED_TOKEN)
        assert verified_data.role == UserRole.admin
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
    assert user.role == UserRole.admin
    assert user.room_id == 1


def test_add_authorization_cookie() -> None:
    response = MagicMock()
    response.set_cookie = MagicMock()
    token = ENCODED_TOKEN
    add_authorization_cookie(response, token)
    response.set_cookie.assert_called_once_with(AUTHORIZATION_COOKIE, ENCODED_TOKEN, httponly=True)


def test_remove_authorization_cookie() -> None:
    response = MagicMock()
    response.set_cookie = MagicMock()
    remove_authorization_cookie(response)
    response.set_cookie.assert_called_once_with(AUTHORIZATION_COOKIE, expires=0, max_age=0, httponly=True)
