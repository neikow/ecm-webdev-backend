import enum
from random import randint
from typing import Annotated

from pydantic import BaseModel, Field

from backend.domain.events import BaseEvent, GameEvent
from backend.events.bus import EventBus
from backend.games.abstract import Game, PlayerSpec, Metadata, GameException, GameExceptionType
from backend.infra.memory_event_store import MemoryEventStore
from backend.models.game_room_model import GameRoomModel

ROWS = 6
COLUMNS = 7


class ConnectFourState(str, enum.Enum):
    not_started = "not_started"
    ongoing = "ongoing"
    draw = "draw"
    win = "win"


class ConnectFourGlobalState(BaseModel):
    grid: list[list[int]] = Field(default_factory=lambda: [[0 for _ in range(COLUMNS)] for _ in range(ROWS)])
    current_player: int = 0
    state: ConnectFourState = ConnectFourState.not_started
    winning_positions: list[tuple[int, int]] | None = None


class PlayerActionData(BaseModel):
    player: Annotated[
        int,
        Field(gt=0, lt=3)
    ]
    column: Annotated[
        int,
        Field(ge=0, lt=COLUMNS)
    ]


class ConnectFour(Game):
    metadata = Metadata(
        display_name="Connect Four",
        description="A two-player connection game in which the players first choose a color and then take turns dropping colored discs into a seven-column, six-row vertically suspended grid. The pieces fall straight down, occupying the lowest available space within the column. The objective of the game is to be the first to form a horizontal, vertical, or diagonal line of four of one's own discs. Connect Four is a solved game. The first player can always win by playing the right moves.",
        instructions="""1. The game is played on a grid that is seven columns wide and six rows high.
2. Players take turns dropping one of their colored discs from the top into any of the seven columns.
3. The disc will fall straight down, occupying the lowest available space within the column.
4. The objective of the game is to be the first player to form a horizontal, vertical
    or diagonal line of four of one's own discs.
5. The game ends when a player connects four of their discs in a row, or when the board is full
    and no more moves are possible, resulting in a draw.
6. If a player attempts to drop a disc into a column that is already full, they must choose a different column.
7. Players alternate turns until the game is won or ends in a draw.
8. The game can be played multiple times, with players switching colors after each game if desired.""",
        tags=["abstract", "board", "strategy", "two-player"]
    )

    game_room: GameRoomModel

    _global_state: ConnectFourGlobalState

    def __init__(
            self,
            game_room: GameRoomModel,
            event_store: MemoryEventStore,
            event_bus: EventBus,
    ) -> None:
        self.game_room = game_room
        self._global_state = ConnectFourGlobalState()
        self.event_store = event_store
        self.event_bus = event_bus

    @classmethod
    def get_players_spec(cls) -> PlayerSpec:
        return PlayerSpec(
            min=2,
            max=2,
        )

    async def _handle_game_start(self, event: BaseEvent) -> None:
        if self._global_state.state != ConnectFourState.not_started:
            raise GameException(
                exception_type=GameExceptionType.state_incompatibility,
                message=f"Game has already started."
            )
        self._global_state.state = ConnectFourState.ongoing
        self._global_state.current_player = randint(1, 2)
        event = await self.event_store.append(
            room_id=self.game_room.id,
            event_type=GameEvent.GAME_STATE_UPDATE,
            actor_id=event.actor_id,
            data=self._global_state.model_dump(mode="json"),
        )
        await self.event_bus.publish(event=event)

    @staticmethod
    def _check_winner(grid: list[list[int]], player: int) -> tuple[bool, list[tuple[int, int]]]:
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for row in range(ROWS):
            for col in range(COLUMNS):
                if grid[row][col] != player:
                    continue
                for dr, dc in directions:
                    count = 0
                    winning_positions = []
                    r, c = row, col
                    while 0 <= r < ROWS and 0 <= c < COLUMNS and grid[r][c] == player:
                        winning_positions.append((ROWS - r - 1, c))
                        count += 1
                        if count == 4:
                            return True, winning_positions
                        r += dr
                        c += dc
        return False, []

    @staticmethod
    def _check_draw(grid: list[list[int]]) -> bool:
        for row in grid:
            if 0 in row:
                return False
        return True

    @staticmethod
    def _get_column_height(grid: list[list[int]], column: int) -> int:
        for row in range(ROWS - 1, -1, -1):
            if grid[row][column] == 0:
                return ROWS - 1 - row
        return ROWS

    async def _handle_player_action(self, event: BaseEvent) -> None:
        if self._global_state.state != ConnectFourState.ongoing:
            raise GameException(
                exception_type=GameExceptionType.state_incompatibility,
                message=f"Game is not ongoing, cannot perform actions."
            )
        action_data = PlayerActionData(**event.data)
        if action_data.player != self._global_state.current_player:
            raise GameException(
                exception_type=GameExceptionType.wrong_player,
                message=f"Please wait for your turn."
            )

        column = action_data.column
        column_height = self._get_column_height(self._global_state.grid, column)
        if column_height >= ROWS:
            raise GameException(
                exception_type=GameExceptionType.forbidden_action,
                message=f"Column {column} is full, cannot drop disc there."
            )
        self._global_state.grid[ROWS - 1 - column_height][column] = action_data.player

        has_winner, winning_positions = self._check_winner(self._global_state.grid, action_data.player)
        if has_winner:
            self._global_state.state = ConnectFourState.win
            self._global_state.winning_positions = winning_positions
        elif self._check_draw(self._global_state.grid):
            self._global_state.state = ConnectFourState.draw
        else:
            self._global_state.current_player = self._global_state.current_player % 2 + 1

        event = await self.event_store.append(
            room_id=self.game_room.id,
            event_type=GameEvent.GAME_STATE_UPDATE,
            actor_id=event.actor_id,
            data=self._global_state.model_dump(mode="json"),
        )
        await self.event_bus.publish(event=event)

    async def handle_event(
            self,
            event: BaseEvent,
    ) -> None:
        # TODO: if an event fails it should send an event to the actor informing them of the error: we could use a targetted event, or a "responds_to" field in the event
        if event.type == GameEvent.GAME_START:
            await self._handle_game_start(event)
            return
        if event.type == GameEvent.PLAYER_ACTION:
            await self._handle_player_action(event)
            return
