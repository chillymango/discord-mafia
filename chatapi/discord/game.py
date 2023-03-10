# global game registry
import typing as T

if T.TYPE_CHECKING:
    import disnake
    from engine.game import Game


GAMES: T.Dict["disnake.TextChannel", "Game"] = {}
