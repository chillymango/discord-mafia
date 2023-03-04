"""
This should describe how bots interact with the game.

Information bots
"""
import asyncio
import typing as T

from chatapi.discord.driver import DiscordDriver
from chatapi.discord.driver import WebhookDriver

if T.TYPE_CHECKING:
    from chatapi.app.bot import BotUser
    from engine.actor import Actor
    from engine.game import Game


class BotApi:
    """
    Supports interacting with a game object.

    Wait why don't we just make a game API object in general...

    Bot programs should follow this procedure:
    1. Request a bot ID. If there's no bot ID it should just stop.
        This request should come with a server bind for our API to plug
        back into in order to send traffic the other way.
    2. Bot API should assign this ID. Respond to the request with information
        like bot name, bot role, etc.
        Fuck it I should really learn gRPC.
    3. 
    """

    def __init__(self, game: "Game") -> None:
        self._game = game
        self._get_bots_from_game()
        self._setup_heartbeat_timers()

        self._reservations: T.Set["BotUser"] = set()

    @property
    def game(self) -> "Game":
        return self._game

    @property
    def discord_driver(self) -> "DiscordDriver":
        return self._game.messenger.get_driver_by_class(DiscordDriver)

    @property
    def webhook_driver(self) -> "WebhookDriver":
        return self._game.messenger.get_driver_by_class(WebhookDriver)

    @property
    def free_bots(self) -> T.Set["BotUser"]:
        return {b for b in self._bots if b not in self._reservations}

    @property
    def reserved_bots(self) -> T.Set["BotUser"]:
        # return a shallow copy
        return set(self._reservations)

    def get_bot_by_id(self, bot_id: str) -> T.Optional["BotUser"]:
        for bot in self._bots:
            if bot.id == bot_id:
                return bot
        return None

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
        self._reservations.add(bot)
        return bot

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
        # use synchronous method to queue up our message
        self.webhook_driver.queue_publish_webhook(bot.name, msg)

    def private_message(self, bot_id: str, target_name: str, msg: str) -> None:
        """
        Issue a private message to the person with specified name.
        """
