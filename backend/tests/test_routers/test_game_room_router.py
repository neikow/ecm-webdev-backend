from starlette import status

from backend.models.game_room_model import GameType
from backend.services.game_room_service import GameRoomService
from backend.utils.security import create_access_token, PlayerData, AUTHORIZATION_COOKIE
from backend.utils.security import verify_token, PlayerRole


def test_get_index(session, client):
    game_room = GameRoomService.create(
        session, game_type=GameType.connect_four, password="secret"
    )
    response = client.get("/game_rooms/")

    assert response.status_code == 200
    json = response.json()
    assert json["data"] is not None
    assert json == {"data": [{"id": game_room.id, "game_type": game_room.game_type}]}


def test_create_game_room(session, client):
    response = client.post(
        "/game_rooms/",
        json={"game_type": GameType.connect_four, "password": "secretpassword"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None


def test_get_game_room_with_valid_password(session, client):
    game_room = GameRoomService.create(
        session, game_type=GameType.connect_four, password="secret"
    )

    response = client.get(f"/game_rooms/data/{game_room.id}?password=secret")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == game_room.id
    assert data["game_type"] == game_room.game_type
    assert data["password"] == game_room.password


def test_fail_to_get_game_room_with_invalid_password(session, client):
    game_room = GameRoomService.create(
        session, game_type=GameType.connect_four, password="secret"
    )

    response = client.get(f"/game_rooms/data/{game_room.id}?password=wrongpassword")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] == f"Invalid password"


def test_fail_to_get_unknown_game_room(session, client):
    response = client.get(f"/game_rooms/-1?password=wrongpassword")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == f"Not Found"


def test_fail_to_find_game_room_by_empty_password(session, client):
    response = client.get(f"/game_rooms/find-by-password?password=")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Password query parameter is required"


def test_creating_game_room_sets_the_user_as_admin(session, client):
    response = client.post(
        "/game_rooms/",
        json={"game_type": GameType.connect_four, "password": "secretpassword"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] is not None
    assert AUTHORIZATION_COOKIE in response.cookies
    token = response.cookies[AUTHORIZATION_COOKIE]
    assert token is not None

    player_data = verify_token(token)
    assert player_data.role == PlayerRole.admin
    assert player_data.room_id == data["id"]


def test_fail_to_create_game_room_if_the_user_is_in_game_room(session, client):
    client.cookies[AUTHORIZATION_COOKIE] = create_access_token(PlayerData(
        role=PlayerRole.default,
        room_id=1,
    ))

    response = client.post(
        "/game_rooms/",
        json={"game_type": GameType.connect_four, "password": "anothersecret"},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["detail"] == "You are already in a game room"
