"""
Message forwarding to bot queues
"""
from cachetools import TTLCache
import typing as T

from chatapi.discord.router import router
from engine.message import Message

if T.TYPE_CHECKING:
    import disnake
    from chatapi.discord.driver import BotMessageDriver
    from chatapi.discord.router import Router
    from engine.game import Game
    from engine.message import Messenger


class ForwardChatMessages:
    """
    Forward all Discord chat messages to outbound queues.

    These should dump immediately.
    """

    def __init__(
        self,
        game: "Game",
        channel: "disnake.TextChannel",
    ):
        # TODO: should we forward directly to BotMessageDriver or go through Messenger?
        self._game = game
        self._channel = channel
        # need to keep track of what messages we have seen
        # TODO: i'm sure this is fine lol but maybe we need it bigger eventually
        self._seen_messages: TTLCache = TTLCache(maxsize=10000, ttl=300)

    @property
    def messenger(self) -> "Messenger":
        return self._game.messenger

    @property
    def channel(self) -> "disnake.TextChannel":
        return self._channel

    @channel.setter
    def channel(self, new_channel: "disnake.TextChannel") -> None:
        self._channel = new_channel

    def enable_forwarding(self) -> None:
        """
        Add a callback to the router to start forwarding all public chat messages from
        the Discord into the bot message queues.

        These should all be listed as public queue messages.
        """
        router.register_message_callback(self.channel.name, self.do_forward)

    def disable_forwarding(self) -> None:
        router.unregister_message_callback(self.channel.name, self.do_forward)

    async def do_forward(self, message: "disnake.Message") -> None:
        """
        Forward only chat messages to bots. They should be labeled as public messages.

        Bots are responsible for filtering messages they sent.

        TODO: i don't think we need this anymore
        """
        if not message.content:
            # this shouldn't be going out anyways
            return

        if message.id in self._seen_messages:
            print(f"We've already seen message with id {message.id}")
            return

        self._seen_messages[message.id] = message

        # THIS SHOULD ONLY FORWARD NON-BOT TRAFFIC
        if not message.author.bot:
            actor = self._game.get_actor_by_name(message.author.name)
            if actor is None:
                print(f"Dropping forwarded message to {message.author.name}")
                return
            self.messenger.queue_message(Message.player_public_message(actor, message.content))
