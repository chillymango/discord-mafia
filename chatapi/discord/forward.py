"""
Message forwarding to bot queues
"""
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

    @property
    def messenger(self) -> "Messenger":
        return self._game.messenger

    @property
    def channel(self) -> "disnake.TextChannel":
        return self._channel

    @channel.setter
    def channel(self, new_channel: str) -> None:
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

        if message.author.bot and "Mafia" not in message.author.name:
            actor = self._game.get_actor_by_name(message.author)
            if actor is None:
                print(f"Dropping forwarded message to {message.author.name}")
            self.messenger.queue_message(Message.bot_public_message(actor, message.content))
        elif not message.author.bot:
            actor = self._game.get_actor_by_name(message.author)
            if actor is None:
                print(f"Dropping forwarded message to {message.author.name}")
            self.messenger.queue_message(Message.player_public_message(actor, message.content))
