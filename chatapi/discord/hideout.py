"""
Hideout is a private chat.

Examples:
    * Mafia have a hideout private chat during the night
    * Jailor has a hideout private chat during the night
    * Cultists will have a hideout private chat during the night
    * private day chat could be cool too for some faction
    * maybe the ILLUMINATI?!
"""
from collections import defaultdict
import asyncio
import time
import typing as T
import disnake

from chatapi.discord.router import router
from engine.action.jail import Jail as JailAction
from engine.phase import TurnPhase
from engine.role.town.jailor import Jailor
# TODO: kidnapper, interrogator
#from engine.role.mafia.ki

if T.TYPE_CHECKING:
    from engine.actor import Actor
    from engine.game import Game


class Hideout:
    """
    Hideouts get set up by Town Hall.

    Town Hall will check to see which alignments exist and create these hideouts at
    the beginning of the game.

    Hideouts in Discord are implemented by private threads.

    Hideouts should define a set of criteria by which to add players to the hideout.
    """

    NAME = "Hideout"

    def is_open(self) -> bool:
        """
        Specifies when the Hideout is accessible.

        Defaults to False. Child classes should define this.
        """
        return False

    async def initialize(self) -> None:
        # create the hideout private thread
        self._thread = await self._channel.create_thread(
            name=self.NAME,
            type=disnake.ChannelType.private_thread,
            invitable=False,
        )

    @classmethod
    async def create_and_init(cls, game: "Game", channel: "disnake.TextChannel") -> "Hideout":
        hideout = cls(game, channel)
        await hideout.initialize()
        return hideout

    def __init__(self, game: "Game", channel: "disnake.TextChannel") -> None:
        self._game = game
        self._channel = channel
        self._stop = asyncio.Event()
        self._task: asyncio.Task = None
        self._thread: disnake.Thread = None
        self._active: bool = False
        self.extra_init()

    def extra_init(self) -> None:
        pass

    async def open(self) -> None:
        """
        Inheriting classes should define this method but by default it's a no-op
        """

    async def close(self) -> None:
        """
        Inheriting classes should define this method but by default it's a no-op
        """

    def start(self) -> None:
        self._task = asyncio.create_task(self.run())

    def stop(self) -> None:
        self._stop.set()

    def signal_message(self, message: str) -> None:
        """
        TODO: there should be a default implementation for this
        """
        return

    async def run(self) -> None:
        try:
            while not self._stop.is_set():
                if self.is_open() and not self._active:
                    print(f"Opening {self.__class__.__name__}")
                    self._active = True
                    await self.open()
                elif not self.is_open() and self._active:
                    print(f"Closing {self.__class__.__name__}")
                    self._active = False
                    await self.close()
                await asyncio.sleep(1.0)
        except Exception as exc:
            print(repr(exc))


# lets just make one concrete version first
class MafiaHideout(Hideout):
    """
    Mafia Hideout is a nighttime private thread that they can use to communicate with each other
    """

    NAME = "Mafia Hideout"

    def is_open(self) -> bool:
        """
        Specifies when the Hideout is accessible.

        Defaults to False. Child classes should define this.
        """
        return self._game.turn_phase == TurnPhase.NIGHT and not self._game.party_ongoing

    async def open(self) -> None:
        """
        As part of initialization, the thread should be created already.

        Add the appropriate players to this thread.
        Players should be added to the Mafia thread if
            1. there is no party going on
            2. they are a member of the Mafia
            3. they are alive
            4. they are not in jail
        """
        to_add: T.List["Actor"] = []
        for actor in self._game.get_live_mafia_actors():
            if actor in self._game._jail_map.values():
                continue
            if actor.player.is_bot:
                continue
            to_add.append(actor)
        await asyncio.gather(*[self._thread.add_user(actor.player.user) for actor in to_add])

    async def close(self) -> None:
        """
        As part of teardown, remove all members of the thread
        """
        members = await self._thread.fetch_members()
        await asyncio.gather(*[self._thread.remove_user(mem) for mem in members])

# some method that generates an output username for the forwarding
RouteAlias = T.Callable[[disnake.Message], str]

# some specification for an outbound rule
RouteEgress = T.Tuple[T.Union[disnake.Thread, disnake.TextChannel], RouteAlias]


