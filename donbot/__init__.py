"""
It's the Robot Mafia
"""
import asyncio
import time
import typing as T

from grpc import aio
from grpc import RpcError

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
        self._message_queue: asyncio.Queue[message_pb2.Message] = asyncio.Queue()

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
            except RpcError as error:
                print(f"Error response: {repr(error)}")

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
        """
        blah
        """
        self._subscribe_task = asyncio.create_task(self.subscribe_task())

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
            while True:
                try:
                    response: message_pb2.SubscribeMessagesResponse = await call.read()
                    for msg in response.messages:
                        self._message_queue.put_nowait(msg)
                except RpcError as error:
                    print(f"Error in subscribe messages: {repr(error)}")
                    # TODO: does it make sense to retry here??? reconnect and retry?
                except asyncio.CancelledError:
                    print(f"Let's bounce")
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
        print(f'sending public message: {message}')
        async with aio.insecure_channel(BIND) as channel:
            stub = service_pb2_grpc.GrpcBotApiStub(channel)
            try:
                to_send = message_pb2.Message(timestamp=time.time(), source=message_pb2.Message.PUBLIC, message=message)
                response: message_pb2.SendMessageResponse = await \
                    stub.SendMessage(message_pb2.SendMessageRequest(timestamp=time.time(), bot_id=self._bot_id, message=to_send))
                print(response.success)
            except RpcError as error:
                print(f"Error in send: response: {repr(error)}")

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
        print("Doing the inner execution loop I guess")
        t_init = time.time()
        while time.time() - t_init < 60:
            await self.get_game_state()
            self.print_all_messages()
            await self.send_public_message(f"Hello there my name is {self.name}")
            # something here to evaluate
            # print all messages lol
            await asyncio.sleep(3.)

    async def run(self) -> None:
        try:
            await self.connect()
            await self.establish_identity()
            await self.subscribe_messages()
            await self.inner()
        finally:
            await self.disconnect()
