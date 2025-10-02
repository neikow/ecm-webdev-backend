from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session
from starlette import status
from starlette.responses import Response

from backend.models.game_room_model import GameRoomModel, GameType
from backend.services.game_room_service import (
    GameRoomService,
    GameRoomDoesNotExist,
    PasswordAlreadyInUse,
)
from backend.utils.db import get_session
from backend.utils.security import PlayerData, current_player_data, add_authorization_cookie, create_access_token, \
    PlayerRole

router = APIRouter(prefix="/game_rooms", tags=["game_rooms"])


class CreateGameRoomData(BaseModel):
    game_type: GameType
    password: str


@router.post(
    "/",
    response_model=GameRoomModel,
)
async def create_game_room(
        response: Response,
        game_data: CreateGameRoomData,
        session: Session = Depends(get_session),
        player_data: PlayerData | None = Depends(current_player_data),
):
    if player_data is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are already in a game room",
        )
    try:
        game_room = GameRoomService.create(session, game_data.game_type, game_data.password)
        add_authorization_cookie(
            response,
            create_access_token(
                PlayerData(
                    role=PlayerRole.admin, room_id=game_room.id
                )
            ))

        return game_room
    except PasswordAlreadyInUse:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password already in use by an active game room",
        )


class PublicGameRoomModel(BaseModel):
    id: int
    game_type: GameType


class GameRoomListResponse(BaseModel):
    data: list[PublicGameRoomModel]


@router.get("/", response_model=GameRoomListResponse)
async def get_game_rooms(session: Session = Depends(get_session)):
    game_rooms = GameRoomService.list_all(session)
    return GameRoomListResponse(
        data=[
            PublicGameRoomModel(id=game_room.id, game_type=game_room.game_type)
            for game_room in game_rooms
            if game_room.id
        ]
    )


@router.get(
    "/data/{game_room_id}",
    response_model=GameRoomModel,
)
async def get_game_room(
        game_room_id: int, password: str, session: Session = Depends(get_session)
):
    try:
        game_service = GameRoomService.get_or_error(session, game_room_id)
        if game_service.password != password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
            )
        return game_service
    except GameRoomDoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/find-by-password",
    response_model=GameRoomModel,
)
async def find_game_room_by_password(
        password: str, session: Session = Depends(get_session)
):
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password query parameter is required",
        )

    game_room = GameRoomService.find_by_password(session, password)
    if not game_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game room with the given password not found",
        )
    return game_room

# async def test(user: PlayerData | None = Depends(current_user_data)):
#     if user is None:
#         return {"message": "No user"}
#     return {"message": f"User role: {user.role}, room_id: {user.room_id}"}
