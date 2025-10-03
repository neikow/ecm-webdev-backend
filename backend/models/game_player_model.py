import enum

from nanoid import generate as generate_nanoid
from sqlmodel import SQLModel, Field


class UserRole(str, enum.Enum):
    admin = "admin"
    player = "player"


class GamePlayerModel(SQLModel, table=True):
    id: str = Field(default_factory=lambda: generate_nanoid(), primary_key=True)
    user_name: str
    room_id: int
    role: UserRole = Field(default=UserRole.player, index=True)
