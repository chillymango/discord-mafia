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


class ForwardChatMessages:
    """
    Forward all Discord chat messages to outbound queues.

    These should dump immediately.
    """

    def __init__(
        self,
        driver: "BotMessageDriver",
        game: "Game",
        channel: "disnake.TextChannel",
    ):
        self._driver = driver
        self._game = game
        self._channel = channel

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
        """
        if message.author.bot:
            await self._driver.public_publish(Message.announce(self._game, message.content), game_message=False)
        elif not message.author.bot:
            # TODO: makes more sense probably to remove this labeling loci
            await self._driver.public_publish(Message.announce(self._game, f"{message.author.nick}: {message}"))
