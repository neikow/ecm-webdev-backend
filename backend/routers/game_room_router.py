from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session
from starlette import status
from starlette.responses import Response
from starlette.websockets import WebSocket

from backend.models.game_player_model import GamePlayerModel, UserRole
from backend.models.game_room_model import GameRoomModel, GameType
from backend.services.game_room_service import (
    GameRoomService,
    GameRoomDoesNotExist,
    PasswordAlreadyInUse,
)
from backend.utils.db import get_session
from backend.utils.errors import ErrorCode
from backend.utils.security import current_player_data, add_authorization_cookie, create_access_token, \
    remove_authorization_cookie

router = APIRouter(prefix="/game_rooms", tags=["game_rooms"])


class CreateGameRoomData(BaseModel):
    game_type: GameType
    password: str


class CreateGameRoomResponse(BaseModel):
    game_room: GameRoomModel
    player: GamePlayerModel


@router.post(
    "/",
)
async def create_game_room(
        response: Response,
        game_data: CreateGameRoomData,
        session: Session = Depends(get_session),
        player_data: GamePlayerModel | None = Depends(current_player_data),
) -> CreateGameRoomResponse:
    if player_data is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": ErrorCode.ALREADY_IN_GAME_ROOM,
                "message": "You are already in a game room, cannot create a new one",
                "room_id": player_data.room_id,
                "role": player_data.role,
            },
        )
    try:
        game_room = GameRoomService.create(session, game_data.game_type, game_data.password)
        # Once again I still don't understand why this is necessary
        game_room_copy = game_room.model_copy()
        player = GameRoomService.add_user(session, game_room.id, UserRole.admin)
        add_authorization_cookie(
            response,
            create_access_token(
                player
            )
        )

        response.status_code = status.HTTP_201_CREATED
        return CreateGameRoomResponse(
            game_room=game_room_copy,
            player=player,
        )

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
        game_room_id: int,
        password: str | None = None,
        session: Session = Depends(get_session),
        current_player: GamePlayerModel | None = Depends(current_player_data)
):
    try:
        game_service = GameRoomService.get_or_error(session, game_room_id)

        if current_player is not None and current_player.room_id == game_room_id:
            return game_service

        if game_service.password != password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing password"
            )
        return game_service
    except GameRoomDoesNotExist as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/find",
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


@router.post(
    '/join/{game_room_id}',
)
async def join_game_room(
        game_room_id: int,
        password: str,
        response: Response,
        session: Session = Depends(get_session),
) -> GamePlayerModel:
    game_room = GameRoomService.find_by_password(session, password)
    if not game_room:
        raise GameRoomDoesNotExist

    user = GameRoomService.add_user(session, game_room_id, UserRole.player)
    add_authorization_cookie(response, create_access_token(user))
    return user


class LeaveGameRoomResponse(BaseModel):
    message: str


@router.post(
    '/leave',
)
async def leave_game_room(
        response: Response,
        session: Session = Depends(get_session),
        player_data: GamePlayerModel | None = Depends(current_player_data),
) -> LeaveGameRoomResponse:
    if player_data is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": ErrorCode.NOT_IN_GAME_ROOM,
                "message": "You are not in a game room",
            },
        )
    try:
        GameRoomService.remove_user(session, player_data.id)

        remove_authorization_cookie(response)
        return LeaveGameRoomResponse(
            message="You have successfully left the game room",
        )
    except GameRoomDoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": ErrorCode.NOT_IN_GAME_ROOM,
                "message": "You are not in a game room",
            },
        )


def dispatch(websocket: WebSocket, game_room_id: int, data: dict) -> None:
    pass


@router.websocket("/{game_room_id}/ws")
async def websocket_endpoint(
        game_room_id: int,
        websocket: WebSocket
):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        dispatch(websocket, game_room_id, data)
