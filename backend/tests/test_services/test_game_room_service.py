import pytest

from backend.models.game_room_model import GameType
from backend.services.game_room_service import (
    GameRoomService,
    GameRoomDoesNotExist,
    PasswordAlreadyInUse,
)


def test_game_room_can_be_created(session):
    password = "securepassword"
    game_type = GameType.connect_four

    game_room = GameRoomService.create(session, game_type, password)

    assert game_room is not None
    assert game_room.id is not None
    assert game_room.password == password
    assert game_room.game_type == game_type
    assert game_room.is_active is True


def test_is_password_in_use_by_active_game_room(session):
    password = "securepassword"
    game_type = GameType.connect_four

    game_room = GameRoomService.create(session, game_type, password)
    assert game_room is not None
    assert (
        GameRoomService.is_password_in_use_by_active_game_room(session, password)
        is True
    )


def test_game_room_cannot_be_created_if_password_already_in_use_by_an_active_room(
    session,
):
    password = "securepassword"
    game_type = GameType.connect_four

    game_room1 = GameRoomService.create(session, game_type, password)
    assert game_room1 is not None

    with pytest.raises(PasswordAlreadyInUse):
        GameRoomService.create(session, game_type, password)


def test_game_room_get_or_error_existing(session):
    password = "securepassword"
    game_type = GameType.connect_four

    create_game_room = GameRoomService.create(session, game_type, password)
    assert create_game_room is not None

    game_room = GameRoomService.get_or_error(session, create_game_room.id)

    assert game_room is not None


def test_game_room_get_or_error_non_existing(session):
    non_existing_id = -1

    try:
        GameRoomService.get_or_error(session, non_existing_id)
    except GameRoomDoesNotExist as e:
        assert str(e) == f"Game room with id {non_existing_id} not found"
    else:
        assert False, "Expected ValueError was not raised"


def test_game_room_check_password_with_password(session):
    password = "securepassword"
    game_type = GameType.connect_four

    create_game_room = GameRoomService.create(session, game_type, password)
    assert create_game_room is not None

    assert (
        GameRoomService.check_password(session, create_game_room.id, password) is True
    )


def test_list_all(session):
    password1 = "securepassword1"
    password2 = "securepassword2"
    game_type = GameType.connect_four

    create_game_room1 = GameRoomService.create(session, game_type, password1)
    create_game_room2 = GameRoomService.create(session, game_type, password2)

    game_rooms = GameRoomService.list_all(session)

    assert len(game_rooms) >= 2
    assert create_game_room1 in game_rooms
    assert create_game_room2 in game_rooms


def test_game_room_check_password_with_wrong_password(session):
    password = "securepassword"
    wrong_password = "wrongpassword"
    game_type = GameType.connect_four

    create_game_room = GameRoomService.create(session, game_type, password)
    assert create_game_room is not None

    assert (
        GameRoomService.check_password(session, create_game_room.id, wrong_password)
        is False
    )


def test_find_game_room_by_password(session):
    password = "securepassword"
    game_type = GameType.connect_four

    create_game_room = GameRoomService.create(session, game_type, password)
    found_game_room = GameRoomService.find_by_password(session, password)

    assert found_game_room is not None
    assert found_game_room.id == create_game_room.id
    assert found_game_room.password == create_game_room.password
    assert found_game_room.game_type == create_game_room.game_type
