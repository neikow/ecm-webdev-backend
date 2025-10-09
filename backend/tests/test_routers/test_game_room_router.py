import pytest
import time_machine
from starlette import status

from backend.models.game_player_model import GamePlayerModel, UserRole
from backend.models.game_room_model import GameType
from backend.services.game_room_service import GameRoomService
from backend.utils.errors import ErrorCode, ApiErrorDetail
from backend.utils.game_utils import get_room_max_users
from backend.utils.security import create_access_token, AUTHORIZATION_COOKIE
from backend.utils.security import verify_token


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
        json={
            "game_type": GameType.connect_four,
            "password": "secretpassword",
            "user_name": "admin"
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    json = response.json()
    assert json["game_room"] is not None
    assert json["game_room"]["id"] is not None
    assert json["player"] is not None
    assert json["player"]["id"] is not None
    assert json["player"]["user_name"] == "admin"


def test_get_game_room_with_valid_password(session, client):
    game_room = GameRoomService.create(
        session, game_type=GameType.connect_four, password="secret"
    )

    response = client.get(f"/game_rooms/data/{game_room.id}?password=secret")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    current_player_data = data["current_player"]
    assert current_player_data is None

    game_room_data = data["game_room"]
    assert game_room_data["id"] == game_room.id
    assert game_room_data["game_type"] == game_room.game_type
    assert game_room_data["password"] == game_room.password


def test_fail_to_get_game_room_with_invalid_password(session, client):
    game_room = GameRoomService.create(
        session, game_type=GameType.connect_four, password="secret"
    )

    response = client.get(f"/game_rooms/data/{game_room.id}?password=wrongpassword")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] == {
        "code": 'password_invalid',
        "message": "Invalid or missing password",
    }


