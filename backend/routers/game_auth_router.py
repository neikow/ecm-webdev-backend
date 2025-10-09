from typing import Annotated

from fastapi import APIRouter, Response, Cookie, Depends
from sqlmodel import Session, select
from starlette import status

from backend.models.game_player_model import GamePlayerModel
from backend.utils.db import get_session
from backend.utils.errors import APIException, ApiErrorDetail, ErrorCode
from backend.utils.security import verify_refresh_token, InvalidTokenError, TokenExpiredError, \
    remove_authorization_cookie, remove_refresh_cookie, create_access_token, AccessTokenData, create_refresh_token, \
    RefreshTokenData, add_access_cookie, add_refresh_cookie, FailedToDecodeToken

router = APIRouter(prefix="/game_auth", tags=['auth'])


@router.post("/refresh")
async def refresh_token(
        response: Response,
        session: Session = Depends(get_session),
        refresh: Annotated[str | None, Cookie()] = None
):
    if not refresh:
        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ApiErrorDetail(
                code=ErrorCode.NO_REFRESH_TOKEN,
                message="No refresh token provided"
            )
        )

    try:
        refresh_data = verify_refresh_token(refresh)
        statement = select(GamePlayerModel).where(
            GamePlayerModel.id == refresh_data.player_id,
            GamePlayerModel.room_id == refresh_data.room_id
        )
        game_player = session.exec(statement).first()
        if not game_player:
            raise InvalidTokenError

    except (InvalidTokenError, TokenExpiredError, FailedToDecodeToken):
        remove_authorization_cookie(response)
        remove_refresh_cookie(response)

        raise APIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ApiErrorDetail(
                code=ErrorCode.NO_REFRESH_TOKEN,
                message="Invalid or expired refresh token"
            )
        )

    new_access = create_access_token(
        AccessTokenData(
            player=game_player
        )
    )
    new_refresh = create_refresh_token(
        RefreshTokenData(
            player_id=game_player.id,
            room_id=game_player.room_id
        )
    )

    add_access_cookie(response, new_access)
    add_refresh_cookie(response, new_refresh)

    response.status_code = status.HTTP_200_OK
