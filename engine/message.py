import asyncio
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
        game: "Game" = actor.game
        return Message(time.time(), (game.turn_number, game.turn_phase), message)

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
    Some way of getting strings from in here to some text box or channel where they need to be

    Basically just a duck type
    """

    async def public_publish(self, message: "Message") -> None:
        """
        Publish a message to the bulletin that everybody can see
        """

    async def private_publish(self, player: "Player", message: "Message") -> None:
        """
        Publish a message to a player that only they can see
        """


class Messenger:

    def __init__(self, game: "Game", message_driver: MessageDriver = None) -> None:
        """
        Maintains a public message queue as well as a private message queue

        TODO: message driver goes here (i.e bot API)
        """
        self._game = game
        self._message_driver: MessageDriver = message_driver

        self._public_queue: T.List[Message] = []

    def announce(self, message: str, flush: bool = False) -> None:
        """
        If flush=True, it will flush the message immediately
        """
        msg = Message.announce(self._game, message)
        if flush:
            asyncio.ensure_future(self._message_driver.public_publish(msg))
        else:
            self._public_queue.append(msg)

    def private_actor(self, actor: "Actor", message: str) -> None:
        if actor not in self._game.get_actors():
            print("WARNING: that actor is not associated with this game")
            return
        actor._message_queue.append(Message.address_to(actor, message))

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
        if flush:
            asyncio.ensure_future(
                self._message_driver.private_publish(actor.player, Message.address_to(actor, message))
            )
        else:
            actor._message_queue.append(Message.address_to(actor, message))

    async def drive_public_queue(self, count: int = None, delay: float = 0.0) -> None:
        """
        Drive the public queue of messages with some delay between messages.

        By default will drive all messages instantly.
        Another component could be layered on top of this one to give a more interesting
        release of public messages.
        """
        print('Driving public queue')
        delay = delay or 0.0  # do not allow a None value
        # TODO: implement driving by counts
        idx = 0
        while self._public_queue:
            if idx == count:
                break
            message = self._public_queue.pop(0)
            if self._message_driver is None:
                print(f"DEBUG::drive_public_queue {message}")
            else:
                print(message.message)
                await self._message_driver.public_publish(message)

            await asyncio.sleep(delay)

    async def drive_all_private_queues(self, count: int = None, delay: float = 0.0) -> None:
        await asyncio.gather(*[
            self.drive_private_queue(actor, count=count, delay=delay) for actor in self._game.get_actors()
        ])

    async def drive_private_queue(self, actor: "Actor", count: int = None, delay: float = 0.0) -> None:
        """
        Drive a private queue of messages with some delay between messages.

        By default will drive all messages instantly.
        """
        idx = 0
        while actor._message_queue:
            if idx == count:
                break
            idx += 1
            message = actor._message_queue.pop(0)
            if self._message_driver is None:
                print(f"DEBUG::drive_private_queue::[TO {actor.name}] {message}")
            else:
                print(message.message)
                await self._message_driver.private_publish(actor.player, message)

            await asyncio.sleep(delay)
