"""
Interface to game player (from actor).

This should be 1:1 player:actor but we will keep them separate for now.
"""
import typing as T

from proto import state_pb2

if T.TYPE_CHECKING:
    from disnake import User
    from chatapi.app.bot import BotUser


class Player:
    """
    Hello there!
    """

    def __init__(self, name: str):
        self._name = name
        self._user = None
        self._bot = None

    def to_proto(self) -> state_pb2.Player:
        player = state_pb2.Player()
        player.is_bot = self.is_bot
        player.is_human = self.is_human
        player.name = self.name
        return player

    @classmethod
    def create_from_user(self, user: "User") -> "Player":
        p = Player(user.name)
        p._user = user
        return p

    @classmethod
    def create_from_bot(self, bot: "BotUser") -> "Player":
        p = Player(bot.name)
        p._bot = bot
        return p

    @property
    def user(self) -> "User":
        if not self.is_human:
            raise ValueError(f"{self.name} is not a Human")
        return self._user

    @property
    def bot(self) -> "BotUser":
        return self._bot

    @property
    def is_bot(self) -> bool:
        return self._bot is not None

    @property
    def is_human(self) -> bool:
        return self._user is not None

    @property
    def name(self) -> str:
        return self._name
