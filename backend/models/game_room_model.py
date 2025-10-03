import enum
from datetime import datetime

from sqlalchemy import Column, Enum
from sqlmodel import SQLModel, Field


class GameType(str, enum.Enum):
    connect_four = "connect_four"


class GameRoomModel(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(default_factory=lambda: datetime.now())
    password: str
    game_type: GameType = Field(
        sa_column=Column(Enum(GameType)), default=GameType.connect_four
    )
    is_active: bool = Field(default=True)
