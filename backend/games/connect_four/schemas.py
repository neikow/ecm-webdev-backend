from typing import Annotated

from pydantic import BaseModel, Field

from backend.games.abstract import GameState
from backend.games.connect_four.consts import P_1, P_2, COLUMNS, EMPTY, ROWS


class ConnectFourState(GameState):
    grid: list[list[int]] = Field(default_factory=lambda: [[EMPTY for _ in range(COLUMNS)] for _ in range(ROWS)])
    current_player: int = 0
    winning_positions: list[tuple[int, int]] | None = None


class ConnectFourActionData(BaseModel):
    player: Annotated[
        int,
        Field(ge=P_1, le=P_2)
    ]
    column: Annotated[
        int,
        Field(ge=0, lt=COLUMNS)
    ]
