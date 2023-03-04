import asyncio
import time
import typing as T

from chatapi.discord.driver import BotMessageDriver
from chatapi.discord.webhook import don_bot_message
from engine.message import Message
from proto import service_pb2_grpc
from proto import connect_pb2
from proto import message_pb2
from proto import state_pb2

if T.TYPE_CHECKING:
    from grpc import ServicerContext
    from chatapi.app.bot import BotUser
    from chatapi.app.bot_api import BotApi
    from engine.message import Messenger


class GrpcBotApi(service_pb2_grpc.GrpcBotApiServicer):

    _bot_api: T.Optional["BotApi"] = None
    _subscribed: T.Set["BotUser"] = set()

    @property
    def driver(self) -> "BotMessageDriver":
        driver: BotMessageDriver = self._bot_api.game.messenger.get_driver_by_class(BotMessageDriver)
        if driver is None:
            raise ValueError("Game does not have a bot driver setup yet.")
        return driver

    def set_bot_api(self, api: "BotApi") -> None:
        self._bot_api = api

    def get_bot(self, bot_id: str) -> "BotUser":
        if self._bot_api is None:
            raise ValueError("Bot API has not been set. This endpoint is not yet configured.")

        bot = self._bot_api.get_bot_by_id(bot_id)
        if bot is None:
            raise ValueError(f"Cannot find bot with ID {bot_id}")

        return bot

    def Connect(self, request: connect_pb2.ConnectRequest, context):
        """
        Handle a bot service requesting a game bot.
        """
        if self._bot_api is None:
            raise ValueError("Bot API has not been set. This endpoint is not yet configured.")
        
        requested_name = request.request_name
        bot = self._bot_api.check_out_bot(bot_name=requested_name)
        if bot is None and requested_name:
            raise ValueError(f"Could not reserve bot with name {requested_name}")
        if bot is None:
            raise ValueError(f"Could not reserve a bot. We appear to be out.")

        # give the basic information about the bot
        print(f"Vending {bot.name}")
        response = connect_pb2.ConnectResponse()
        response.timestamp = time.time()
        response.bot_name = bot.name
        response.bot_id = bot.id
        return response

    def Disconnect(self, request: connect_pb2.DisconnectRequest, context):
        """
        Handle a bot service disconnecting from a game bot.
        """
        bot = self.get_bot(request.bot_id)
        self._bot_api.check_in_bot(bot.name)
        print(f"Disconnected. {self._bot_api.reserved_bots or 'No'} bots being held.\n"
              f"{[bot.name for bot in self._bot_api.free_bots]} are free.")

        response = connect_pb2.DisconnectResponse()
        response.timestamp = time.time()
        response.success = True
        return response

    def GetGame(self, request: state_pb2.GetGameRequest, ctx):
        bot = self.get_bot(request.bot_id)

        return state_pb2.GetGameResponse(
            game=self._bot_api.game.to_proto(),
            timestamp=time.time()
        )

    def GetActor(self, request: state_pb2.GetActorRequest, ctx):
        if self._bot_api is None:
            raise ValueError("Bot API has not been set. This endpoint is not yet configured.")

        actor = None
        if request.bot_id:
            bot = self._bot_api.get_bot_by_id(request.bot_id)
            actor = self._bot_api.game.get_actor_by_name(bot.name)
        elif request.player_name:
            actor = self._bot_api.game.get_actor_by_name(request.player_name)

        if actor is None:
            raise ValueError(f"Could not find bot with provided identifier")

        return state_pb2.GetActorResponse(
            actor=actor.to_proto(),
            timestamp=time.time(),
        )

    async def SubscribeMessages(self, request: message_pb2.SubscribeMessagesRequest, context: "ServicerContext"):
        """
        What does this actually do lol

        I guess we could just make it yield fake messages as a test
        """
        bot = self.get_bot(request.bot_id)

        # TODO: add exit criteria
        self._subscribed.add(bot)
        while bot in self._subscribed:
            # ordering between public / private doesn't matter
            # get all the messages we can
            msgs = []
            while not self.driver._private_grpc_queues[bot].empty():
                msgs.append(self.driver._private_grpc_queues[bot].get_nowait())
            response = message_pb2.SubscribeMessagesResponse(timestamp=time.time(), messages=msgs)
            yield response
        print("Ok this actually worked? Wait do we even need this lol I thought it dies just fine")

    def SendMessage(self, request: message_pb2.SendMessageRequest, context) -> message_pb2.SendMessageResponse:
        # this is where the fun begins?
        bot = self.get_bot(request.bot_id)
        self._bot_api.public_message(bot.id, request.message.message)
        return message_pb2.SendMessageResponse(timestamp=time.time(), success=True)
