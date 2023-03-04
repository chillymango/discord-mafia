import asyncio
import cachetools
import time
import typing as T

from engine.phase import TurnPhase

if T.TYPE_CHECKING:
    from engine.actor import Actor
    from engine.game import Game
    from engine.player import Player


class Message:
    """
    Messages consist of a real timestamp, a game timestamp, and a message string.
    """

    def __init__(self, real_time: float, game_time: T.Tuple[int, "TurnPhase"], message: str) -> None:
        self._real_time = real_time
        self._game_time = game_time
        self._message = message

    def __repr__(self) -> str:
        return f"**{self.message}**"
    
    def debug_repr(self) -> str:
        return (f"[{self.real_timestamp}] ({self.turn_phase.name.capitalize()} "
                f"{self.turn_number}): {self.message}")

    @classmethod
    def announce(cls, game: "Game", message: str) -> "Message":
        return Message(time.time(), (game.turn_number, game.turn_phase), message)

    @classmethod
    def address_to(cls, actor: "Actor", message: str) -> "Message":
        """
        TODO: rename, this name is incorrect
        """
        game: "Game" = actor.game
        return Message(time.time(), (game.turn_number, game.turn_phase), message)

    @classmethod
    def label_from(cls, actor: "Actor", message: str) -> "Message":
        return cls.address_to(actor, f"{actor.name}: {message}")

    @property
    def real_timestamp(self) -> str:
        return time.strftime("%H:%M:%S", time.gmtime(self._real_time))

    @property
    def turn_number(self) -> int:
        return self._game_time[0]

    @property
    def turn_phase(self) -> "TurnPhase":
        return self._game_time[1]

    @property
    def message(self) -> str:
        return self._message


class MessageDriver:
    """
    Some sort of message boundary controller
    """


class InboundMessageDriver(MessageDriver):
    """
    Handles getting messages into the game from external sources.

    Really this is just intended to allow bots to message the game chat.
    """

    async def run(self) -> None:
        """
        Generally these should process asynchonrously whenever we get a message
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

    def __init__(self, game: "Game", *message_drivers: T.List[MessageDriver]) -> None:
        """
        Maintains a public message queue as well as a private message queue

        TODO: message driver goes here (i.e bot API)
        """
        self._game = game
        self._message_drivers: T.List[MessageDriver] = message_drivers or []

        self._inbound_tasks: T.Set[asyncio.Task] = set()

    def start_inbound(self) -> None:
        for driver in self.inbound_drivers:
            self._inbound_tasks.add(asyncio.ensure_future(driver.run()))

    @property
    def inbound_drivers(self) -> T.Iterable[InboundMessageDriver]:
        return [d for d in self._message_drivers if isinstance(d, InboundMessageDriver)]

    @property
    def outbound_drivers(self) -> T.Iterable[OutboundMessageDriver]:
        return [d for d in self._message_drivers if isinstance(d, OutboundMessageDriver)]

    def get_driver_by_class(self, klass: T.Type[MessageDriver]) -> T.Optional[MessageDriver]:
        for driver in self._message_drivers:
            if isinstance(driver, klass):
                return driver
        return None

    def drive_messengers_public(self, message: "Message", flush: bool = True) -> None:
        """
        Drive all outbound public queue
        """
        for driver in self.outbound_drivers:
            asyncio.create_task(driver.public_publish(message, flush=flush))

    def drive_messengers_private(self, actor: "Actor", message: "Message", flush: bool = True) -> None:
        """
        Drive outbound private queues
        """
        for driver in self.outbound_drivers:
            asyncio.create_task(driver.private_publish(actor.player, message, flush=flush))

    def announce(self, message: str, flush: bool = False) -> None:
        """
        If flush=True, it will flush the message immediately
        """
        msg = Message.announce(self._game, message)
        self.drive_messengers_public(msg, flush=flush)

    def private_actor(self, actor: "Actor", message: str, flush: bool = True) -> None:
        if actor not in self._game.get_actors():
            print("WARNING: that actor is not associated with this game")
            return
        self.drive_messengers_private(actor, Message.address_to(actor, message), flush=flush)

    def private_number(self, number: int, message: str) -> None:
        if number > len(self._game.get_actors()):
            print(f"WARNING: invalid actor index {number}")
            return
        actor = self._game.get_actors()[number]
        self.private_actor(actor, message)

    def private_message(self, name: str, message: str, flush: bool = True) -> None:
        actor = self._game.get_actor_by_name(name)
        if actor is None:
            print(f"WARNING: no actor by name {name}")
            return
        self.private_actor(actor, message, flush=flush)

    async def drive_public_queue(self) -> None:
        """
        Drive the public queue of messages with some delay between messages.

        By default will drive all messages instantly.
        Another component could be layered on top of this one to give a more interesting
        release of public messages.
        """
        print('Driving public queue')
        await asyncio.gather(*[driver.flush_public() for driver in self.outbound_drivers])

    async def drive_all_private_queues(self) -> None:
        print('Driving all private queues')
        await asyncio.gather(*[driver.flush_private() for driver in self.outbound_drivers])

    async def drive_private_queue(self, actor: "Actor") -> None:
        """
        Drive a private queue of messages with some delay between messages.

        By default will drive all messages instantly.
        """
        print(f'Driving private queue for {actor.name}')
        await asyncio.gather(*[driver.flush_private(actor.player) for driver in self.outbound_drivers])