class MessageTunnel:
    """
    Message Tunnel specification

    Each entry specifies that for an inbound message match, there's a list of
    outbound message rules. The rules will specify where to send the message, as
    well as the alias to use.

    A Webhook is used for this...
    TODO: does it make sense to use the game messenger?
    the routing rules seem like they'd get kinda wacked
    """

    def __init__(self) -> None:
        """
        Forward from one thread to other threads
        """
        self._routing_rules: T.Dict[disnake.TextChannel, T.List[RouteEgress]] = defaultdict(list)
        self._stop = asyncio.Event()
        self._queue = asyncio.Queue()
        self._webhooks: T.Dict[disnake.TextChannel, disnake.Webhook] = dict()

    def clear(self) -> None:
        self._routing_rules = defaultdict(list)
        # do we also clear webhooks...? nah lol

    @staticmethod
    def _webhook_key(channel: T.Union[disnake.Thread, disnake.TextChannel]):
        if isinstance(channel, disnake.Thread):
            return channel.parent
        return channel

    async def add_route(
        self,
        source: disnake.TextChannel,
        sink: T.Union[disnake.TextChannel, disnake.Thread],
        alias: RouteAlias,
    ) -> None:
        """
        Add a routing rule
        """
        for egress in self._routing_rules[source]:
            if egress[0] == sink:
                # maybe there's a case where we want this but for now I can't come up with one
                raise ValueError("Route already exists with a different function")
        self._routing_rules[source].append((sink, alias))

        key = self._webhook_key(sink)
        if key not in self._webhooks:
            # TODO: does key need to be unique?
            self._webhooks[key] = await sink.parent.create_webhook(name=f"MessageTunnel-{key.name}")

        router.register_message_callback(source.name, self.filter_message)

    async def remove_route(
        self,
        source: disnake.TextChannel,
        sink: disnake.TextChannel,
    ):
        """
        Remove a routing rule
        """
        for egress in self._routing_rules[source]:
            if egress[0] == sink:
                self._routing_rules[source].remove(egress)
                router.unregister_message_callback(source.name, self.filter_message)

        print("WARNING: remove_route tried to remove a route that did not exist")

    async def filter_message(self, message: "disnake.Message") -> None:
        """
        If the message matches, forward this onto the next thread.

        This should be passed into the router as an instance method.
        The instance should be used to evaluate the message.
        """
        if message.channel not in self._routing_rules:
            return

        for sink, alias in self._routing_rules[message.channel]:
            # fire and forget on best effort
            # i think this *does* mean that messages could be delivered out of order, which
            # we might not want...? let's see how likely it is
            webhook = self._webhooks[self._webhook_key(sink)]
            if message.webhook_id == webhook.id:
                print("Skipping a double broadcast")
                continue

            #asyncio.create_task(webhook.send(content=message.content, username=alias(message)))
            kwargs = dict(content=message.content, username=alias(message))
            if isinstance(sink, disnake.Thread):
                kwargs["thread"] = sink
            # run it synchronously i guess?
            await webhook.send(**kwargs)


