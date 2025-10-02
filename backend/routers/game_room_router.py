from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session
from starlette import status

from backend.models.game_room_model import GameRoomModel, GameType
from backend.services.game_room_service import GameRoomService, GameRoomDoesNotExist
from backend.utils.db import get_session

router = APIRouter(prefix="/game_rooms", tags=["game_rooms"])


class CreateGameRoomData(BaseModel):
    game_type: GameType
    password: str


@router.post(
    "/",
    response_model=GameRoomModel,
)
async def create_game_room(
        game_data: CreateGameRoomData,
        session: Session = Depends(get_session)
):
    return GameRoomService.create(
        session,
        game_data.game_type,
        game_data.password
    )


class PublicGameRoomModel(BaseModel):
    id: int
    game_type: GameType


class GameRoomListResponse(BaseModel):
    data: list[PublicGameRoomModel]


@router.get(
    "/",
    response_model=GameRoomListResponse
)
async def get_game_rooms(session: Session = Depends(get_session)):
    game_rooms = GameRoomService.list_all(session)
    return GameRoomListResponse(data=[
        PublicGameRoomModel(
            id=game_room.id,
            game_type=game_room.game_type
        ) for game_room in game_rooms if game_room.id
    ])


@router.get(
    "/{game_room_id}",
    response_model=GameRoomModel,
)
async def get_game_room(
        game_room_id: int,
        password: str,
        session: Session = Depends(get_session)
):
    try:
        game_service = GameRoomService.get_or_error(session, game_room_id)
        if game_service.password != password:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
        return game_service
    except GameRoomDoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))
