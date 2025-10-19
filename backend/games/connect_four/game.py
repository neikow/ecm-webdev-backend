import asyncio
from random import randint

from backend.domain.events import BaseEvent, GameEvent
from backend.events.bus import EventBus
from backend.games.abstract import Game, Metadata, PlayerSpec, GameException, GameExceptionType, GameStatus
from backend.games.connect_four.consts import ROWS, COLUMNS, EMPTY, P_2, P_1
from backend.games.connect_four.schemas import ConnectFourState, ConnectFourActionData, ConnectFourInitData
from backend.infra.memory_event_store import MemoryEventStore
from backend.models.game_room_model import GameRoomModel


class ConnectFour(Game[ConnectFourState]):
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

    def __init__(
            self,
            game_room: GameRoomModel,
            event_store: MemoryEventStore,
            event_bus: EventBus,
    ) -> None:
        super().__init__(game_room, event_store, event_bus)
        self.state = ConnectFourState()

    @classmethod
    def get_players_spec(cls) -> PlayerSpec:
        return PlayerSpec(
            min=2,
            max=2,
        )

    async def _handle_game_start(self, event: BaseEvent) -> None:
        if not self.state.status.can_be_started:
            raise GameException(
                exception_type=GameExceptionType.state_incompatibility,
                message=f"Game has already started."
            )
        player_spec = self.get_players_spec()
        if len(self.current_players) < player_spec.min:
            raise GameException(
                exception_type=GameExceptionType.wrong_players_number,
                message=f"Not enough players to start the game."
            )
        elif len(self.current_players) > player_spec.max:
            raise GameException(
                exception_type=GameExceptionType.wrong_players_number,
                message=f"Too many players to start the game."
            )
        self.state.status = GameStatus.ongoing
        self.state.current_player = randint(P_1, P_2)
        await self.broadcast_game_state_update(actor_id=event.actor_id)
        await self.send_game_started_events(actor_id=event.actor_id)

    async def send_game_started_events(self, actor_id: str) -> None:
        await asyncio.gather(*[
            self._send_game_started_event(
                actor_id=actor_id,
                target_id=player.user_id,
            ) for player in self.current_players
        ])

    async def _send_game_started_event(
            self,
            actor_id: str,
            target_id: str
    ) -> None:
        event = await self.event_store.append(
            room_id=self.game_room.id,
            event_type=GameEvent.GAME_INIT,
            actor_id=actor_id,
            target_id=target_id,
            data=ConnectFourInitData(
                player=next(
                    (index + 1) for index, player in enumerate(self.current_players) if player.user_id == target_id
                ),
            ).model_dump()
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
            if EMPTY in row:
                return False
        return True

    @staticmethod
    def _get_column_height(grid: list[list[int]], column: int) -> int:
        for row in range(ROWS - 1, -1, -1):
            if grid[row][column] == EMPTY:
                return ROWS - 1 - row
        return ROWS

    async def _handle_player_action(self, event: BaseEvent) -> None:
        if not self.state.status.accepts_player_actions:
            raise GameException(
                exception_type=GameExceptionType.state_incompatibility,
                message="Game is not ongoing, cannot perform actions."
            )
        action_data = ConnectFourActionData.model_validate(event.data)
        if action_data.player != self.state.current_player:
            raise GameException(
                exception_type=GameExceptionType.wrong_player,
                message=f"Please wait for your turn."
            )

        column = action_data.column
        column_height = self._get_column_height(self.state.grid, column)
        if column_height >= ROWS:
            raise GameException(
                exception_type=GameExceptionType.forbidden_action,
                message=f"Column {column} is full, cannot drop disc there."
            )
        self.state.grid[ROWS - 1 - column_height][column] = action_data.player

        has_winner, winning_positions = self._check_winner(self.state.grid, action_data.player)
        if has_winner:
            self.state.status = GameStatus.win
            self.state.winning_positions = winning_positions
        elif self._check_draw(self.state.grid):
            self.state.status = GameStatus.draw
        else:
            self.state.current_player = self.state.current_player % 2 + 1

        await self.broadcast_game_state_update(actor_id=event.actor_id)

    async def handle_event(
            self,
            event: BaseEvent,
    ) -> None:
        # TODO: if an event fails it should send an event to the actor informing them of the error: we could use a targetted event, or a "responds_to" field in the event
        if event.type == GameEvent.GAME_START:
            await self._handle_game_start(event)
            return
        elif event.type == GameEvent.PLAYER_ACTION:
            await self._handle_player_action(event)
            return
        else:
            raise GameException(
                exception_type=GameExceptionType.unknown_action,
                message=f"Event type {event.type} is not handled by the game."
            )
