"""
It's the Robot Mafia
"""
import asyncio
import random
import time
import typing as T

from grpc import aio
from grpc import RpcError

from donbot.action import BotAction
from donbot.auto_ctx import AutomationContext
from donbot.resolver import RandomResolver
from proto import command_pb2
from proto import connect_pb2
from proto import message_pb2
from proto import state_pb2

from proto import service_pb2_grpc

if T.TYPE_CHECKING:
    from grpc.aio import UnaryStreamCall

BIND = "localhost:50051"


class DonBot:
    """
    Base class

    You come to me on the day of my robot daughter's wedding

    OK so...
    Procedure:
    * start up
    * Connect to app server
    * do shit
    * Disconnect from app server
    """

    def __init__(self, bot_name: str = None) -> None:
        self._connected = False
        self._bot_name: str = bot_name
        self._bot_id: str = None

        # current state
        self._actor: state_pb2.Actor = None  # this is us
        self._game: state_pb2.Game = None  # this updates

        self._subscribe_task: asyncio.Task = None
        self._print_task: asyncio.Task = None
        self._message_queue: asyncio.Queue[message_pb2.Message] = asyncio.Queue()
        self.setup_resolvers()

        self._should_exit = False

    def setup_resolvers(self) -> None:
        self._random_resolver = RandomResolver()
        self._action_resolver = self._random_resolver
        self._resolvers = {ba: self._random_resolver for ba in BotAction}

    @property
    def name(self) -> str:
        if self._actor is None:
            return None
        return self._actor.player.name

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

                print("Successfully connected!")
            except RpcError as error:
                print(f"Error response: {repr(error)}")
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
                print(f"Error response: {repr(error)}")

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
                if not actor.is_alive:
                    print(f"Uh oh! We're dead!")
                    self._should_exit = True
                    return False

                return True
            except RpcError as error:
                print(f"Error response: {repr(error)}")

    def contextualize(self) -> T.Dict[BotAction, T.List[T.Any]]:
        # this gives us a list of possible bot actions
        autoctx = AutomationContext.create_from_game_proto(self._bot_name, self._game)
        bot_actions = autoctx.infer_actions()
        targets = autoctx.infer_targets(bot_actions)
        print(f"Possible Actions: {bot_actions}\nPossible Targets: {targets}\n")
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

    async def execute_action(self, action: BotAction, target: T.Any) -> None:
        # now that we have an action and a target, we can execute it
        if action is None:
            print("Null Action?")
            return

        if action == BotAction.NO_OP:
            print("No-Op action")
            return
        if action == BotAction.DAY_ACTION:
            print("Day Target")
            await self.target(target)
            return
        if action == BotAction.NIGHT_ACTION:
            print("Night Target")
            await self.target(target)
            return
        if action == BotAction.LYNCH_VOTE:
            print("Lynch Vote")
            await self.lynch_vote(target)
            return
        if action == BotAction.TRIAL_VOTE:
            print("Trial Vote")
            await self.trial_vote(target)
            return
        if action == BotAction.SKIP_VOTE:
            print("Skip Vote")
            await self.trial_vote(target)
            return
        if action == BotAction.SEND_PRIVATE_MESSAGE:
            print("Private Message (TODO)")
            return
        if action == BotAction.SEND_PUBLIC_MESSAGE:
            print("Public Message (TODO)")
            return
        print(f"Bot Action: {action.name} Unhandled")

    async def establish_identity(self) -> None:
        async with aio.insecure_channel(BIND) as channel:
            stub = service_pb2_grpc.GrpcBotApiStub(channel)
            try:
                response: state_pb2.GetActorResponse = await \
                    stub.GetActor(state_pb2.GetActorRequest(timestamp=time.time(), bot_id=self._bot_id))
                self._actor = response.actor
                print(f"My name is {self.name}. My role is {self.role.name}")
            except RpcError as error:
                print(f"Error response: {repr(error)}")

    async def subscribe_messages(self) -> None:
        self._subscribe_task = asyncio.create_task(self.subscribe_task())
        self._print_task = asyncio.create_task(self.print_message_task())

    async def subscribe_task(self) -> None:
        """
        Process messages as we get them. That just means putting them into our queue.

        Probably want to just run this in the background or something
        """
        async with aio.insecure_channel(BIND) as channel:
            stub = service_pb2_grpc.GrpcBotApiStub(channel)
            call: UnaryStreamCall = stub.SubscribeMessages(
                message_pb2.SubscribeMessagesRequest(
                    timestamp=time.time(),
                    bot_id=self._bot_id
                )
            )
            consecutive_fails = 0
            while True:
                try:
                    response: message_pb2.SubscribeMessagesResponse = await call.read()
                    for msg in response.messages:
                        self._message_queue.put_nowait(msg)
                    consecutive_fails = 0
                except RpcError as error:
                    print(f"Error in subscribe messages: {repr(error)}")
                    consecutive_fails += 1
                    if consecutive_fails > 3:
                        # TODO: look for a way to see if RPC was cancelled from server
                        break
                except asyncio.CancelledError:
                    print(f"Let's bounce")
                    break

    async def print_message_task(self) -> None:
        """
        Wraps the message printer as async and runs it in the background
        """
        while True:
            try:
                msg = await self._message_queue.get()
                print(f"[{self.name} | {self.role.name}] {msg.message}")
            except asyncio.CancelledError:
                break

    def print_all_messages(self) -> None:
        """
        Clear the message queue and print all messages.
        """
        while not self._message_queue.empty():
            msg = self._message_queue.get_nowait()
            print(f"[{self.name} | {self.role.name}] {msg.message}")

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
                print(f"Error in send: response: {repr(error)}")

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
                print(f"Error in trial vote: {repr(error)}")

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
                print(f"Error in lynch vote: {repr(error)}")

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
                print(f"Error in skip vote: {repr(error)}")

    async def target(self, target_name: str) -> None:
        async with aio.insecure_channel(BIND) as channel:
            stub = service_pb2_grpc.GrpcBotApiStub(channel)
            try:
                await stub.DayTarget(command_pb2.TargetRequest(
                    timestamp=time.time(),
                    bot_id=self._bot_id,
                    target_name=target_name
                ))
            except RpcError as error:
                print(f"Error in target: {repr(error)}")

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
            t_init = time.time()

            if await self.get_game_state():
                action_target = self.contextualize()
                if action_target:
                    await self.execute_action(*self.plan_action(action_target))
            t_final = time.time()
            sleep_dur = random.random() * 10.0
            print(f"Loop Duration: {t_final - t_init}. Sleeping for {sleep_dur}s")
            await asyncio.sleep(sleep_dur)

    async def run(self) -> None:
        try:
            await self.connect()
            await self.establish_identity()
            await self.subscribe_messages()
            await self.inner()
        finally:
            await self.disconnect()
