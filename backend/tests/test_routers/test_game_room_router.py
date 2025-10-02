from starlette import status

from backend.models.game_room_model import GameType
from backend.services.game_room_service import GameRoomService


def test_get_index(session, client):
    game_room = GameRoomService.create(session, game_type=GameType.connect_four, password="secret")
    print(id(session))
    response = client.get("/game_rooms/")

    assert response.status_code == 200
    json = response.json()
    assert json["data"] is not None
    assert json == {
        "data": [
            {
                "id": game_room.id,
                "game_type": game_room.game_type
            }
        ]
    }


def test_create_game_room(session, client):
    response = client.post(
        "/game_rooms/",
        json={
            "game_type": GameType.connect_four,
            "password": "secretpassword"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None


def test_get_game_room_with_valid_password(session, client):
    game_room = GameRoomService.create(
        session,
        game_type=GameType.connect_four,
        password="secret"
    )

    response = client.get(f"/game_rooms/{game_room.id}?password=secret")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == game_room.id
    assert data["game_type"] == game_room.game_type
    assert data["password"] == game_room.password


def test_fail_to_get_game_room_with_invalid_password(session, client):
    game_room = GameRoomService.create(
        session,
        game_type=GameType.connect_four,
        password="secret"
    )

    response = client.get(f"/game_rooms/{game_room.id}?password=wrongpassword")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] == f"Invalid password"


def test_fail_to_get_unknown_game_room(session, client):
    response = client.get(f"/game_rooms/-1?password=wrongpassword")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == f"Game room with id -1 not found"
