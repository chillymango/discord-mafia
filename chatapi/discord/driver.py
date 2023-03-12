import asyncio
import time
import typing as T
from collections import defaultdict
from collections import deque
import disnake

from chatapi.discord.icache import icache
from chatapi.discord.town_hall import TownHall
from engine.game import Game
from engine.message import Message
from engine.message import InboundMessageDriver
from engine.message import MessageDriver
from engine.message import MessageType
from engine.message import OutboundMessageDriver

from proto import message_pb2

if T.TYPE_CHECKING:
    from chatapi.app.bot import BotUser
    from chatapi.discord.input_panel import InputController
    from engine.actor import Actor
    from engine.message import Message
    from engine.player import Player


class BotMessageDriver(OutboundMessageDriver):
    """
    Drives messages to bots.
    """

    def __init__(self, actor: "Actor") -> None:
        self._actor = actor
        self._grpc_queue: asyncio.Queue[Message] = asyncio.Queue()
        super().__init__()

    def wants(self, message: "Message") -> bool:
        """
        We want this message if it's intended for our bot.
        """
        return message.addressed_to == self._actor or message.message_type in (
            MessageType.ANNOUNCEMENT,
            MessageType.NIGHT_SEQUENCE,
            MessageType.INDICATOR,
            MessageType.PLAYER_PUBLIC_MESSAGE,
            MessageType.BOT_PUBLIC_MESSAGE,  # LMAOOO
        )

    @property
    def grpc_queue(self) -> asyncio.Queue[Message]:
        return self._grpc_queue

    async def publish(self, message: "Message") -> None:
        """
        All this does is make the message *availble* for gRPC to pick up.
        """
        self._grpc_queue.put_nowait(message)


class ChatDriver(OutboundMessageDriver):
    """
    Drives messages to Chat

    In this case, `Chat` will almost certainly just mean Court chat, unless
    we come up with some other dumb Chat ideas
    """

    def __init__(self, game: "Game", channel: "disnake.TextChannel") -> None:
        super().__init__()
        self._game = game
        self._channel = channel
        self._webhook: "disnake.Webhook" = None
        self._terminated = False
        self._discussion_thread: "disnake.Thread" = None

    def wants(self, message: "Message") -> bool:
        """
        We want all Botspeak messages and that's it
        """
        return message.message_type in (
            MessageType.BOT_PUBLIC_MESSAGE,
            MessageType.INDICATOR,
        )

    @classmethod
    async def create_with_name(cls, game: "Game", channel: "disnake.TextChannel", name: str) -> "WebhookDriver":
        driver = cls(game, channel)
        await driver.setup_webhook(name)
        return driver

    async def setup_webhook(self, name: str):
        self._webhook = await self._channel.create_webhook(name=name)

    def set_discussion_thread(self, thread: "disnake.Thread") -> None:
        self._discussion_thread = thread

    def format_message(self, message: "Message") -> T.Dict[str, str]:
        """
        For now this should just implement Court chat?

        Obscure the player name

        TODO: the below logic feels like it might belong somewhere else
        """
        if message.addressed_from.role.name in ("Judge", "Crier"):
            username = "Court"
        else:
            username = "Jury"

        return dict(username=username, content=message.message)

    def publish_from_external(self, sender_name: str, message: str) -> None:
        """
        Queue a message from the external API (slash command)
        """
        actor = self._game.get_actor_by_name(sender_name)
        if actor is None:
            print(f"No actor by name {sender_name}")
            return
        self.add_to_queue(Message.player_public_message(actor, message))

    async def publish(self, message: "Message") -> None:
        """
        Aggressively drop messages if we are unable to publish.

        This should be routed from internal messenger.
        """
        if self._webhook is None:
            return
        if self._discussion_thread is None:
            return

        try:
            await self._webhook.send(thread=self._discussion_thread, **self.format_message(message))
        except Exception as exc:
            print(f"Failed in ChatDriver: {repr(exc)}")


