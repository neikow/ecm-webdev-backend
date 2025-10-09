from datetime import timedelta

import pytest
from starlette import status

from backend.models.game_player_model import UserRole
from backend.models.game_room_model import GameType
from backend.services.game_room_service import GameRoomService
from backend.utils.security import REFRESH_COOKIE, create_refresh_token, RefreshTokenData, AUTHORIZATION_COOKIE


@pytest.mark.asyncio
async def test_refresh_token_authed_player(client, session, mock_event_bus, mock_event_store):
    game_room = GameRoomService.create(
        session=session,
        game_type=GameType.connect_four,
        password="test_password",
    )
    player = await GameRoomService.add_user(
        session=session,
        game_room_id=game_room.id,
        user_name="test",
        role=UserRole.admin,
        event_bus=mock_event_bus,
        event_store=mock_event_store,
    )

    initial_refresh = create_refresh_token(
        RefreshTokenData(
            player_id=player.id,
            room_id=player.room_id
        ),
        expires_delta=timedelta(days=7)
    )
    client.cookies[REFRESH_COOKIE] = initial_refresh

    response = client.post("/game_auth/refresh")

    assert response.status_code == status.HTTP_200_OK
    assert AUTHORIZATION_COOKIE in response.cookies
    assert REFRESH_COOKIE in response.cookies
    assert response.cookies[AUTHORIZATION_COOKIE] is not None
    assert response.cookies[REFRESH_COOKIE] != initial_refresh


@pytest.mark.asyncio
async def test_refresh_token_should_return_401_if_no_refresh_token(client):
    response = client.post("/game_auth/refresh")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "code": "no_refresh",
        "message": "No refresh token provided",
        "should_refresh_token": True
    }


@pytest.mark.asyncio
async def test_refresh_token_should_return_401_if_invalid_refresh_token(client):
    client.cookies[REFRESH_COOKIE] = "invalid_token"
    response = client.post("/game_auth/refresh")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "code": "no_refresh",
        "message": "Invalid or expired refresh token",
        "should_refresh_token": True
    }


@pytest.mark.asyncio
async def test_refresh_token_should_return_401_if_the_user_is_not_in_a_game(client):
    initial_refresh = create_refresh_token(
        RefreshTokenData(
            player_id="non_existent_player",
            room_id=1
        ),
        expires_delta=timedelta(days=7)
    )
    client.cookies[REFRESH_COOKIE] = initial_refresh

    response = client.post("/game_auth/refresh")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "code": "no_refresh",
        "message": "Invalid or expired refresh token",
        "should_refresh_token": True
    }
