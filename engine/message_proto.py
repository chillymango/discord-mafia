from enum import Enum
import asyncio
import cachetools
import time
import typing as T

from engine.phase import TurnPhase

from proto import message_pb2

if T.TYPE_CHECKING:
    from engine.actor import Actor
    from engine.game import Game
    from engine.player import Player
    from chatapi.discord.driver import DiscordPrivateDriver
    from chatapi.discord.driver import DiscordPublicDriver
    from chatapi.discord.driver import WebhookDriver


class MessageType(Enum):
    """
    Instead of using routing rules (TODO: maybe do that instead) we just
    use the message type to determine how to handle inbound messages.

    The logic is hardcoded in the Messenger class.

    We'll probably need lots of different options here since this will also
    be what determines how to render the outbound message.
    """
    # if we don't specify a message type it'll just print as debug
    DEBUG = 0

    # public-facing announcements
    # examples include government reveals, lynch votes
    # these aren't the same as Panels - a Panel has the ability to render itself
    ANNOUNCEMENT = 1

    # a message sent from a bot.
    # this should basically always be issued to the Webhook driver
    BOT_PUBLIC_MESSAGE = 2

    # a message sent from player
    # we will never issue this message out, this should only ever come from players
    PLAYER_PUBLIC_MESSAGE = 3

    # message sent from a player (or bot) to another player
    PRIVATE_MESSAGE = 4

    # message sent to a player privately indicating the result of some action
    PRIVATE_FEEDBACK = 5

    # post in day-thread for situational awareness, should be public
    INDICATOR = 6

    # public announcement in game channel
    NIGHT_SEQUENCE = 7


class Message(message_pb2.Message):
    """
    Messages consist of a real timestamp, a game timestamp, and a message string.
    """

    def __init__(
        self,
        real_time: float,
        game_time: T.Tuple[int, "TurnPhase"],
        message: str = "",
        *,
        title: str = "",
        message_type: MessageType = message_pb2.Message.UNKNOWN,
        addressed_to: "Actor" = None,
        addressed_from: "Actor" = None
    ) -> None:
        """
        If `addressed_to` is specified, this is a private message to that person.
        If not specified, this is a public message. This is primarily used for
        filtering 
        """
        self.title = title
        self.message_type = message_type
        self.real_time = real_time
        self.game_time = game_time
        self.message = message
        self.addressed_to = addressed_to
        self.addressed_from = addressed_from

    def __repr__(self) -> str:
        return f"[Message] **{self.title}** : {self.message}"
    
    def debug_repr(self) -> str:
        return (f"[{self.real_timestamp}] ({self.turn_phase.name.capitalize()} "
                f"{self.turn_number}): {self.message}")

    def ai_repr(self) -> str:
        """
        Representation for bots?
        """
        return f"{self.title} - {self.message}".replace('*', '')

    @classmethod
    def announce(cls, game: "Game", title: str, message: str = "") -> "Message":
        return Message(
            time.time(),
            (game.turn_number, game.turn_phase),
            message=message,
            title=title,
            message_type=MessageType.ANNOUNCEMENT,
        )

    @classmethod
    def indicate(cls, game: "Game", title: str, message: str = "") -> "Message":
        return Message(
            time.time(),
            (game.turn_number, game.turn_phase),
            message=message,
            title=title,
            message_type=MessageType.INDICATOR,
        )

    @classmethod
    def night_sequence(cls, game: "Game", message: str) -> "Message":
        return Message(
            time.time(),
            (game.turn_number, game.turn_phase),
            title=message,
            message_type=MessageType.NIGHT_SEQUENCE,
        )

    @classmethod
    def bot_public_message(cls, actor: "Actor", message: str) -> "Message":
        return Message(
            time.time(),
            (actor.game.turn_number, actor.game.turn_phase),
            message=message,
            addressed_from=actor,
            message_type=MessageType.BOT_PUBLIC_MESSAGE,
        )

    @classmethod
    def player_public_message(cls, actor: "Actor", message: str) -> "Message":
        return Message(
            time.time(),
            (actor.game.turn_number, actor.game.turn_phase),
            message=message,
            addressed_from=actor,
            message_type=MessageType.PLAYER_PUBLIC_MESSAGE,
        )

    @classmethod
    def private_message(cls, from_actor: "Actor", to_actor: "Actor", message: str) -> "Message":
        return Message(
            time.time(),
            (from_actor.game.turn_number, from_actor.game.turn_phase),
            message=message,
            addressed_from=from_actor,
            addressed_to=to_actor,
            message_type=MessageType.PRIVATE_MESSAGE,
        )

    @classmethod
    def private_feedback(cls, to_actor: "Actor", title: str, message: str) -> "Message":
        return Message(
            time.time(),
            (to_actor.game.turn_number, to_actor.game.turn_phase),
            message=message,
            # address_from is the game, so...
            addressed_to=to_actor,
            message_type=MessageType.PRIVATE_FEEDBACK,
            title=title,
        )

    @property
    def real_timestamp(self) -> str:
        return time.strftime("%H:%M:%S", time.gmtime(self.real_time))

    @property
    def turn_number(self) -> int:
        return self.game_time[0]

    @property
    def turn_phase(self) -> "TurnPhase":
        return self.game_time[1]


