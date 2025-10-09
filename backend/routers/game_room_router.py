from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session
from starlette import status
from starlette.responses import Response

from backend.dependencies import get_event_store, get_event_bus
from backend.events.bus import EventBus
from backend.infra.memory_event_store import MemoryEventStore
from backend.models.game_player_model import GamePlayerModel, UserRole
from backend.models.game_room_model import GameRoomModel, GameType
from backend.services.game_room_service import (
    GameRoomService,
)
from backend.utils.db import get_session
from backend.utils.errors import ErrorCode, APIException, ApiErrorDetail
from backend.utils.security import current_player_data, add_authorization_cookie, create_access_token, \
    remove_authorization_cookie

router = APIRouter(prefix="/game_rooms", tags=["game_rooms"])


class CreateGameRoomData(BaseModel):
    game_type: GameType
    password: str
    user_name: str


class CreateGameRoomResponse(BaseModel):
    game_room: GameRoomModel
    player: GamePlayerModel


@router.post(
    "/",
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ApiErrorDetail,
            "description": "User is already in a game room",
        }
    }
)
async def create_game_room(
        response: Response,
        game_data: CreateGameRoomData,
        session: Session = Depends(get_session),
        player_data: GamePlayerModel | None = Depends(current_player_data),
        event_store: MemoryEventStore = Depends(get_event_store),
        event_bus: EventBus = Depends(get_event_bus)
) -> CreateGameRoomResponse:
    if player_data is not None:
        raise APIException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ApiErrorDetail(
                code=ErrorCode.ALREADY_IN_GAME_ROOM,
                message="You are already in a game room, cannot create a new one",
                room_id=player_data.room_id,
                role=player_data.role,
            ),
        )
    try:
        game_room = GameRoomService.create(session, game_data.game_type, game_data.password)
        # Once again I still don't understand why this is necessary
        game_room_copy = game_room.model_copy()

        if not game_room.id:
            raise APIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ApiErrorDetail(
                    code=ErrorCode.INTERNAL_ERROR,
                    message="Failed to create game room",
                ),
            )

        player = await GameRoomService.add_user(
            session,
            game_room.id,
            UserRole.admin,
            game_data.user_name,
            event_store,
            event_bus
        )
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

    except GameRoomService.PasswordAlreadyInUse:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.PASSWORD_USED,
                "message": "The password is already in use",
            },
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


class GetGameRoomResponse(BaseModel):
    game_room: GameRoomModel
    current_player: GamePlayerModel | None = None


@router.get(
    "/data/{game_room_id}/",
    response_model=GetGameRoomResponse,
)
async def get_game_room(
        game_room_id: int,
        password: str | None = None,
        session: Session = Depends(get_session),
        current_player: GamePlayerModel | None = Depends(current_player_data)
):
    try:
        game_room = GameRoomService.get_or_error(session, game_room_id)

        if current_player is not None and current_player.room_id == game_room_id:
            return GetGameRoomResponse(
                game_room=game_room,
                current_player=current_player
            )

        if game_room.password != password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": ErrorCode.PASSWORD_INVALID,
                    "message": "Invalid or missing password",
                }
            )
        return GetGameRoomResponse(
            game_room=game_room,
            current_player=None
        )
    except GameRoomService.GameRoomDoesNotExist:
        raise HTTPException(
            status_code=404,
            detail={
                "code": ErrorCode.GAME_ROOM_DOES_NOT_EXIST,
                "message": "The requested game room does not exist",
            }
        )


@router.get(
    "/find",
    response_model=GameRoomModel,
)
async def find_game_room_by_password(
        password: str, session: Session = Depends(get_session)
):
    if not password:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ApiErrorDetail(
                code=ErrorCode.MISSING_QUERY_PARAMS,
                message="Missing required query parameter: password",
            )
        )

    game_room = GameRoomService.find_by_password(session, password)

    if not game_room:
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiErrorDetail(
                code=ErrorCode.GAME_ROOM_DOES_NOT_EXIST,
                message="Game room with the given password not found",
            ),
        )
    return game_room


@router.post(
    '/join/{game_room_id}',
)
async def join_game_room(
        game_room_id: int,
        password: str,
        user_name: str,
        response: Response,
        session: Session = Depends(get_session),
        event_store: MemoryEventStore = Depends(get_event_store),
        event_bus: EventBus = Depends(get_event_bus)
) -> GamePlayerModel:
    game_room = GameRoomService.find_by_password(session, password)
    if not game_room:
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiErrorDetail(
                code=ErrorCode.GAME_ROOM_DOES_NOT_EXIST,
                message="Game room with the given password not found"
            )
        )

    try:
        user = await GameRoomService.add_user(
            session=session,
            game_room_id=game_room_id,
            role=UserRole.player,
            user_name=user_name,
            event_store=event_store,
            event_bus=event_bus
        )
        add_authorization_cookie(response, create_access_token(user))
        return user
    except GameRoomService.GameRoomIsFull:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": ErrorCode.ROOM_FULL,
                "message": "The game room is full",
            },
        )


class LeaveGameRoomResponse(BaseModel):
    message: str


@router.post(
    '/leave',
)
async def leave_game_room(
        response: Response,
        session: Session = Depends(get_session),
        player_data: GamePlayerModel | None = Depends(current_player_data),
        event_store: MemoryEventStore = Depends(get_event_store),
        event_bus: EventBus = Depends(get_event_bus)
) -> LeaveGameRoomResponse:
    if player_data is None:
        raise APIException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ApiErrorDetail(
                code=ErrorCode.NOT_IN_GAME_ROOM,
                message="You are not in a game room",
            ),
        )

    await GameRoomService.remove_user(
        session=session,
        player_id=player_data.id,
        event_store=event_store,
        event_bus=event_bus,
    )
    remove_authorization_cookie(response)

    return LeaveGameRoomResponse(
        message="You have successfully left the game room",
    )


class EndGameRoomResponse(BaseModel):
    success: bool
    message: str


@router.post(
    '/{game_room_id}/end/',
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": ApiErrorDetail,
            "description": "User is not admin or not in the game room",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ApiErrorDetail,
            "description": "Game room does not exist",
        },
    }
)
async def end_game_room(
        game_room_id: int,
        session: Session = Depends(get_session),
        player_data: GamePlayerModel | None = Depends(current_player_data),
        event_store: MemoryEventStore = Depends(get_event_store),
        event_bus: EventBus = Depends(get_event_bus)
) -> EndGameRoomResponse:
    if player_data is None or player_data.role != UserRole.admin or player_data.room_id != game_room_id:
        raise APIException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ApiErrorDetail(
                code=ErrorCode.FORBIDDEN,
                message="You do not have permission to end this game room",
                role=player_data.role if player_data else None,
                room_id=player_data.room_id if player_data else None,
                id=player_data.id if player_data else None,
            )
        )
    try:
        success = await GameRoomService.end_game_room(
            session=session,
            game_room_id=game_room_id,
            event_store=event_store,
            event_bus=event_bus
        )
        return EndGameRoomResponse(
            success=success,
            message="Game room ended successfully" if success else "Failed to end the game room",
        )
    except GameRoomService.GameRoomDoesNotExist:
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ApiErrorDetail(
                code=ErrorCode.GAME_ROOM_DOES_NOT_EXIST,
                message="The requested game room does not exist",
            )
        )
