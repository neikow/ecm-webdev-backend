from backend.games.abstract import Game


class MemoryGameStore:
    _games: dict[int, Game] = {}

    def __init__(self) -> None:
        self._games = {}

    def add_game(self, key: int, game: Game) -> None:
        self._games[key] = game

    def get_game(self, key: int) -> Game | None:
        return self._games.get(key)

    def delete_game(self, key: int) -> None:
        if key in self._games:
            del self._games[key]
