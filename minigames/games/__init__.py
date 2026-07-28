from django.conf import settings
from django.utils.module_loading import import_string

from minigames.games.base import BaseGame, GameScore, Player, Team
from minigames.games.first_to_n import FirstToN
from minigames.games.lockout_bingo import LockoutBingo

game_registry: dict[str, BaseGame] = {
    name: import_string(path)() for name, path in settings.MINIGAMES.items()
}

__all__ = ["BaseGame", "GameScore", "Player", "Team", "FirstToN", "LockoutBingo", "game_registry"]
