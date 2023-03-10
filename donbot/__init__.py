"""
It's the Robot Mafia
"""
import asyncio
import logging
import random
import time
import typing as T

from grpc import aio
from grpc import RpcError

import log
from donbot.action import BotAction
from donbot.auto_ctx import AutomationContext
from donbot.resolver import RandomResolver
from engine.affiliation import MAFIA
from engine.affiliation import NEUTRAL
from engine.affiliation import TRIAD
from engine.phase import TurnPhase
from proto import command_pb2
from proto import connect_pb2
from proto import message_pb2
from proto import state_pb2

from proto import service_pb2_grpc

if T.TYPE_CHECKING:
    from grpc.aio import UnaryStreamCall

BIND = "localhost:50051"


class DecisionState:
    """
    The bot should update this periodically as it goes through states.

    A 1hz timer should be sufficient.

    Hopefully this helps with latching for specific decisions that bots must make during
    the decision making process.

    TODO: with the below setup, bots won't ever perform day actions.

    DAYLIGHT:
        * are we suspicious of anybody?
            * if yes, go to TRIBUNAL_SUSPECT
        * if not, stay in this state
    TRIBUNAL_SUSPECT:
        * we should put up a trial vote for somebody
    """


class LogEvent:
    """
    Generic data object
    """

    def __init__(self, turn_number: int, turn_phase: TurnPhase, message: str) -> None:
        self.turn_number = turn_number
        self.turn_phase = turn_phase
        self.message = message


