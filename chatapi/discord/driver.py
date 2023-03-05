import asyncio
import time
import typing as T
from collections import defaultdict
from collections import deque
import disnake

from chatapi.discord.icache import icache
from engine.message import InboundMessageDriver
from engine.message import MessageDriver
from engine.message import OutboundMessageDriver

from proto import message_pb2

if T.TYPE_CHECKING:
    from chatapi.app.bot import BotUser
    from chatapi.discord.input_panel import InputController
    from engine.message import Message
    from engine.player import Player


class BotMessageDriver(OutboundMessageDriver):
    """
    Drives messages to bots.

    The gRPC API should poll once a second or so for new messages.
    This driver just makes a queue available for the API to pull and clear.
    The engine-facing side puts elements in the queue.
    """

    def __init__(self) -> None:
        self._grpc_queue: asyncio.Queue[message_pb2.Message] = asyncio.Queue()
        self._public_engine_queue: asyncio.Queue[message_pb2.Message] = asyncio.Queue()

        self._private_message_queues: T.Dict["BotUser", asyncio.Queue[message_pb2.Message]] = \
            defaultdict(asyncio.Queue)
        self._private_grpc_queues: T.Dict["BotUser", asyncio.Queue[message_pb2.Message]] = \
            defaultdict(asyncio.Queue)

    async def flush_public(self) -> None:
        """
        Flush the public queue for the message driver.
        """
        while not self._public_engine_queue.empty():
            item = self._public_engine_queue.get_nowait()
            for q in self._private_grpc_queues.values():
                q.put_nowait(item)

    async def flush_private(self, player: "Player" = None) -> None:
        """
        Flush the private queue for the message driver for a player.

        If player is not provided, flush all private queues.
        """
        if player is None:
            asyncio.gather(*[self.flush_private(p) for p in self._private_message_queues])
            return

        while not self._private_message_queues[player].empty():
            self._private_grpc_queues[player].put_nowait(
                self._private_message_queues[player].get_nowait()
            )

    async def public_publish(
        self,
        message: "Message",
        flush: bool = True,
        game_message: bool = False
    ) -> None:
        """
        NOTE: flush doesn't do anything because timings probably don't matter to bots
        """
        # give everybody this message
        if game_message:
            message_type = message_pb2.Message.GAME
        else:
            message_type = message_pb2.Message.PUBLIC
        msg = message_pb2.Message(timestamp=time.time(), source=message_type, message=message.message)
        if flush:
            # NOTE: this has to initialize with private messages... lol should probably fix that
            for bot in self._private_grpc_queues:
                self._private_grpc_queues[bot].put_nowait(msg)
        else:
            self._public_engine_queue.put_nowait(msg)
        self._public_engine_queue.put_nowait(msg)

    async def private_publish(
        self,
        player: "Player",
        message: "Message",
        flush: bool = True
    ) -> None:
        """
        NOTE: flush doesn't do anything because timings probably don't matter to bots
        """
        if player.bot is None:
            # this is invalid
            print(f"{player.name} is not a bot")
            return

        message_type = message_pb2.Message.PRIVATE
        msg = message_pb2.Message(timestamp=time.time(), source=message_type, message=message.message)
        if flush:
            self._private_grpc_queues[player.bot].put_nowait(msg)
        else:
            self._private_message_queues[player.bot].put_nowait(msg)


class WebhookDriver(InboundMessageDriver):
    """
    Drives messages to Discord from bots using Webhooks

    TODO: move this to other module, it's not a MessageDriver
    """

    def __init__(self, pub_channel: "disnake.TextChannel") -> None:
        self._pub_channel = pub_channel
        self._webhook: "disnake.Webhook" = None
        self._message_queue: asyncio.Queue[T.Tuple[str, str]] = asyncio.Queue()

    async def setup_webhook(self):
        self._webhook = await self._pub_channel.create_webhook(name="Botspeak")

    async def run(self) -> None:
        """
        This should just run in the background as a task.
        """
        while True:
            try:
                user, message = await self._message_queue.get()
                await self.publish_webhook(user, message)
            except asyncio.CancelledError:
                break

    async def publish_webhook(self, user: str, message: str) -> None:
        if self._webhook is None:
            print("Warning: no WebHook to publish to")
            return
        await self._webhook.send(
            content=message,
            username=user,
            allowed_mentions=disnake.AllowedMentions.all()
        )

    def queue_publish_webhook(self, user: str, message: str) -> None:
        """
        Synchronous method that queues up a message to publish over Webhook.
        """
        self._message_queue.put_nowait((user, message))


class DiscordDriver(OutboundMessageDriver):
    """
    Drives Discord messages
    """

    def __init__(
        self,
        pub_channel: "disnake.TextChannel",
    ) -> None:
        self._pub_channel = pub_channel

        self._public_queue: T.Deque["Message"] = deque()
        self._private_queues: T.Dict["Player", T.Deque["Message"]] = defaultdict(deque)

        self._webhook: "disnake.Webhook" = None

    async def flush_public(self) -> None:
        while self._public_queue:
            message = self._public_queue.popleft()
            await self.public_publish(message, flush=True)

    async def flush_private(self, player: "Player" = None) -> None:
        if player is None:
            await asyncio.gather(*[self.flush_private(player=p) for p in self._private_queues])
            return
        queue = self._private_queues.get(player)
        if queue is None:
            return
        while queue:
            message = queue.popleft()
            await self.private_publish(player, message, flush=True)

    async def public_publish(self, message: "Message", flush: bool = True) -> None:
        if flush:
            await self._pub_channel.send(message)
        else:
            self._public_queue.append(message)

    async def private_publish(self, player: "Player", message: "Message", flush: bool = True) -> None:
        # TODO: is there a better way to do it than manually checking?
        # we can't cache it locally since the original dictionary is prone to changing
        # we could maybe store it differently in both cases
        # ... or actually Player should just contain a reference to User
        if message is None or not message.message:
            print(f"Empty message?")
            return

        for user, interaction in icache.items():
            if user.name == player.name:
                break
        else:
            print(f"No interaction found for {player.name}. Dropping message: {message.message}")
            return None

        if not flush:
            self._private_queues[player].append(message)
            return

        # TODO: i think this is a bug with disnake but I might just be sleepy
        try:
            print(f'Sending message to {player.name}')
            await interaction.send(content=message.message, ephemeral=True)
        except:
            await interaction.followup.send(content=message.message, ephemeral=True)

    async def edit_last_private(self, player: "Player", **kwargs: T.Any) -> None:
        """
        Edit the previously issued private message sent to a player
        """
        for user, interaction in icache.items():
            if user.name == player.name:
                break
        else:
            return None
        try:
            await interaction.edit_original_response(**kwargs)
        except:
            print('Followup update')
            await interaction.followup.edit(**kwargs)
