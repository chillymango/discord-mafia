"""
This should describe how bots interact with the game.

Information bots
"""
import asyncio
import typing as T

from chatapi.discord.driver import BotMessageDriver
from engine.message import Message

if T.TYPE_CHECKING:
    from chatapi.app.bot import BotUser
    from engine.actor import Actor
    from engine.game import Game
    from engine.message import Messenger


class BotApi:
    """
    Supports interacting with a game object.

    TODO: calling the bot API from gRPC runs into some event loop bullshit, where
    gRPC seems to think that the primary loop isn't running. My guess is that it's
    due to the fact that the gRPC implementation probably uses a different underlying
    event loop, but I'm not totally sure. In any case, after putting both servers on
    the same loop, we're still unable to call the right methods.

    Unfortunately I think what we'll have to do is have the API synchronously queue
    messages / state changes up from here and then get dumped out.
    """

    def __init__(self, game: "Game") -> None:
        self._game = game
        self._get_bots_from_game()
        self._setup_heartbeat_timers()

        self._reservations: T.Set["BotUser"] = set()

        self._bot_drivers: T.Dict[BotUser, BotMessageDriver] = dict()

    @property
    def game(self) -> "Game":
        return self._game

    @property
    def messenger(self) -> "Messenger":
        return self._game.messenger

    @property
    def free_bots(self) -> T.Set["BotUser"]:
        return {b for b in self._bots if b not in self._reservations}

    @property
    def reserved_bots(self) -> T.Set["BotUser"]:
        # return a shallow copy
        return set(self._reservations)

    def get_bot_driver_by_id(self, bot_id: str) -> BotMessageDriver:
        """
        Cache this internally so we don't have to keep looking it up lol
        """
        bot = self.get_bot_by_id(bot_id)
        if bot not in self._bot_drivers:
            for driver in self._game.messenger._drivers:
                if isinstance(driver, BotMessageDriver) and driver._actor.name == bot.name:
                    break
            else:
                raise ValueError(f"No bot driver for bot id {bot_id}")
            self._bot_drivers[bot] = driver
        return self._bot_drivers[bot]

    def get_bot_by_id(self, bot_id: str) -> T.Optional["BotUser"]:
        for bot in self._bots:
            if bot.id == bot_id:
                return bot
        return None

    def prune(self) -> None:
        to_remove = list()
        for bot, actor in self._bots.items():
            if not actor.is_alive:
                to_remove.append(bot)
        for _bot in to_remove:
            self._bots.pop(_bot)

    def check_out_bot(self, bot_name: str = None) -> T.Optional["BotUser"]:
        """
        Reserve a bot. Request one with given name if available.

        If `bot_name` is specified and it's not available, return None.
        If `bot_name` is not specified and there are no bots available, return None.
        Otherwise, return a matching bot.
        """
        if bot_name:
            print(f'looking for a bot with name {bot_name}')
            for bot in self.free_bots:
                if bot.name == bot_name:
                    break
            else:
                return None
        elif self.free_bots:            
            bot = self.free_bots.pop()
            if bot is None:
                return None

        if bot is not None:
            self._reservations.add(bot)
            return bot

        return None

    def check_in_bot(self, bot_name: str) -> bool:
        """
        Free the bot with that given name.
        """
        for bot in self._reservations:
            if bot.name == bot_name:
                break
        else:
            print(f"No bot in-use found with name {bot_name}")
            return False
        self._reservations.discard(bot)
        return True

    def _get_bots_from_game(self) -> None:
        self._bots: T.Dict["BotUser", "Actor"] = dict()
        for actor in self._game.get_actors():
            if actor.player.is_bot:
                self._bots[actor.player.bot] = actor

    def _setup_heartbeat_timers(self) -> None:
        # TODO: this might eventually be useful to drop bots
        pass

    def public_message(self, bot_id: str, msg: str) -> None:
        """
        Issue a public message to the chat.

        If the chat is closed at the moment, this will be dropped.
        """
        bot = self.get_bot_by_id(bot_id)
        actor = self._game.get_actor_by_name(bot.name, raise_if_missing=True)
        self.messenger.queue_message(Message.bot_public_message(actor, msg))

    def private_message(self, bot_id: str, target_name: str, msg: str) -> None:
        """
        Issue a private message to the person with specified name.
        """

    def submit_last_will(self, bot_id: str, last_will: str) -> None:
        bot = self.get_bot_by_id(bot_id)
        actor = self._game.get_actor_by_name(bot.name, raise_if_missing=True)
        actor._last_will = last_will