class DonBot:
    """
    Base class

    You come to me on the day of my robot daughter's wedding
    """

    def __init__(self, bot_name: str = None) -> None:
        self._connected = False
        self._bot_name: str = bot_name
        self._bot_id: str = None
        self.log = logging.Logger(name=f"Bot {self._bot_name}")
        self.log.addHandler(log.ch)

        # current state
        self._actor: state_pb2.Actor = None  # this is us
        self._game: state_pb2.Game = None  # this updates

        self._subscribe_task: asyncio.Task = None
        self._print_task: asyncio.Task = None
        self._message_queue: asyncio.Queue[message_pb2.Message] = asyncio.Queue()
        self.setup_resolvers()

        # these keep track of whether we've made decisions at each phase / turn num
        self._action_decisions: T.Dict[T.Tuple[TurnPhase, int], T.List[str]] = dict()
        self._trial_decisions: T.Dict[T.Tuple[TurnPhase, int], T.Optional[str]] = dict()
        self._lynch_decisions: T.Dict[T.Tuple[TurnPhase, int], T.Optional[bool]] = dict()

        self._action_results: T.Dict[T.Tuple[TurnPhase, int], str] = dict()

        self._game_log: T.List[LogEvent] = list()
        self._prev_last_will: str = ""

        self._should_exit = False

    @property
    def last_will(self) -> str:
        """
        Construct this from our game log
        """
        lw = ""
        for log_event in self._game_log:
            if log_event.turn_phase in (TurnPhase.DAYBREAK, TurnPhase.DAYLIGHT, TurnPhase.DUSK):
                prefix = "D"
            elif log_event.turn_phase in (TurnPhase.NIGHT, TurnPhase.NIGHT_SEQUENCE):
                prefix = "N"
            else:
                prefix = "U"
            lw += f"{prefix}{log_event.turn_number}: {log_event.message}\n"
        return lw

    def setup_resolvers(self) -> None:
        self._random_resolver = RandomResolver()
        self._action_resolver = self._random_resolver
        self._resolvers = {ba: self._random_resolver for ba in BotAction}

    @property
    def last_action_target(self) -> T.Optional[T.List[str]]:
        """
        Sorts action_decisions by turn number (and turn phase) and determines
        the name of the last target selected.

        Returns None if there have been no targets so far.
        """
        if not self._action_decisions:
            return None

        turns = list(self._action_decisions.keys())
        turns.sort(reverse=True)
        turn_key = turns[0]
        return self._action_decisions.get(turn_key)

    @property
    def name(self) -> str:
        if self._actor is None:
            return None
        return self._actor.player.name

    def record_event(self, event: str) -> None:
        self._game_log.append(LogEvent(self._game.turn_number, TurnPhase[self._game.turn_phase], event))

    @property 
    def role(self) -> state_pb2.Role:
        if self._actor is None:
            return None
        return self._actor.role

    async def connect(self) -> None:
        async with aio.insecure_channel(BIND) as channel:
            stub = service_pb2_grpc.GrpcBotApiStub(channel)
            try:
                response: connect_pb2.ConnectResponse = await \
                    stub.Connect(connect_pb2.ConnectRequest(timestamp=time.time(), request_name=self._bot_name))
                self._bot_name = response.bot_name
                self._bot_id = response.bot_id
                self._connected = True
                self.log.name = self._bot_name

                self.log.info("Successfully connected!")
            except RpcError as error:
                self.log.exception(error)
                self._should_exit = True
                raise

    async def disconnect(self) -> None:
        if not self._connected or self._bot_id is None:
            return

        if self._subscribe_task is not None:
            self._subscribe_task.cancel()

        async with aio.insecure_channel(BIND) as channel:
            stub = service_pb2_grpc.GrpcBotApiStub(channel)
            try:
                response: connect_pb2.DisconnectResponse = await \
                    stub.Disconnect(connect_pb2.DisconnectRequest(timestamp=time.time(), bot_id=self._bot_id))
                if response.success:
                    self._bot_id = None
                    self._bot_name = None
                    self._connected = False
            except RpcError as error:
                self.log.exception(error)

    async def get_game_state(self) -> state_pb2.Game:
        if not self._connected:
            raise ValueError("Cannot get game state if we're not connected")

        async with aio.insecure_channel(BIND) as channel:
            stub = service_pb2_grpc.GrpcBotApiStub(channel)
            try:
                response: state_pb2.GetGameResponse = await \
                    stub.GetGame(state_pb2.GetGameRequest(timestamp=time.time(), bot_id=self._bot_id))
                self._game = response.game

                for actor in self._game.actors:
                    if actor.player.name == self.name:
                        break
                else:
                    return False

                self._actor = actor
                if not actor.is_alive:
                    self.log.info("Uh oh! We're dead!")
                    self._should_exit = True
                    return False

                return True
            except RpcError as error:
                self.log.exception(error)

    def contextualize(self) -> T.Dict[BotAction, T.List[T.Any]]:
        # this gives us a list of possible bot actions
        autoctx = AutomationContext.create_from_game_proto(self._bot_name, self._game)
        # we want to minimize the number of things we ask ChatGPT
        # the random bot should just fill out a random instruction whenever it hits a junction
        bot_actions = autoctx.infer_actions()
        targets = autoctx.infer_targets(bot_actions)
        return targets

    def plan_action(self, action_target: T.Dict[BotAction, T.List[T.Any]]) -> T.Tuple[BotAction, T.Any]:
        # then we need to do something to figure out what the best one to take at any given point is
        # if we're randomly picking we don't need a lot of info, all we really need is
        # the set of choices
        # first we need to pick the action to take
        action = self._action_resolver.resolve(list(action_target.keys()))[0]
        if not action_target[action]:
            return (None, None)

        target = self._resolvers[action].resolve(action_target[action])[0]
        return (action, target)

    async def establish_identity(self) -> None:
        async with aio.insecure_channel(BIND) as channel:
            stub = service_pb2_grpc.GrpcBotApiStub(channel)
            try:
                response: state_pb2.GetActorResponse = await \
                    stub.GetActor(state_pb2.GetActorRequest(timestamp=time.time(), bot_id=self._bot_id))
                self._actor = response.actor
                self.log.info(f"I am a {self.role.name}")
            except RpcError as error:
                self.log.exception(error)

    async def subscribe_messages(self) -> None:
        self._subscribe_task = asyncio.create_task(self.subscribe_task())
        self._print_task = asyncio.create_task(self.print_message_task())

    async def subscribe_task(self) -> None:
        """
        Process messages as we get them. That just means putting them into our queue.

        Probably want to just run this in the background or something
        """
        self.log.info("Subscribing to messages")
        async with aio.insecure_channel(BIND) as channel:
            stub = service_pb2_grpc.GrpcBotApiStub(channel)
            call: UnaryStreamCall = stub.SubscribeMessages(
                message_pb2.SubscribeMessagesRequest(
                    timestamp=time.time(),
                    bot_id=self._bot_id
                )
            )

            # read until we need to exit...?
            while True:
                try:
                    response: message_pb2.SubscribeMessagesResponse = await call.read()
                    for msg in response.messages:
                        self._message_queue.put_nowait(msg)
                except RpcError as error:
                    self.log.exception(error)
                    asyncio.sleep(1.0)
                except asyncio.CancelledError:
                    self.log.info("Exiting subscribe messages")
                    break

    async def print_message_task(self) -> None:
        """
        Wraps the message printer as async and runs it in the background
        """
        while True:
            try:
                msg = await self._message_queue.get()
                # feed resolver with this information
                # if it's an action feedback, update last will
                await self._maybe_record_feedback(msg)
            except asyncio.CancelledError:
                break

    async def _maybe_record_feedback(self, msg: message_pb2.Message) -> None:
        """
        Inspect the received message and see if it has information
        that should be added to the game event log.
        """
        if msg.source == message_pb2.Message.FEEDBACK:
            # if the report is that we died, skip it
            if "killed" in msg.title.lower() or "neutralized" in msg.title.lower():
                return

            # associate this with last known action target
            self.log.info(f"Message feedback: {msg}")
            _, _, result = msg.message.rpartition(':')
            self.record_event(result)
            await self._maybe_update_last_will()

    async def _maybe_update_last_will(self) -> None:
        """
        If our last will has changed, update it on server as well
        """
        if self._actor.role.affiliation in (MAFIA, TRIAD, NEUTRAL):
            # neuts (even benigns) and evils never leave a LW
            return

        if self.last_will != self._prev_last_will:
            await self.update_last_will()
            self._prev_last_will = self.last_will

    async def send_public_message(self, message: str) -> None:
        """
        Issue a message to public chat
        """
        async with aio.insecure_channel(BIND) as channel:
            stub = service_pb2_grpc.GrpcBotApiStub(channel)
            try:
                to_send = message_pb2.Message(timestamp=time.time(), source=message_pb2.Message.PUBLIC, message=message)
                response: message_pb2.SendMessageResponse = await \
                    stub.SendMessage(message_pb2.SendMessageRequest(timestamp=time.time(), bot_id=self._bot_id, message=to_send))
            except RpcError as error:
                self.log.exception(error)

    async def trial_vote(self, target_name: str) -> None:
        """
        Issue a trial vote
        """
        async with aio.insecure_channel(BIND) as channel:
            stub = service_pb2_grpc.GrpcBotApiStub(channel)
            try:
                await stub.TrialVote(command_pb2.TargetRequest(
                    timestamp=time.time(),
                    bot_id=self._bot_id,
                    target_name=target_name
                ))
            except RpcError as error:
                self.log.exception(error)

    async def lynch_vote(self, vote: bool) -> None:
        """
        Issue a boolean lynch vote
        """
        async with aio.insecure_channel(BIND) as channel:
            stub = service_pb2_grpc.GrpcBotApiStub(channel)
            try:
                await stub.LynchVote(command_pb2.BoolVoteRequest(
                    timestamp=time.time(),
                    bot_id=self._bot_id,
                    vote=vote
                ))
            except RpcError as error:
                self.log.exception(error)

    async def skip_vote(self, vote: bool) -> None:
        """
        Issue a boolean skip vote
        """
        async with aio.insecure_channel(BIND) as channel:
            stub = service_pb2_grpc.GrpcBotApiStub(channel)
            try:
                await stub.SkipVote(command_pb2.BoolVoteRequest(
                    timestamp=time.time(),
                    bot_id=self._bot_id,
                    vote=vote
                ))
            except RpcError as error:
                self.log.exception(error)

    async def target(self, target_name: str) -> None:
        async with aio.insecure_channel(BIND) as channel:
            stub = service_pb2_grpc.GrpcBotApiStub(channel)
            try:
                response: command_pb2.TargetResponse = await stub.DayTarget(command_pb2.TargetRequest(
                    timestamp=time.time(),
                    bot_id=self._bot_id,
                    target_name=target_name
                ))
                self.log.info(f"I am targeting {target_name} with {self._actor.role.name} ability")
            except RpcError as error:
                self.log.exception(error)

    async def update_last_will(self) -> None:
        async with aio.insecure_channel(BIND) as channel:
            stub = service_pb2_grpc.GrpcBotApiStub(channel)
            try:
                await stub.LastWill(message_pb2.LastWillRequest(
                    timestamp=time.time(),
                    bot_id=self._bot_id,
                    last_will=self.last_will
                ))
            except RpcError as error:
                self.log.exception(error)

    async def inner(self) -> None:
        """
        This is probably too generic. We can ask for responses to generic actions.

        At least for now, the current inner loop looks like this:
        1. Get the current game state at 1Hz
        2. Update our intentions and etc

        TODO: does it make more sense to subscribe to changes instead?
        The game state shouldn't change in most 1s intervals and so the feedback
        received shouldn't execute anything...
        """
        while not self._should_exit:
            # sleep on entry
            await asyncio.sleep(3.0)

            # get the current game state
            if not await self.get_game_state():
                await asyncio.sleep(1.0)
                continue

            # how should trial voting be done?
            # options are:
            #   * lynch train
            #       * AI will just follow onto who others vote for
            #   * absolutely random
            #       * AI will randomly pick a decision whenever it is available
            #       * this decision should latch per turn
            #       * ChatGPT will directly replace the questions we ask at each
            #         stage, by asking for choices between trial votes, then lynch
            #         vote.
            #   * suspicion walk
            #       * we pick someone to be suspicious of and traverse
            #         a random walk that describes whether they are guilty.
            #         the higher up we walk on the tree, the more harshly
            #         we will vote for them
            #       * this is probably good for getting a random bot to
            #         behave in a consistent manner, but would probably be
            #         assisting ChatGPT a little too much to make it interesting

            # prioritize selecting actions if they are available
            actions = self.contextualize()
            if (self._game.turn_phase, self._game.turn_number) not in self._action_decisions:
                if BotAction.DAY_ACTION in actions:
                    # think about selecting a target
                    targets = actions[BotAction.DAY_ACTION]
                    if targets:
                        # when playing randomly, day targets will often trigger
                        # e.g MAYOR ON DAY 1 BABY
                        selected = self._action_resolver.resolve(targets)
                    else:
                        selected = None
                elif BotAction.NIGHT_ACTION in actions:
                    targets = actions[BotAction.NIGHT_ACTION]
                    if targets:
                        # when playing randomly, day targets will often trigger
                        # e.g MAYOR ON DAY 1 BABY
                        selected = self._action_resolver.resolve(targets)
                else:
                    selected = None

                if selected:
                    self._action_decisions[(self._game.turn_phase, self._game.turn_number)] = selected
                    await self.target(*selected)
                    self.record_event(f"Targeted {', '.join(selected)}")

            if (self._game.turn_phase, self._game.turn_number) not in self._trial_decisions:
                if BotAction.TRIAL_VOTE in actions:
                    # we will pick someone to become suspicious of and vote up
                    # but also make sure that "No Vote" is an option
                    targets = actions[BotAction.TRIAL_VOTE] + ['No Target']
                    selected = self._action_resolver.resolve(targets)[0]  # force one resolve
                    # this should always latch when we evaluate
                    self._trial_decisions[(self._game.turn_phase, self._game.turn_number)] = selected
                    if selected != 'No Target':
                        # issue a trial vote
                        await self.trial_vote(selected)
                    else:
                        self.log.info("Did not select a trial vote")

            if (self._game.turn_phase, self._game.turn_number) not in self._lynch_decisions:
                if BotAction.LYNCH_VOTE in actions:
                    targets = actions[BotAction.LYNCH_VOTE]
                    selected = self._action_resolver.resolve(targets)[0]  # force singular
                    await self.lynch_vote(selected)
                    self._lynch_decisions[(self._game.turn_phase, self._game.turn_number)] = selected

            # one of the above (in sequence if applicable) should run, but
            # then the loop should open to the other possible actions
            # mostly though we're just doing communication down here with
            # public and private messaging methods eventually.
            # RandoBot has no reason to talk, but ChatGPT could choose to
            # talk here if it wants.
            await self._maybe_update_last_will()

    async def run(self) -> None:
        try:
            await self.connect()
            await self.establish_identity()
            await self.subscribe_messages()
            await self.inner()
        except Exception as exc:
            self.log.exception(exc)
        finally:
            await self.disconnect()
