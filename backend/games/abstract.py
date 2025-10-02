import abc


class Game(abc.ABC):
    """The maximum number of players allowed in the game and the associated lobby."""
    max_players: int
