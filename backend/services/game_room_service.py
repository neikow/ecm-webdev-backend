from typing import Sequence

from sqlmodel import Session, select

from backend.models.game_room_model import GameType, GameRoomModel


class GameRoomDoesNotExist(Exception):
    pass


class InvalidGameRoomPassword(Exception):
    pass


class PasswordAlreadyInUse(Exception):
    pass


class GameRoomService:
    @staticmethod
    def is_password_in_use_by_active_game_room(session: Session, password: str) -> bool:
        statement = select(GameRoomModel.id).where(
            GameRoomModel.password == password, GameRoomModel.is_active == True
        )
        game_room = session.exec(statement).first()
        return game_room is not None

    @staticmethod
    def create(
        session: Session,
        game_type: GameType,
        password: str,
    ) -> GameRoomModel:
        if GameRoomService.is_password_in_use_by_active_game_room(session, password):
            raise PasswordAlreadyInUse

        game_room = GameRoomModel(
            game_type=game_type,
            password=password,
        )
        session.add(game_room)
        session.commit()
        session.refresh(game_room)
        return game_room

    @staticmethod
    def get_or_error(session: Session, game_room_id: int) -> GameRoomModel:
        statement = select(GameRoomModel).where(GameRoomModel.id == game_room_id)
        game_room = session.exec(statement).first()
        if not game_room:
            raise GameRoomDoesNotExist(f"Game room with id {game_room_id} not found")
        return game_room

    @staticmethod
    def check_password(session: Session, game_room_id: int, password: str) -> bool:
        game_room = GameRoomService.get_or_error(session, game_room_id)
        if not game_room:
            raise GameRoomDoesNotExist(f"Game room with id {game_room_id} not found")
        return game_room.password == password

    @staticmethod
    def find_by_password(session: Session, password: str) -> GameRoomModel | None:
        statement = select(GameRoomModel).where(
            GameRoomModel.password == password, GameRoomModel.is_active == True
        )
        return session.exec(statement).first()

    @staticmethod
    def list_all(session: Session) -> Sequence[GameRoomModel]:
        statement = select(GameRoomModel).where(GameRoomModel.is_active == True)
        game_rooms = session.exec(statement).all()
        return game_rooms