class Jail(Hideout):
    """
    Jail is where Jailors and their targets will end up.

    There is a single Jail instance for the game. When Jailors make Jail requests, whether
    the Jailing is successful will be evaluated during the Dusk phase. If it is, the Jailor(s)
    and their target(s) will be moved to Jail Houses and Jail Cells respectively.

    Afterwards, a message connector proxy is set up between the appropriate threads.
    Each Jailor should only ever see one person in their thread. They will be proxied messages
    from their target, and potentially other Jailors (under the name Jailor) if they share
    a target.
    """

    NAME = "Jail"  # it's *all* called Jail bro

    async def create_thread(self) -> None:
        # thread names must be unique - come up with a random number
        self._threads.append(await self._channel.create_thread(
            name=f"{self.NAME}",
            type=disnake.ChannelType.private_thread,
            invitable=False,
        ))

    async def initialize(self) -> None:
        """
        Create a thread pool for Jail usage.

        The number of threads will not need to exceed 2 * Jailor count.
        `Jailor count` should include Kidnapper and Interro.
        Threads should be sanitized after usage.
        """
        self._threads: T.List[disnake.Thread] = list()
        jailor_count = len(self._game.get_live_actors_by_role(Jailor))
        futures = [asyncio.ensure_future(self.create_thread()) for _ in range(2 * jailor_count)]
        await asyncio.gather(*futures)

        self._message_tunnel = MessageTunnel()

    def is_open(self) -> bool:
        """
        Specifies when the Hideout is accessible.

        Defaults to False. Child classes should define this.
        """
        return self._game.turn_phase == TurnPhase.NIGHT and self._game.can_jail

    async def open(self) -> None:
        # each unique prisoner gets a jail cell thread
        # each jailor gets a jail house thread
        self._jailhouses: T.Dict["Actor", disnake.Thread] = dict()
        self._jailcells: T.Dict["Actor", disnake.Thread] = dict()

        futures: T.List[asyncio.Future] = list()
        for jailor, prisoner in self._game._jail_map.items():
            if jailor.player.is_bot:
                # TODO: plumb this for bots eventually
                pass
            else:
                self._jailhouses[jailor] = self._threads.pop()
                futures.append(
                    asyncio.ensure_future(self._jailhouses[jailor].add_user(jailor.player.user))
                )

            if prisoner not in self._jailcells:
                if prisoner.player.is_bot:
                    # TODO: plumb this for bots eventually
                    pass
                else:
                    self._jailcells[prisoner] = self._threads.pop()
                    futures.append(
                        asyncio.ensure_future(self._jailcells[prisoner].add_user(prisoner.player.user))
                    )
        print("Setting up jail threads")
        # wait for all operations first
        await asyncio.gather(*futures)

        print("setting up tunnel")
        await self.setup_tunnel()

    async def close(self) -> None:
        await self.empty_cells()

    async def setup_tunnel(self) -> None:
        futures = []
        # setup proxies with the original mappings
        for jailor, prisoner in self._game._jail_map.items():
            if jailor.player.is_bot or prisoner.player.is_bot:
                # no point in connecting this
                continue

            # jailor to prisoner, obscure name as "Jailor"
            futures.append(asyncio.ensure_future(
                self._message_tunnel.add_route(
                    self._jailhouses[jailor],
                    self._jailcells[prisoner],
                    lambda msg: "Jailor"
                )
            ))

            # prisoner to jailor, give real name
            futures.append(asyncio.ensure_future(
                self._message_tunnel.add_route(
                    self._jailcells[prisoner],
                    self._jailhouses[jailor],
                    lambda msg: msg.author.name,
                )
            ))

        await asyncio.gather(*futures)

    async def populate_cells(self) -> None:
        """
        Move the prisoners into jail cells and the jailors into jail houses

        This step is skipped if either the jailor or the prisoner is not human.
        They should still get the targeting view though.

        ...

        Also bots should be banned from being Jailor.
        """
        futures = []
        for jailor in set(self._game._jail_map.keys()):
            if jailor.player.is_bot:
                continue
            futures.append(asyncio.ensure_future(
                self._jailhouses[jailor].add_user(jailor.player.user))
            )

        for prisoner in set(self._game._jail_map.values()):
            if prisoner.player.is_bot:
                continue
            futures.append(asyncio.ensure_future(
                self._jailcells[prisoner].add_user(prisoner.player.user))
            )

        await asyncio.gather(*futures)

    async def clean_thread_history(self, thread: disnake.Thread) -> None:
        t_init = time.time()
        to_delete: T.List[disnake.Message] = []
        async for message in thread.history(limit=200):
            to_delete.append(message)

        try:
            await asyncio.gather(*[msg.delete() for msg in to_delete])
        except:
            pass

        t_final = time.time()
        print(f"Took {t_final - t_init}s to clean thread {thread.name}")

    async def cleanup_tunnel(self) -> None:
        futures = []
        # setup proxies with the original mappings
        for jailor, prisoner in self._game._jail_map.items():
            if jailor.player.is_bot or prisoner.player.is_bot:
                # no point in connecting this
                continue

            # jailor to prisoner, obscure name as "Jailor"
            futures.append(asyncio.ensure_future(
                self._message_tunnel.remove_route(
                    self._jailhouses[jailor],
                    self._jailcells[prisoner],
                )
            ))

            # prisoner to jailor, give real name
            futures.append(asyncio.ensure_future(
                self._message_tunnel.remove_route(
                    self._jailcells[prisoner],
                    self._jailhouses[jailor],
                )
            ))

        await asyncio.gather(*futures)

    async def empty_cells(self) -> None:
        """
        Go to all threads. Empty them and delete all messages.
        """
        # unregister all routes
        await self.cleanup_tunnel()

        # give all threads back
        futures = []
        for jailor, jh_thread in self._jailhouses.items():
            futures.append(asyncio.ensure_future(jh_thread.remove_user(jailor.player.user)))
            self._threads.append(jh_thread)
        for prisoner, jc_thread in self._jailcells.items():
            futures.append(asyncio.ensure_future(jc_thread.remove_user(prisoner.player.user)))
            self._threads.append(jc_thread)

        # wait for removal, start a f+f task to clean in the background
        await asyncio.gather(*futures)

        for thread in self._threads:
            asyncio.create_task(self.clean_thread_history(thread))

    async def signal_message(self, jailor: "Actor", message: str) -> None:
        # ok so we need to find everything that's connected
        # find the jail house for our jailor, find the jail cell he's attached to
        # and then find any jail houses attached to the jail cell
        # OH WAIT lets see if this works i think we just have to send it to jailor...
        jailhouse = self._jailhouses.get(jailor)
        if not jailhouse:
            return
        await jailhouse.send(message)


class DeathChat(Hideout):
    """
    Don't close until end of game

    Add dead players
    """

    NAME = "godfathers-inferno"

    @property
    def is_open(self) -> bool:
        return True

    async def open(self) -> None:
        """
        Check for any dead players that are not in the chatroom
        """
        for actor in self._game.actors:
            if actor.player.is_human and not actor.is_alive and actor not in self._in_chatroom:
                await self._thread.add_user(actor.player.user)
                self._in_chatroom.add(actor)

    async def close(self) -> None:
        await asyncio.gather(*[self._thread.remove_user(actor.player.user) for actor in self._in_chatroom])
        self._in_chatroom = set()

    async def run(self) -> None:
        self._in_chatroom: T.Set["Actor"] = set()
        try:
            while not self._stop.is_set():
                # check if we need to add anyone
                if self.is_open:
                    await self.open()
                else:
                    await self.close()
                await asyncio.sleep(1.0)
        except Exception as exc:
            print(repr(exc))