class OldBotMessageDriver(OutboundMessageDriver):
    """
    Drives messages to bots.

    This driver just makes a queue available for the API to pull and clear.
    The engine-facing side puts elements in the queue.
    The gRPC side waits for items to be made available.
    """

    def __init__(self) -> None:
        self._grpc_queue: asyncio.Queue[message_pb2.Message] = asyncio.Queue()
        self._public_engine_queue: asyncio.Queue[message_pb2.Message] = asyncio.Queue()

        self._private_message_queues: T.Dict["BotUser", asyncio.Queue[message_pb2.Message]] = \
            defaultdict(asyncio.Queue)
        self._private_grpc_queues: T.Dict["BotUser", asyncio.Queue[message_pb2.Message]] = \
            defaultdict(asyncio.Queue)

    def wants(self, message: "Message") -> bool:
        """
        We want the following:
            * public messages from players
            * game announcements
            * 
        """

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
    """

    def __init__(self, game: "Game", channel: "disnake.TextChannel") -> None:
        super().__init__()
        self._game = game
        self._channel = channel
        self._webhook: "disnake.Webhook" = None
        self._terminated = False
        self._discussion_thread: "disnake.Thread" = None

    def wants(self, message: "Message") -> bool:
        """
        We want all Botspeak messages and that's it
        """
        return message.message_type in (
            MessageType.BOT_PUBLIC_MESSAGE,
            MessageType.INDICATOR,
        )

    @classmethod
    async def create_with_name(cls, game: "Game", channel: "disnake.TextChannel", name: str) -> "WebhookDriver":
        driver = cls(game, channel)
        await driver.setup_webhook(name)
        return driver

    async def setup_webhook(self, name: str):
        self._webhook = await self._channel.create_webhook(name=name)

    def set_discussion_thread(self, thread: "disnake.Thread") -> None:
        self._discussion_thread = thread

    def format_message(self, message: "Message") -> T.Dict[str, T.Any]:
        if message.message_type == MessageType.BOT_PUBLIC_MESSAGE:
            return dict(content=message.message, username=message.addressed_from.name)
        else:
            embed = disnake.Embed(title=message.title, description=message.message)
            if message.addressed_from:
                username = message.addressed_from.name
            else:
                username = "Mafia Bot"
            return dict(embed=embed, username=username)

    async def publish(self, message: "Message") -> None:
        try:
            if self._webhook is None:
                return
            fmt = self.format_message(message)
            t_init = time.time()
            while time.time() - t_init < 60.0:  # this would be a real problem
                if self._game.town_hall.discussion_thread is not None:
                    thread = self._game.town_hall.discussion_thread
                    break
                # try again in a bit
                await asyncio.sleep(1.0)

            if thread is not None:
                fmt["thread"] = thread
                await self._webhook.send(**fmt)
            # otherwise drop the message if we don't have a thread
        except Exception as exc:
            print(f"Failed to publish Webhook: {repr(exc)}")


class DiscordPublicDriver(OutboundMessageDriver):
    """
    Drives Discord messages to public chat as Mafia Bot.

    For Webhook publishes, use the WebhookDriver.
    For private publishes, use the DiscordPrivateDriver.
    """

    def __init__(self, channel: "disnake.TextChannel") -> None:
        super().__init__()
        self._channel = channel

    def wants(self, message: "Message") -> bool:
        return message.message_type in (
            MessageType.ANNOUNCEMENT,
            MessageType.DEBUG,  # eek
            MessageType.NIGHT_SEQUENCE,
        )

    async def run(self) -> None:
        """
        Public-facing driver probably needs a rate limit
        Not more than one message every 5 seconds?
        """
        while True:
            try:
                msg = await self._queue.get()
                t_init = time.time()
                await self.publish(msg)
                delta = time.time() - t_init
                if delta > 5.0:
                    print("WARNING: publish took longer than 5s")
                else:
                    await asyncio.sleep(5.0 - delta)
            except asyncio.CancelledError:
                break

    def format_message(self, message: "Message") -> T.Dict[str, T.Any]:
        embed = disnake.Embed(title=message.title, description=message.message)
        return dict(embed=embed)

    async def publish(self, message: "Message") -> None:
        await self._channel.send(**self.format_message(message))


class DiscordPrivateDriver(OutboundMessageDriver):
    """
    Drives Discord messages to a private interaction chat as Mafia Bot.

    Each human player should have one of these.
    """

    def __init__(self, channel: "disnake.TextChannel", actor: "Actor") -> None:
        super().__init__()
        self._channel = channel
        self._actor = actor

    def wants(self, message: "Message") -> bool:
        return message.addressed_to == self._actor

    def format_message(self, message: "Message") -> T.Dict[str, T.Any]:
        if message.message_type == MessageType.PRIVATE_FEEDBACK:
            embed = disnake.Embed()
            embed.title = message.title
            embed.description = message.message
            return dict(embed=embed)
        return dict(content=f"(From **{message.addressed_from.name}**): {message.message}")

    async def publish(self, message: "Message") -> None:
        ia = icache.get(self._actor.player.user)
        if ia is None:
            print(f"WARNING: no interaction for {self._actor.name}. Dropping private message")

        try:
            print(f"Sending private message to {self._actor.name}")
            await ia.send(**self.format_message(message), ephemeral=True)
        except Exception as exc:
            print(f"Throwing exception?: {repr(exc)}")
            await ia.followup.send(**self.format_message(message), ephemeral=True)


class DiscordDriver(OutboundMessageDriver):
    """
    Drives Discord messages
    """

    def __init__(
        self,
        town_hall: "TownHall",
    ) -> None:
        self._town_hall = town_hall

        self._public_queue: T.Deque["Message"] = deque()
        self._private_queues: T.Dict["Player", T.Deque["Message"]] = defaultdict(deque)

    @property
    def publisher(self) -> T.Union[None, "disnake.Thread", "disnake.TextChannel"]:
        """
        If we have a thread, use that.

        If we have a channel, use that.

        If we have neither, freak out.
        """
        if self._town_hall.discussion_thread:
            return self._town_hall.discussion_thread
        if self._town_hall:
            return self._town_hall.ch_bulletin
        raise ValueError("Discord driver has no possible outputs")

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
            await self.publisher.send(message)
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