class MessageDriver:
    """
    Some sort of message boundary controller

    TODO: evaluate if this is sufficient or if we need to publish outbound
    messages in a thread or something like that
    """

    def __init__(self) -> None:
        self._task: asyncio.Task = None
        self._queue: asyncio.Queue["Message"] = asyncio.Queue()

    def wants(self, message: "Message") -> bool:
        """
        Specifies whether the driver wants this Message object.

        TODO: this is setup as an overridden method instead of just an allowlist of
        message types since I anticipate at some point we'll want some more fine-grained
        control over forwarding rules. It's much less efficient to do it this way and will
        get worse if we add more Drivers, so revisit this at some point in the future to
        see if your guess was correct.
        """
        raise NotImplementedError(
            "Each MessageDriver implementation must specify desired Messages"
        )

    def format_message(self, message: "Message") -> T.Dict[str, T.Any]:
        """
        Default formatting of message is to just strip the message contents and print
        that out directly as message content.
        """
        return dict(content=str(message.message))

    def add_to_queue(self, message: "Message") -> None:
        """
        Add a message to the queue to be processed whenever the event loop context
        switches to the driver task.
        """
        self._queue.put_nowait(message)

    async def publish(self, message: "Message") -> None:
        """
        Publish sequentially from single queue
        """
        raise NotImplementedError("Message drivers must specify implementation for publish")

    async def run(self) -> None:
        """
        Generally these should process asynchonrously whenever we get a message
        """
        while True:
            try:
                msg = await self._queue.get()
                await self.publish(msg)
            except asyncio.CancelledError:
                break

    def start(self) -> None:
        self._task = asyncio.create_task(self.run())


class InboundMessageDriver(MessageDriver):
    """
    Handles getting messages into the game from external sources.

    Really this is just intended to allow bots to message the game chat.
    """


class OutboundMessageDriver(MessageDriver):
    """
    Some way of getting strings from in here to some text box or channel where they need to be

    Basically just a duck type
    """

    async def flush_public(self) -> None:
        """
        Flush the public queue for the message driver.
        """

    async def flush_private(self, player: "Player" = None) -> None:
        """
        Flush the private queue for the message driver for a player.

        If player is not provided, flush all private queues.
        """

    async def public_publish(self, message: "Message", flush: bool = True) -> None:
        """
        Publish a message to the bulletin that everybody can see.

        If flush is set, the message will be issued immediately.
        """

    async def private_publish(self, player: "Player", message: "Message", flush: bool = True) -> None:
        """
        Publish a message to a player that only they can see.

        If flush is set, the message will be issued immediately.
        """


class Messenger:

    def __init__(self, game: "Game", *drivers: MessageDriver) -> None:
        """
        This class should be a central hub that the service can put messages into.
        This class will look at each message and route the message into the appropriate queue / driver.

        This should largely be done based on message type.

        For example, all messages issued as "MessageType.ANNOUNCE" should:
            * be sent in Discord public
            * be forwarded to bots
        All messages issued as "MessageType.BOTSPEAK" should:
            * be sent in Discord public as a Botspeak Webhook

        The Messenger just accepts messages from any number of inputs, and then
        forwards them out to the appropriate sources.

        This object just exposes a bunch of methods that describe some high-level
        message types and then they get routed through the messenger according to
        some basic rules.
        """
        self._game = game

        # primary queue we pull from
        self._message_queue: asyncio.Queue[Message] = asyncio.Queue()

        #self._outbound_driver = outbound_driver
        self._drivers = drivers
        self._inbound_tasks: T.Set[asyncio.Task] = set()

    async def run(self) -> None:
        print("Starting the message loop")
        while True:
            msg = await self._message_queue.get()
            self.route_message(msg)

    def route_message(self, message: "Message") -> None:
        """
        Dump the message into the appropriate queues

        Each driver defines a filter. If the message passes the filter, it
        gets issued to that driver.
        """
        for driver in self._drivers:
            if driver.wants(message):
                driver.add_to_queue(message)

    def start(self) -> None:
        # start all message drivers
        self.start_drivers()
        # start our internal task
        self._task = asyncio.create_task(self.run())

    def start_drivers(self) -> None:
        for driver in self._drivers:
            driver.start()

    def queue_message(self, message: "Message") -> None:
        """
        Input a message into the queue.
        """
        self._message_queue.put_nowait(message)

    def get_driver_by_class(self, klass: T.Type[MessageDriver]) -> T.Optional[MessageDriver]:
        for driver in self._drivers:
            if isinstance(driver, klass):
                return driver
        return None