def test_get_game_room_data_with_authentication_but_no_password(session, client):
    game_room = GameRoomService.create(
        session, game_type=GameType.connect_four, password="secret"
    )

    client.cookies[AUTHORIZATION_COOKIE] = create_access_token(
        GamePlayerModel(
            role=UserRole.player,
            room_id=game_room.id,
        )
    )

    response = client.get(f"/game_rooms/data/{game_room.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    current_player_data = data["current_player"]
    assert current_player_data is not None
    assert current_player_data["role"] == UserRole.player
    assert current_player_data["room_id"] == game_room.id
    assert current_player_data["id"] is not None

    game_room_data = data["game_room"]

    assert game_room_data["id"] == game_room.id
    assert game_room_data["game_type"] == game_room.game_type
    assert game_room_data["password"] == game_room.password


def test_get_game_room_returns_the_user_id_in_the_response(session, client):
    game_room = GameRoomService.create(
        session, game_type=GameType.connect_four, password="secret"
    )

    client.cookies[AUTHORIZATION_COOKIE] = create_access_token(
        GamePlayerModel(
            role=UserRole.player,
            room_id=game_room.id,
            id="42",
        )
    )

    response = client.get(f"/game_rooms/data/{game_room.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    game_room_data = data["game_room"]
    current_player_data = data["current_player"]
    assert game_room_data["id"] == game_room.id
    assert game_room_data["game_type"] == game_room.game_type
    assert game_room_data["password"] == game_room.password
    assert current_player_data["id"] == "42"


def test_fail_to_get_unknown_game_room(session, client):
    response = client.get(f"/game_rooms/-1?password=wrongpassword")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == f"Not Found"


def test_fail_to_find_game_room_by_empty_password(session, client):
    response = client.get(f"/game_rooms/find?password=")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data == ApiErrorDetail(
        code=ErrorCode.MISSING_QUERY_PARAMS,
        message="Missing required query parameter: password"
    ).model_dump()


def test_creating_game_room_sets_the_user_as_admin(session, client):
    response = client.post(
        "/game_rooms/",
        json={
            "game_type": GameType.connect_four,
            "password": "secretpassword",
            "user_name": "admin"
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["game_room"]["id"] is not None
    assert data["player"]["id"] is not None
    assert data["player"]["user_name"] == "admin"
    assert data["player"]["role"] == UserRole.admin
    assert AUTHORIZATION_COOKIE in response.cookies
    token = response.cookies[AUTHORIZATION_COOKIE]
    assert token is not None

    player_data = verify_token(token)
    assert player_data.role == UserRole.admin
    assert player_data.room_id == data["game_room"]["id"]


def test_fail_to_create_game_room_if_the_user_is_in_game_room(session, client):
    client.cookies[AUTHORIZATION_COOKIE] = create_access_token(GamePlayerModel(
        role=UserRole.player,
        room_id=1,
    ))

    response = client.post(
        "/game_rooms/",
        json={
            "game_type": GameType.connect_four,
            "password": "anothersecret",
            "user_name": "admin"
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()

    assert data == ApiErrorDetail(
        code=ErrorCode.ALREADY_IN_GAME_ROOM,
        message='You are already in a game room, cannot create a new one',
        role='player',
        room_id=1,
    ).model_dump()


def test_join_game_room(session, client):
    game_room_password = "secret"
    user_name = "admin"
    game_room = GameRoomService.create(
        session, game_type=GameType.connect_four, password=game_room_password
    )
    assert client.cookies.get(AUTHORIZATION_COOKIE) is None
    response = client.post(
        f"/game_rooms/join/{game_room.id}?password={game_room_password}&user_name={user_name}"
    )
    assert client.cookies.get(AUTHORIZATION_COOKIE) is not None
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["role"] == UserRole.player
    assert data["room_id"] == game_room.id
    assert data["user_name"] == user_name
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_fail_to_join_full_game_room(
        session,
        client,
        mock_event_store,
        mock_event_bus,
):
    game_room = GameRoomService.create(
        session, game_type=GameType.connect_four, password="secret"
    )
    max_users = get_room_max_users(game_room.game_type)

    for _ in range(max_users):
        await GameRoomService.add_user(
            session=session,
            game_room_id=game_room.id,
            role=UserRole.player,
            user_name="player",
            event_store=mock_event_store,
            event_bus=mock_event_bus,
        )

    response = client.post(f"/game_rooms/join/{game_room.id}?password=secret&user_name=latecomer")
    assert response.status_code == status.HTTP_409_CONFLICT
    data = response.json()
    assert data["detail"]["code"] == ErrorCode.ROOM_FULL
    assert data["detail"]["message"] == "The game room is full"


@pytest.mark.asyncio
async def test_leave_game_room(
        session,
        client,
        mock_event_store,
        mock_event_bus,
):
    game_room = GameRoomService.create(
        session, game_type=GameType.connect_four, password="<PASSWORD>"
    )
    player = await GameRoomService.add_user(
        session=session,
        game_room_id=game_room.id,
        role=UserRole.player,
        user_name="admin",
        event_store=mock_event_store,
        event_bus=mock_event_bus,
    )
    client.cookies[AUTHORIZATION_COOKIE] = create_access_token(player)

    response = client.post("/game_rooms/leave")
    assert response.status_code == status.HTTP_200_OK
    assert response.cookies.get(AUTHORIZATION_COOKIE) is None
    data = response.json()
    assert data["message"] == "You have successfully left the game room"


@pytest.mark.asyncio
async def test_end_game_room_should_end_an_active_game_when_called_by_admin(
        session,
        client,
        mock_event_store,
        mock_event_bus,
):
    game_room = GameRoomService.create(
        session, game_type=GameType.connect_four, password="<PASSWORD>"
    )

    admin = await GameRoomService.add_user(
        session=session,
        game_room_id=game_room.id,
        role=UserRole.admin,
        user_name="admin",
        event_store=mock_event_store,
        event_bus=mock_event_bus,
    )
    client.cookies[AUTHORIZATION_COOKIE] = create_access_token(admin)

    response = client.post(f"/game_rooms/{game_room.id}/end")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Game room ended successfully"


@pytest.mark.asyncio
async def test_fail_to_end_game_room_when_called_by_non_admin(
        session,
        client,
        mock_event_store,
        mock_event_bus,
):
    game_room = GameRoomService.create(
        session, game_type=GameType.connect_four, password="<PASSWORD>"
    )

    player = await GameRoomService.add_user(
        session=session,
        game_room_id=game_room.id,
        role=UserRole.player,
        user_name="player",
        event_store=mock_event_store,
        event_bus=mock_event_bus,
    )
    client.cookies[AUTHORIZATION_COOKIE] = create_access_token(player)

    response = client.post(f"/game_rooms/{game_room.id}/end")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data == ApiErrorDetail(
        code=ErrorCode.FORBIDDEN,
        message="You do not have permission to end this game room",
        role=UserRole.player,
        room_id=game_room.id,
        id=player.id,
    ).model_dump()


@pytest.mark.asyncio
async def test_fail_to_leave_a_game_room_if_not_in_one(
        session,
        client,
):
    response = client.post("/game_rooms/leave")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data == ApiErrorDetail(
        code=ErrorCode.NOT_IN_GAME_ROOM,
        message="You are not in a game room",
    ).model_dump()


@pytest.mark.asyncio
async def test_fail_to_end_a_game_room_that_does_not_exist(
        session,
        client,
        mock_event_store,
        mock_event_bus,
):
    game_room = GameRoomService.create(
        session, game_type=GameType.connect_four, password="<PASSWORD>"
    )

    admin = await GameRoomService.add_user(
        session=session,
        game_room_id=game_room.id,
        role=UserRole.admin,
        user_name="admin",
        event_store=mock_event_store,
        event_bus=mock_event_bus,
    )
    client.cookies[AUTHORIZATION_COOKIE] = create_access_token(admin)

    session.delete(game_room)
    session.commit()

    response = client.post(f"/game_rooms/{game_room.id}/end")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data == ApiErrorDetail(
        code=ErrorCode.GAME_ROOM_DOES_NOT_EXIST,
        message="The requested game room does not exist"
    ).model_dump()


@pytest.mark.asyncio
async def test_fail_to_join_game_room_if_wrong_password(
        session,
        client,
        mock_event_store,
        mock_event_bus,
):
    game_room = GameRoomService.create(
        session, game_type=GameType.connect_four, password="secret"
    )

    response = client.post(f"/game_rooms/join/{game_room.id}?password=wrongpassword&user_name=latecomer")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data == ApiErrorDetail(
        code=ErrorCode.GAME_ROOM_DOES_NOT_EXIST,
        message="Game room with the given password not found"
    ).model_dump()


@pytest.mark.asyncio
@time_machine.travel("2025-01-01 12:00:00")
def test_find_game_room_by_password_should_return_game_room_data(
        session,
        client
):
    password = "securepassword"
    game_type = GameType.connect_four

    create_game_room = GameRoomService.create(session, game_type, password)

    response = client.get(f"/game_rooms/find?password={password}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data == create_game_room.model_dump(mode="json")


@pytest.mark.asyncio
async def test_fail_to_find_game_room_by_password_if_not_exists(
        session,
        client
):
    response = client.get(f"/game_rooms/find?password=unknownpassword")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data == ApiErrorDetail(
        code=ErrorCode.GAME_ROOM_DOES_NOT_EXIST,
        message="Game room with the given password not found"
    ).model_dump()
